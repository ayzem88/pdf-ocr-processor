from __future__ import annotations
from pathlib import Path
import importlib.util
import time
import calendar
import sys
import traceback
import os
import shutil
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import subprocess
from concurrent.futures import ThreadPoolExecutor
import re
from dataclasses import dataclass
from typing import Tuple, Optional, List, Iterable
from PIL import Image, ImageOps

# تأكيد PATH للأدوات المثبّتة عبر Homebrew
# هذا يضمن أن يتم العثور على الأدوات حتى لو لم تكن في PATH الافتراضي
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

def _find_executable(candidates_names: list[str]) -> Optional[str]:
    """يحاول إيجاد المسار التنفيذي للأداة عبر which ثم مواقع شائعة.
    يعيد None إذا لم يُعثر عليها بدل رفع استثناء كي لا يتعطل السكربت عند الاستيراد.
    """
    # 1) جرّب which للأسماء المعطاة
    for name in candidates_names:
        p = shutil.which(name)
        if p:
            return p
    # 2) جرّب مسارات شائعة يدويًا
    common_bins = [
        "/opt/homebrew/bin",   # Apple Silicon Homebrew
        "/usr/local/bin",      # Intel Homebrew
        "/usr/bin",
        "/bin",
    ]
    for base in common_bins:
        for name in candidates_names:
            cand = os.path.join(base, name)
            if os.path.exists(cand):
                return cand
    # 3) لم يتم العثور
    return None

# تحديد مسارات الأدوات (تلقائيًا أينما نُقل السكربت)
MAGICK: Optional[str] = _find_executable(["magick"])  # ImageMagick
TESS: Optional[str] = _find_executable(["tesseract"]) # Tesseract OCR
PDFTOPPM: Optional[str] = _find_executable(["pdftoppm"]) # Poppler

# إعدادات مجمّعة يسهل تعديلها في مكان واحد
CONFIG = {
    'DENSITY': 400,       # dpi
    'MAX_WORKERS': 4,     # عدد خيوط OCR
    'PSM': 6,             # 6 = صفحة نص متجانس
    'LANG_PDF': 'ara+eng',# لغات OCR لملف PDF
    'LANG_TXT': 'ara+eng',# لغات OCR لملف TXT
    'KEEP_IMAGES': False, # الاحتفاظ بالصور المؤقتة
    'MERGE_BATCH': 200,   # دمج PDF على دفعات
}

def load_module(module_path: Path, module_name: str):
    """تحميل وحدة بايثون ديناميكيًا من مسار ملف."""
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"تعذر تحميل الوحدة: {module_path.name}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

def list_pdfs(directory: Path) -> List[Path]:
    """يسرد جميع ملفات PDF في المجلد المحدد."""
    try:
        return [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
    except PermissionError:
        print(
            "لا صلاحيات للوصول إلى هذا المجلد. على macOS، امنح تطبيق Terminal صلاحية الوصول للمجلدات (Files and Folders) أو فعّل Full Disk Access من إعدادات الخصوصية."
        )
        return []

def find_script(base_dir: Path, candidates: list[str]) -> Path | None:
    """يبحث عن سكربت معين في المجلد الأساسي."""
    for name in candidates:
        p = base_dir / name
        if p.exists():
            return p
    return None

def extract_page_number(txt_file_path: str, file_base: str) -> int:
    """يستخرج رقم الصفحة من اسم ملف نصي."""
    base_name = os.path.basename(txt_file_path)
    name_part = os.path.splitext(base_name)[0]
    try:
        page_num_str = name_part.replace(file_base + '-', '')
        return int(page_num_str)
    except ValueError:
        return 0

def process_image_for_ocr(image_file: Path, file_base: str):
    """يقوم بمعالجة صورة واحدة باستخدام Tesseract لإنشاء PDF ونص."""
    try:
        if not TESS:
            print("Tesseract غير متوفر في النظام. تخطّي OCR لهذه الصورة.")
            return
        tesseract_pdf_command = [TESS, str(image_file), str(image_file.with_suffix('')), '-l', CONFIG['LANG_PDF'], '--oem', '1', '--psm', str(CONFIG['PSM']), 'pdf']
        tesseract_txt_command = [TESS, str(image_file), str(image_file.with_suffix('')), '-l', CONFIG['LANG_TXT'], '--oem', '1', '--psm', str(CONFIG['PSM']), 'txt']
        
        subprocess.run(tesseract_pdf_command, check=True, capture_output=True, text=True)
        subprocess.run(tesseract_txt_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"حدث خطأ في Tesseract أثناء معالجة الصورة {image_file.name}: {e.stderr}")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصورة {image_file.name}: {e}")

def remove_empty_lines(file_path: Path):
    """يزيل الأسطر الفارغة من ملف نصي."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        non_empty_lines = [line for line in lines if line.strip()]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(non_empty_lines)
    except Exception as e:
        print(f"فشل إزالة الأسطر الفارغة من {file_path.name}: {e}")

def merge_pdfs_in_batches(paths: List[Path], out_path: Path, batch_size: int = CONFIG['MERGE_BATCH']):
    """يدمج قائمة من ملفات PDF في دفعة واحدة للحفاظ على الذاكرة."""
    temp_chunks = []
    try:
        for i in range(0, len(paths), batch_size):
            chunk = paths[i:i+batch_size]
            tmp = out_path.parent / f"._chunk_{i//batch_size:03d}.pdf"
            with PdfMerger() as m:
                for p in chunk:
                    m.append(str(p))
                with tmp.open("wb") as f:
                    m.write(f)
            temp_chunks.append(tmp)

        with PdfMerger() as final_m:
            for c in temp_chunks:
                final_m.append(str(c))
            with out_path.open("wb") as f:
                final_m.write(f)
    except Exception as e:
        print(f"حدث خطأ أثناء دمج ملفات PDF على دفعات: {e}")
    finally:
        for c in temp_chunks:
            try:
                c.unlink()
            except OSError as e:
                print(f"فشل حذف الملف المؤقت {c.name}: {e}")

def process_pdf(pdf_file: Path, epoch_time: int):
    """يقوم بتحويل ملف PDF مصور إلى نص وPDF قابل للبحث."""
    try:
        file_name = pdf_file.stem
        folder_path = pdf_file.parent / f"{epoch_time}_{file_name}_temp"
        os.makedirs(folder_path, exist_ok=True)

        print(f"تحويل {pdf_file.name} إلى صور...")
        # التحويل إلى صور: فضّل ImageMagick، ثم pdftoppm كبديل
        converted = False
        if MAGICK:
            magick_cmd = [MAGICK, 'convert', '-density', str(CONFIG['DENSITY']), '-colorspace', 'Gray', '-contrast-stretch', '0', '-alpha', 'remove', '-strip', str(pdf_file), str(folder_path / f"{file_name}-%04d.png")]
            try:
                subprocess.run(magick_cmd, check=True, capture_output=True, text=True)
                converted = True
            except subprocess.CalledProcessError as e:
                print(f"ImageMagick فشل: {e.stderr.strip()}. المحاولة باستخدام pdftoppm...")
        else:
            print("ImageMagick غير متوفر. المحاولة باستخدام pdftoppm...")

        if not converted:
            if PDFTOPPM:
                pdftoppm_cmd = [PDFTOPPM, '-r', str(CONFIG['DENSITY']), '-gray', '-png', str(pdf_file), str(folder_path / file_name)]
                subprocess.run(pdftoppm_cmd, check=True, capture_output=True, text=True)
                # إعادة تسمية الملفات الناتجة من pdftoppm لتتناسب مع النمط
                for p in sorted(folder_path.glob(f"{file_name}-*.png")):
                    m = re.search(r"-(\d+)\.png$", p.name)
                    if m:
                        nn = int(m.group(1))
                        p.rename(folder_path / f"{file_name}-{nn:04d}.png")
                converted = True
            else:
                raise RuntimeError("لا ImageMagick ولا pdftoppm متاحان. يرجى تثبيت أحدهما.")
        
        png_files = sorted([p for p in folder_path.iterdir() if p.suffix == '.png'])
        if not png_files:
            raise RuntimeError(f"لم يتم العثور على صور لتحويلها من {pdf_file.name}.")

        if not TESS:
            print("Tesseract غير متوفر. سيتم تخطّي OCR وإنشاء الصور فقط.")
        else:
            print(f"تشغيل OCR على {len(png_files)} صورة...")
            with ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS']) as executor:
                executor.map(lambda img_file: process_image_for_ocr(img_file, file_name), png_files)

        ocred_pdfs = sorted([p for p in folder_path.iterdir() if p.suffix == '.pdf'])
        searchable_pdf_path = pdf_file.parent / f"{file_name}-قابل_للبحث.pdf"
        if ocred_pdfs:
            print("دمج ملفات PDF التي تم التعرف عليها...")
            merge_pdfs_in_batches(ocred_pdfs, searchable_pdf_path)

        ocred_txts = sorted([p for p in folder_path.iterdir() if p.suffix == '.txt'], key=lambda x: extract_page_number(str(x), file_name))
        txt_output_path = pdf_file.parent / f"{file_name}.txt"
        
        if ocred_txts:
            print("دمج الملفات النصية التي تم التعرف عليها...")
            with open(txt_output_path, 'w', encoding='utf-8') as outfile:
                for txt_file in ocred_txts:
                    page_number = extract_page_number(str(txt_file), file_name)
                    separator = f"==============================={page_number}===============================\n"
                    outfile.write(separator)
                    with open(txt_file, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n")
            remove_empty_lines(txt_output_path)
        else:
            print(f"لم يتم العثور على ملفات نصية في {folder_path.name}.")

        if not CONFIG['KEEP_IMAGES']:
            print("تنظيف الملفات المؤقتة...")
            for p in folder_path.iterdir():
                try:
                    p.unlink()
                except OSError as e:
                    print(f"فشل حذف الملف المؤقت {p.name}: {e}")
            try:
                folder_path.rmdir()
            except OSError as e:
                print(f"فشل حذف المجلد المؤقت {folder_path.name}: {e}")

        print(f"تمت معالجة {pdf_file.name} بنجاح.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الملف {pdf_file.name}: {e}")

def run_ocr_to_text(directory: Path):
    """تحويل كل ملف مصور إلى ملف نصي (ينتج TXT فقط)."""
    epoch = int(calendar.timegm(time.gmtime()))
    pdfs = list_pdfs(directory)
    if not pdfs:
        print("لا توجد ملفات PDF في المجلد الحالي.")
        return
    for pdf in pdfs:
        print(f"بدء تحويل {pdf.name} إلى نص...")
        try:
            process_pdf(pdf, epoch)
            searchable_pdf = pdf.with_name(f"{pdf.stem}-قابل_للبحث.pdf")
            if searchable_pdf.exists():
                try:
                    searchable_pdf.unlink()
                except OSError as e:
                    print(f"فشل حذف PDF القابل للبحث المؤقت: {e}")
            print(f"حُوّل إلى نص: {pdf.name} -> {pdf.stem}.txt")
        except Exception as e:
            print(f"فشل التحويل إلى نص للملف {pdf.name}: {e}")

def run_ocr_to_searchable_pdf(directory: Path):
    """تحويل كل ملف مصور إلى كتاب قابل للبحث (ينتج PDF فقط)."""
    epoch = int(calendar.timegm(time.gmtime()))
    pdfs = list_pdfs(directory)
    if not pdfs:
        print("لا توجد ملفات PDF في المجلد الحالي.")
        return
    for pdf in pdfs:
        print(f"بدء تحويل {pdf.name} إلى PDF قابل للبحث...")
        try:
            process_pdf(pdf, epoch)
            txt_path = pdf.with_suffix(".txt")
            if txt_path.exists():
                try:
                    txt_path.unlink()
                except OSError as e:
                    print(f"فشل حذف الملف النصي المؤقت: {e}")
            print(f"حُوّل إلى كتاب قابل للبحث: {pdf.name} -> {pdf.stem}-قابل_للبحث.pdf")
        except Exception as e:
            print(f"فشل التحويل إلى كتاب قابل للبحث للملف {pdf.name}: {e}")

# ===================== أدوات مساعدة لـ PDFService =====================
ARABIC_DIGIT_MAP = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",  # عربي شرقي + فارسي
    "01234567890123456789"
)

def normalize_digits(s: str) -> str:
    """يحول الأرقام العربية والفارسية إلى أرقام لاتينية."""
    return s.translate(ARABIC_DIGIT_MAP)

def natural_key(s: str):
    """ينشئ مفتاحًا لفرز طبيعي (بشري) لسلاسل النصوص."""
    s = normalize_digits(s)
    parts = re.split(r'(\d+)', s.lower())
    key: List[object] = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p)
    return tuple(key)

def parse_pages(spec: str, total: int) -> List[int]:
    """يحلل مواصفات الصفحات (مثل '1,3,5-8') ويُرجع قائمة بفهارس الصفحات (0-based)."""
    spec = spec.strip()
    if not spec:
        raise ValueError("مواصفة الصفحات فارغة.")
    out: List[int] = []
    for part in (p.strip() for p in spec.split(",")):
        if not part:
            continue
        if "-" in part:
            try:
                a_str, b_str = part.split("-", 1)
                a, b = int(a_str), int(b_str)
            except ValueError:
                raise ValueError(f"صيغة نطاق صفحات غير صحيحة: '{part}'")
            if a > b: a, b = b, a
            for k in range(a, b + 1):
                i = k - 1
                if 0 <= i < total: out.append(i)
        else:
            try:
                k = int(part)
            except ValueError:
                raise ValueError(f"رقم صفحة غير صحيح: '{part}'")
            i = k - 1
            if 0 <= i < total: out.append(i)
    
    # إزالة التكرارات وفرز الصفحات
    seen = set()
    ordered = []
    for i in out:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    ordered.sort() # تأكد من أن الصفحات مرتبة

    if not ordered:
        raise ValueError("لا توجد صفحات صحيحة ضمن النطاق المحدد.")
    return ordered

# ===================== نماذج PDF =====================

@dataclass
class PDFSource:
    path: Path

    @classmethod
    def first_in_dir(cls, directory: Path = Path(".")) -> "PDFSource":
        """يعيد أول ملف PDF في المجلد، مرتبًا طبيعيًا."""
        files = sorted((p for p in directory.iterdir() if p.suffix.lower() == ".pdf"), key=lambda p: natural_key(p.name))
        if not files:
            raise FileNotFoundError("لا يوجد أي ملف PDF في المجلد.")
        return cls(files[0].resolve())

class PDFDocument:
    """يمثل وثيقة PDF مع إمكانيات التحميل الأساسية."""
    def __init__(self, source: PDFSource):
        self.source = source
        self.reader: Optional[PdfReader] = None
        self.total_pages: int = 0
        self.base_name: str = self.source.path.stem

    def load(self) -> None:
        """يقوم بتحميل ملف PDF ويجهز القارئ."""
        try:
            self.reader = PdfReader(str(self.source.path))
            if self.reader.is_encrypted:
                # محاولة فك التشفير بكلمة مرور فارغة أو افتراضية
                try:
                    self.reader.decrypt("") 
                except Exception as e:
                    raise PermissionError(f"الملف مشفّر ولا يمكن قراءته: {e}. قد تحتاج لكلمة مرور.")
            self.total_pages = len(self.reader.pages)
        except Exception as e:
            raise IOError(f"فشل تحميل ملف PDF {self.source.path.name}: {e}")

    def writer_from_indices(self, indices: Iterable[int]) -> PdfWriter:
        """ينشئ كاتب PDF مع صفحات محددة."""
        if self.reader is None:
            raise RuntimeError("يجب استدعاء load() أولاً لتحميل المستند.")
        w = PdfWriter()
        for i in indices:
            if 0 <= i < self.total_pages: # تأكد أن الفهرس صالح
                w.add_page(self.reader.pages[i])
        return w

    def split_halves(self) -> Tuple[PdfWriter, PdfWriter]:
        """يقسم المستند إلى نصفين ويعيد كُتاب PDF لكل نصف."""
        if self.reader is None:
            raise RuntimeError("يجب استدعاء load() أولاً لتحميل المستند.")
        mid = self.total_pages // 2
        return (
            self.writer_from_indices(range(0, mid)),
            self.writer_from_indices(range(mid, self.total_pages)),
        )

class PDFExporter:
    """يتعامل مع حفظ كُتاب PDF إلى ملفات."""
    def __init__(self, out_dir: Path = Path(".")):
        self.out_dir = out_dir

    def export_writer(self, writer: PdfWriter, out_path: Path, overwrite: bool = True) -> Path:
        """يحفظ كاتب PDF إلى مسار محدد."""
        path = out_path if overwrite else self._avoid_clobber(out_path)
        try:
            with open(path, "wb") as f:
                writer.write(f)
            return path
        except Exception as e:
            raise IOError(f"فشل حفظ ملف PDF إلى {path.name}: {e}")

    def export_halves(self, doc: PDFDocument, halves: Tuple[PdfWriter, PdfWriter],
                      suffixes: Tuple[str, str] = ("-النصف الأول", "-النصف الثاني"),
                      overwrite: bool = True) -> Tuple[Path, Path]:
        """يحفظ نصفي PDF إلى ملفين منفصلين."""
        out1 = self.out_dir / f"{doc.base_name}{suffixes[0]}.pdf"
        out2 = self.out_dir / f"{doc.base_name}{suffixes[1]}.pdf"
        return (self.export_writer(halves[0], out1, overwrite),
                self.export_writer(halves[1], out2, overwrite))

    @staticmethod
    def _avoid_clobber(path: Path) -> Path:
        """ينشئ اسم ملف فريد لتجنب الكتابة فوق ملف موجود."""
        if not path.exists(): return path
        i, stem, suf = 1, path.stem, path.suffix
        while True:
            c = path.with_name(f"{stem} ({i}){suf}")
            if not c.exists(): return c
            i += 1

# ===================== خدمة العمليات =====================

class PDFService:
    """يقدم خدمات لمعالجة ملفات PDF مثل استخراج الصفحات، التقسيم، الحذف، والدمج."""
    def __init__(self, directory: Path = Path(".")):
        self.directory = directory

    def _open_first(self) -> PDFDocument:
        """يفتح أول ملف PDF في المجلد ويُرجع كائن PDFDocument."""
        src = PDFSource.first_in_dir(self.directory)
        doc = PDFDocument(src)
        doc.load()
        return doc

    def split_halves(self) -> Tuple[Path, Path]:
        """يقسم أول ملف PDF في المجلد إلى نصفين."""
        doc = self._open_first()
        if doc.total_pages < 2:
            raise ValueError("الملف يحتوي على أقل من صفحتين ولا يمكن تقسيمه.")
        halves = doc.split_halves()
        return PDFExporter(self.directory).export_halves(doc, halves)

    def extract_pages(self, pages_spec: str) -> Path:
        """يستخرج صفحات محددة من أول ملف PDF في المجلد."""
        doc = self._open_first()
        idx = parse_pages(pages_spec, doc.total_pages)
        if not idx:
            raise ValueError("لا توجد صفحات صالحة للاستخراج من المواصفات المقدمة.")
        w = doc.writer_from_indices(idx)
        out = self.directory / f"{doc.base_name}-صفحات-{pages_spec.replace(' ','')}.pdf"
        return PDFExporter(self.directory).export_writer(w, out)

    def delete_pages(self, pages_spec: str) -> Path:
        """يحذف صفحات محددة من أول ملف PDF في المجلد."""
        doc = self._open_first()
        del_idx = set(parse_pages(pages_spec, doc.total_pages))
        keep = [i for i in range(doc.total_pages) if i not in del_idx]
        if not keep:
            raise ValueError("لا يمكن حذف كل الصفحات. سيصبح الملف الناتج فارغًا.")
        w = doc.writer_from_indices(keep)
        out = self.directory / f"{doc.base_name}-بعد_الحذف-{pages_spec.replace(' ','')}.pdf"
        return PDFExporter(self.directory).export_writer(w, out)

    def merge_all(self, out_name: str = "الكل-مدمج.pdf", overwrite: bool = True) -> Path:
        """يدمج جميع ملفات PDF في المجلد الحالي بترتيب طبيعي."""
        pdfs = [p for p in self.directory.iterdir() if p.suffix.lower() == ".pdf"]
        pdfs.sort(key=lambda p: natural_key(p.name))
        
        # استبعاد ملف الإخراج إن وُجد ضمن القائمة لتجنب دورة لا نهائية
        target_out_path = self.directory / out_name
        pdfs = [p for p in pdfs if p != target_out_path]

        if len(pdfs) < 2:
            raise ValueError("يلزم وجود ملفين PDF على الأقل للدمج في نفس المجلد.")
        
        merger = PdfMerger()
        try:
            for p in pdfs:
                try:
                    merger.append(str(p))
                except Exception as e:
                    print(f"تجاهل ملف PDF غير صالح {p.name} أثناء الدمج: {e}")
                    continue
            
            out_path = target_out_path
            if not overwrite:
                out_path = PDFExporter._avoid_clobber(out_path)
            
            with open(out_path, "wb") as f:
                merger.write(f)
            return out_path
        finally:
            merger.close()

# ===================== معالجة الصور =====================
def open_image_rgb_fixed(path: Path, bg: Tuple[int,int,int] | None=(255,255,255)) -> Image.Image:
    """يفتح صورة، يُطبق تدوير EXIF، ويضمن أنها بتنسيق RGB مع خلفية اختيارية."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img) # يصحح اتجاه الصورة بناءً على بيانات EXIF

    if img.mode in ("RGBA", "LA") and bg is not None:
        # إذا كانت الصورة شفافة، أدمجها مع خلفية (افتراضيًا بيضاء)
        base = Image.new("RGB", img.size, bg)
        base.paste(img, mask=img.split()[-1]) # استخدم قناة ألفا كقناع
        img = base
    elif img.mode != "RGB":
        img = img.convert("RGB") # تحويل أي وضع آخر إلى RGB
    return img

def convert_each_to_pdf(folder: Path):
    """يحول كل ملف صورة في المجلد إلى ملف PDF منفصل."""
    # مرشحات الملفات لتضمينها كصور
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    try:
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in image_extensions]
    except PermissionError:
        print("لا صلاحيات للوصول إلى هذا المجلد. امنح الصلاحيات اللازمة من إعدادات الخصوصية في macOS.")
        return
    files.sort(key=lambda p: natural_key(p.name))
    count = 0
    for f in files:
        try:
            img = open_image_rgb_fixed(f)
            out = folder / f"{f.stem}.pdf"
            img.save(out, "PDF", resolution=300) # حفظ بدقة 300dpi
            img.close()
            count += 1
        except Exception as e:
            print(f"فشل تحويل الصورة {f.name} إلى PDF: {e}")
            continue
    print(f"تم تحويل {count} صورة إلى ملفات PDF منفصلة في {folder.name}")

def merge_all_to_pdf(folder: Path, out_name: str = "الصور-مدمجة.pdf"):
    """يدمج جميع ملفات الصور في المجلد إلى ملف PDF واحد."""
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    try:
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in image_extensions]
    except PermissionError:
        print("لا صلاحيات للوصول إلى هذا المجلد. امنح الصلاحيات اللازمة من إعدادات الخصوصية في macOS.")
        return
    files.sort(key=lambda p: natural_key(p.name))
    images = []
    for f in files:
        try:
            img = open_image_rgb_fixed(f)
            images.append(img)
        except Exception as e:
            print(f"فشل تحميل الصورة {f.name} للدمج: {e}")
            continue
    
    if not images:
        print("لا توجد صور صالحة للدمج.")
        return
    
    out_path = folder / out_name
    try:
        # حفظ الصورة الأولى، ثم إضافة البقية
        images[0].save(out_path, save_all=True, append_images=images[1:], resolution=300)
        print(f"تم دمج {len(images)} صورة في ملف واحد: {out_path.name}")
    except Exception as e:
        print(f"فشل دمج الصور إلى PDF: {e}")
    finally:
        for im in images:
            im.close() # تأكد من إغلاق جميع كائنات الصور

# ===================== دوال تشغيل الخدمة =====================

def _convert_image_to_png_if_needed(image_path: Path) -> Path:
    """يحاول تحويل الصورة إلى PNG إذا كان امتدادها غير مدعوم على macOS بشكل افتراضي.
    يعيد مسار الملف النهائي (قد يكون نفسه إن لم تُجرى أي عملية).
    """
    try:
        suffix = image_path.suffix.lower()
        # اترك PNG/JPG/JPEG كما هي
        if suffix in (".png", ".jpg", ".jpeg"):
            return image_path
        # حاول التحويل لباقي الصيغ إلى PNG
        with Image.open(image_path) as im:
            out_path = image_path.with_suffix(".png")
            im.save(out_path, "PNG")
        try:
            image_path.unlink()
        except OSError:
            pass
        return out_path
    except Exception as e:
        print(f"تعذر التحويل إلى PNG: {image_path.name}: {e}")
        return image_path

def run_split_halves(directory: Path):
    """يقسم أول ملف PDF في المجلد إلى نصفين."""
    try:
        svc = PDFService(directory)
        p1, p2 = svc.split_halves()
        print(f"تم التقسيم بنجاح:\n- {p1.name}\n- {p2.name}")
    except Exception as e:
        print(f"فشل تقسيم الملف: {e}")

def run_extract_pages(directory: Path):
    """يستخرج صفحات محددة من أول ملف PDF في المجلد."""
    try:
        svc = PDFService(directory)
        spec = input("أدخل الصفحات بصيغة 1,3,5-8: ").strip()
        out = svc.extract_pages(spec)
        print(f"تم استخراج الصفحات إلى: {out.name}")
    except Exception as e:
        print(f"فشل استخراج الصفحات: {e}")

def run_delete_pages(directory: Path):
    """يحذف صفحات محددة من أول ملف PDF في المجلد."""
    try:
        svc = PDFService(directory)
        spec = input("أدخل الصفحات للحذف بصيغة 2,4,10-12: ").strip()
        out = svc.delete_pages(spec)
        print(f"تم الحذف وحفظ الناتج: {out.name}")
    except Exception as e:
        print(f"فشل حذف الصفحات: {e}")

def run_merge_all_pdfs(directory: Path):
    """يدمج جميع ملفات PDF في المجلد."""
    try:
        svc = PDFService(directory)
        out = svc.merge_all(out_name="الكل-مدمج.pdf", overwrite=True)
        print(f"تم دمج الملفات وحفظ الناتج: {out.name}")
    except ValueError as e:
        print(f"لا يمكن دمج الملفات: {e}")
    except Exception as e:
        print(f"حدث خطأ أثناء دمج ملفات PDF: {e}")

def run_convert_each_image_to_pdf(directory: Path):
    """يحول كل ملف صورة في المجلد إلى ملف PDF منفصل."""
    try:
        convert_each_to_pdf(directory)
    except Exception as e:
        print(f"حدث خطأ أثناء تحويل الصور إلى PDF: {e}")

def run_merge_all_images_to_pdf(directory: Path):
    """يدمج جميع ملفات الصور في المجلد إلى ملف PDF واحد."""
    try:
        out_name = "الصور-مدمجة.pdf"
        merge_all_to_pdf(directory, out_name=out_name)
    except Exception as e:
        print(f"حدث خطأ أثناء دمج الصور إلى PDF: {e}")

def run_unlock_all_pdfs(directory: Path):
    """يفك قفل جميع ملفات PDF المحمية بكلمة مرور فارغة في المجلد."""
    try:
        import pikepdf  # type: ignore
    except ModuleNotFoundError:
        print(
            "حزمة pikepdf غير مثبتة. ثبّت بالحزمة لنفس مفسر بايثون الذي يشغّل هذا الملف:\n"
            "  python3 -m pip install --upgrade pip\n"
            "  python3 -m pip install pikepdf\n"
            "إن استمرّ الخطأ على macOS جرّب أيضًا: brew install qpdf"
        )
        return
    pdfs = list_pdfs(directory)
    if not pdfs:
        print("لا توجد ملفات PDF في المجلد الحالي.")
        return
    count = 0
    for pdf_path in pdfs:
        try:
            with pikepdf.open(str(pdf_path)) as pdf:
                out = pdf_path.with_name(f"معدل_{pdf_path.name}")
                pdf.save(str(out))
                count += 1
                print(f"فُكّ قفل: {pdf_path.name} -> {out.name}")
        except Exception as e:
            print(f"تعذر فتح/حفظ {pdf_path.name}: {e}")
    print(f"اكتملت العملية. عدد الملفات المعدّلة: {count}")

def run_extract_images_from_first_pdf(directory: Path):
    try:
        src = PDFSource.first_in_dir(directory)
    except Exception as e:
        print(f"تعذر إيجاد ملف PDF: {e}")
        return
    pdf_path = src.path
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"تعذر فتح الملف: {pdf_path.name}: {e}")
        return
    
    out_dir = directory / f"ال{pdf_path.stem} مفرق في صور"
    out_dir.mkdir(exist_ok=True)
    extracted = 0
    
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            # PyPDF2 3.0.0+ يستخدم .images بدلًا من الوصول المباشر لـ /XObject
            if hasattr(page, 'images'):
                for img_index, img_obj in enumerate(page.images, start=1):
                    try:
                        # PyPDF2 3.0.0+ يوفر البيانات مباشرة
                        image_data = img_obj.data
                        # PyPDF2 3.0.0+ يكتشف النوع تلقائيًا
                        ext = img_obj.name.split('.')[-1] if '.' in img_obj.name else 'bin'
                        # أحيانًا يكون .name لا يمثل الامتداد بشكل مباشر، يمكننا تخمين أفضل
                        if 'jpeg' in img_obj.name.lower() or 'jpg' in img_obj.name.lower():
                            ext = 'jpg'
                        elif 'png' in img_obj.name.lower():
                            ext = 'png'
                        elif 'tiff' in img_obj.name.lower():
                            ext = 'tiff'
                        elif 'jp2' in img_obj.name.lower():
                            ext = 'jp2'
                            
                        out_file = out_dir / f"page{page_index:04d}_{img_index:04d}.{ext}"
                        with open(out_file, "wb") as f:
                            f.write(image_data)
                        # تحويل لصيغة PNG إن كانت غير مدعومة بسهولة على macOS
                        out_file = _convert_image_to_png_if_needed(out_file)
                        extracted += 1
                    except Exception as e:
                        print(f"تعذر حفظ الصورة {img_index} من الصفحة {page_index}: {e}")
            else: # التوافق مع الإصدارات الأقدم من PyPDF2 (قبل 3.0.0)
                resources = page.get("/Resources")
                if resources is None:
                    continue
                xobjects = resources.get("/XObject")
                if xobjects is None:
                    continue
                xobjects = xobjects.get_object()
                
                for name in xobjects:
                    xobj = xobjects[name]
                    if xobj.get("/Subtype") == "/Image":
                        try:
                            # في بعض الحالات يلزم القراءة المباشرة من stream
                            data = xobj._data if hasattr(xobj, "_data") else None
                            if data is None: # محاولة أخرى للحصول على البيانات
                                data = xobj.get_data()
                        except Exception:
                            data = None # إذا فشلت كل المحاولات

                        if not data:
                            continue
                        
                        filt = xobj.get("/Filter")
                        ext = "bin"
                        if filt == "/DCTDecode":
                            ext = "jpg"
                        elif filt == "/JPXDecode":
                            ext = "jp2"
                        elif filt == "/FlateDecode":
                            ext = "png"
                        elif filt == "/CCITTFaxDecode":
                            ext = "tiff"
                        
                        out_file = out_dir / f"page{page_index:04d}_{extracted+1:04d}.{ext}"
                        try:
                            with open(out_file, "wb") as f:
                                f.write(data)
                            # تحويل لصيغة PNG إن كانت غير مدعومة بسهولة على macOS
                            out_file = _convert_image_to_png_if_needed(out_file)
                            extracted += 1
                        except Exception as e:
                            print(f"تعذر حفظ الصورة من الصفحة {page_index}: {e}")
        except Exception as e:
            print(f"تعذر استخراج صور من الصفحة {page_index}: {e}")
            
    if extracted:
        print(f"تم استخراج {extracted} صورة إلى المجلد: {out_dir.name}")
    else:
        print("لم يتم العثور على صور مضمّنة في الملف الأول.")


def main():
    """الدالة الرئيسية لتشغيل القائمة التفاعلية لخدمات PDF."""
    # السماح بتحديد المجلد الهدف عبر وسيطة سطر الأوامر
    # مثال: python3 معالج\ الكتب\ المصورة.py "/Users/اسمك/Documents/كتبي"
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser()
        if candidate.exists() and candidate.is_dir():
            base_dir = candidate.resolve()
        else:
            print("المسار المحدد غير صالح. سيتم استخدام مجلد السكربت.")
            base_dir = Path(__file__).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent

    print(f"سيتم العمل داخل: {base_dir}")

    MENU = (
        "\nاختر رقم الخدمة:\n"
        "1) فتح قفل كل الملفات المصورة\n"
        "2) دمج كل الملفات المصورة في المجلد\n"
        "3) تقسيم أول ملف مصور إلى نصفين\n"
        "4) استخراج صفحات من أول ملف مصور\n"
        "5) حذف صفحات من أول ملف مصور\n"
        "6) استخراج الصور من أول ملف مصور\n"
        "7) تحويل كل ملف مصور إلى ملف نصي\n"
        "8) تحويل كل ملف مصور إلى كتاب قابل للبحث\n"
        "9) تحويل كل صورة إلى ملف مصور منفصل\n"
        "10) دمج كل الصور في ملف مصور واحد\n"
        "11) إنهاء البرنامج\n"
        "إدخال: "
    )

    while True:
        try:
            choice = input(MENU).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nتم الإنهاء.")
            break

        try:
            if choice == "1":
                run_unlock_all_pdfs(base_dir)
            elif choice == "2":
                run_merge_all_pdfs(base_dir)
            elif choice == "3":
                run_split_halves(base_dir)
            elif choice == "4":
                run_extract_pages(base_dir)
            elif choice == "5":
                run_delete_pages(base_dir)
            elif choice == "6":
                run_extract_images_from_first_pdf(base_dir)
            elif choice == "7":
                run_ocr_to_text(base_dir)
            elif choice == "8":
                run_ocr_to_searchable_pdf(base_dir)
            elif choice == "9":
                run_convert_each_image_to_pdf(base_dir)
            elif choice == "10":
                run_merge_all_images_to_pdf(base_dir)
            elif choice == "11":
                print("تم الإنهاء.")
                break
            else:
                print("خيار غير صحيح.")
        except Exception:
            print("حدث خطأ أثناء التنفيذ:")
            traceback.print_exc()

if __name__ == "__main__":
    main()

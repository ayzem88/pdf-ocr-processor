from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, List, Iterable
import re
import PyPDF2
from PyPDF2 import PdfMerger

# ===================== أدوات مساعدة =====================

ARABIC_DIGIT_MAP = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",  # عربي شرقي + فارسي
    "00112233445566778899"
)

def normalize_digits(s: str) -> str:
    return s.translate(ARABIC_DIGIT_MAP)

def natural_key(s: str):
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
    spec = spec.strip()
    if not spec:
        raise ValueError("مواصفة الصفحات فارغة.")
    out: List[int] = []
    for part in (p.strip() for p in spec.split(",")):
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a > b: a, b = b, a
            for k in range(a, b + 1):
                i = k - 1
                if 0 <= i < total: out.append(i)
        else:
            k = int(part)
            i = k - 1
            if 0 <= i < total: out.append(i)
    seen, ordered = set(), []
    for i in out:
        if i not in seen:
            seen.add(i); ordered.append(i)
    if not ordered:
        raise ValueError("لا توجد صفحات صحيحة ضمن النطاق.")
    return ordered

# ===================== نماذج PDF =====================

@dataclass
class PDFSource:
    path: Path

    @classmethod
    def first_in_dir(cls, directory: Path = Path(".")) -> "PDFSource":
        files = sorted((p for p in directory.iterdir() if p.suffix.lower() == ".pdf"), key=lambda p: natural_key(p.name))
        if not files:
            raise FileNotFoundError("لا يوجد أي ملف PDF في المجلد.")
        return cls(files[0].resolve())

class PDFDocument:
    def __init__(self, source: PDFSource):
        self.source = source
        self.reader: Optional[PyPDF2.PdfReader] = None
        self.total_pages: int = 0
        self.base_name: str = self.source.path.stem

    def load(self) -> None:
        self.reader = PyPDF2.PdfReader(str(self.source.path))
        if getattr(self.reader, "is_encrypted", False):
            try:
                self.reader.decrypt("")
            except Exception as e:
                raise PermissionError(f"الملف مشفّر ولا يمكن قراءته: {e}")
        self.total_pages = len(self.reader.pages)

    def writer_from_indices(self, indices: Iterable[int]) -> PyPDF2.PdfWriter:
        if self.reader is None:
            raise RuntimeError("استدعِ load() أولاً.")
        w = PyPDF2.PdfWriter()
        for i in indices:
            w.add_page(self.reader.pages[i])
        return w

    def split_halves(self) -> Tuple[PyPDF2.PdfWriter, PyPDF2.PdfWriter]:
        mid = self.total_pages // 2
        return (
            self.writer_from_indices(range(0, mid)),
            self.writer_from_indices(range(mid, self.total_pages)),
        )

class PDFExporter:
    def __init__(self, out_dir: Path = Path(".")):
        self.out_dir = out_dir

    def export_writer(self, writer: PyPDF2.PdfWriter, out_path: Path, overwrite: bool = True) -> Path:
        path = out_path if overwrite else self._avoid_clobber(out_path)
        with open(path, "wb") as f: writer.write(f)
        return path

    def export_halves(self, doc: PDFDocument, halves: Tuple[PyPDF2.PdfWriter, PyPDF2.PdfWriter],
                      suffixes: Tuple[str, str] = ("-النصف الأول", "-النصف الثاني"),
                      overwrite: bool = True) -> Tuple[Path, Path]:
        out1 = self.out_dir / f"{doc.base_name}{suffixes[0]}.pdf"
        out2 = self.out_dir / f"{doc.base_name}{suffixes[1]}.pdf"
        return (self.export_writer(halves[0], out1, overwrite),
                self.export_writer(halves[1], out2, overwrite))

    @staticmethod
    def _avoid_clobber(path: Path) -> Path:
        if not path.exists(): return path
        i, stem, suf = 1, path.stem, path.suffix
        while True:
            c = path.with_name(f"{stem} ({i}){suf}")
            if not c.exists(): return c
            i += 1

# ===================== خدمة العمليات =====================

class PDFService:
    """استخراج صفحات، تقسيم نصفين، حذف صفحات، دمج ملفات المجلد."""
    def __init__(self, directory: Path = Path(".")):
        self.directory = directory

    def _open_first(self) -> PDFDocument:
        src = PDFSource.first_in_dir(self.directory)
        doc = PDFDocument(src); doc.load(); return doc

    # 1) تقسيم نصفين
    def split_halves(self) -> Tuple[Path, Path]:
        doc = self._open_first()
        halves = doc.split_halves()
        return PDFExporter(self.directory).export_halves(doc, halves)

    # 2) استخراج صفحات
    def extract_pages(self, pages_spec: str) -> Path:
        doc = self._open_first()
        idx = parse_pages(pages_spec, doc.total_pages)
        w = doc.writer_from_indices(idx)
        out = self.directory / f"{doc.base_name}-صفحات-{pages_spec.replace(' ','')}.pdf"
        return PDFExporter(self.directory).export_writer(w, out)

    # 3) حذف صفحات
    def delete_pages(self, pages_spec: str) -> Path:
        doc = self._open_first()
        del_idx = set(parse_pages(pages_spec, doc.total_pages))
        keep = [i for i in range(doc.total_pages) if i not in del_idx]
        if not keep: raise ValueError("لا يمكن حذف كل الصفحات.")
        w = doc.writer_from_indices(keep)
        out = self.directory / f"{doc.base_name}-بعد_الحذف-{pages_spec.replace(' ','')}.pdf"
        return PDFExporter(self.directory).export_writer(w, out)

    # 4) دمج جميع ملفات PDF في المجلد الحالي بترتيب طبيعي
    def merge_all(self, out_name: str = "الكل-مدمج.pdf", overwrite: bool = True) -> Path:
        pdfs = [p for p in self.directory.iterdir() if p.suffix.lower() == ".pdf"]
        pdfs.sort(key=lambda p: natural_key(p.name))
        # استبعاد ملف الإخراج إن وُجد ضمن القائمة
        pdfs = [p for p in pdfs if p.name != out_name]
        if len(pdfs) < 2:
            raise ValueError("يلزم وجود ملفين PDF على الأقل للدمج في نفس المجلد.")
        merger = PdfMerger()
        try:
            for p in pdfs:
                merger.append(str(p))
            out_path = self.directory / out_name
            if not overwrite:
                out_path = PDFExporter._avoid_clobber(out_path)
            with open(out_path, "wb") as f:
                merger.write(f)
            return out_path
        finally:
            merger.close()

# ===================== واجهة رقمية مبسطة =====================

MENU = (
    "اختر رقم العملية:\n"
    "1) تقسيم إلى نصفين\n"
    "2) استخراج صفحات محددة\n"
    "3) حذف صفحات محددة\n"
    "4) دمج جميع ملفات PDF في المجلد\n"
    "إدخال: "
)

if __name__ == "__main__":
    svc = PDFService()
    try:
        choice = input(MENU).strip()
        if choice == "1":
            p1, p2 = svc.split_halves()
            print(f"تم التقسيم:\n- {p1.name}\n- {p2.name}")
        elif choice == "2":
            spec = input("أدخل الصفحات بصيغة 1,3,5-8: ").strip()
            out = svc.extract_pages(spec)
            print(f"تم استخراج الصفحات إلى: {out.name}")
        elif choice == "3":
            spec = input("أدخل الصفحات للحذف بصيغة 2,4,10-12: ").strip()
            out = svc.delete_pages(spec)
            print(f"تم الحذف وحفظ الناتج: {out.name}")
        elif choice == "4":
            out = svc.merge_all(out_name="الكل-مدمج.pdf", overwrite=True)
            print(f"تم دمج الملفات وحفظ الناتج: {out.name}")
        else:
            print("خيار غير صحيح.")
    except Exception as e:
        print(f"فشل التنفيذ: {e}")

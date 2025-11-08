import os
import time
import calendar
from PyPDF2 import PdfMerger
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re

# تأكيد PATH للأدوات المثبّتة عبر Homebrew
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
MAGICK = "/opt/homebrew/bin/magick"
TESS = "/opt/homebrew/bin/tesseract"
PDFTOPPM = "/opt/homebrew/bin/pdftoppm"

# إعدادات مجمّعة يسهل تعديلها في مكان واحد
CONFIG = {
    'DENSITY': 250,       # dpi
    'MAX_WORKERS': 4,     # عدد خيوط OCR
    'PSM': 6,             # 6 = صفحة نص متجانس
    'LANG_PDF': 'ara+eng',# لغات OCR لملف PDF
    'LANG_TXT': 'ara+eng',# لغات OCR لملف TXT
    'KEEP_IMAGES': False, # الاحتفاظ بالصور المؤقتة
    'MERGE_BATCH': 200,   # دمج PDF على دفعات
}

# ========================= خيارات التحكم =========================
MAX_WORKERS = 4            # عدد الخيوط للـ OCR
KEEP_IMAGES = False        # True للاحتفاظ بالصور المؤقتة
MERGE_BATCH = 200          # حجم دفعة الدمج للـPDF
DENSITY = "400"            # دقة التحويل بالـdpi
PSM_MODE = "6"             # نمط تقسيم الصفحة (6 = نص متجانس)
LANGS_PDF = "ara+eng"      # لغات OCR لإنتاج PDF
LANGS_TXT = "ara+eng"      # لغات OCR لإنتاج النص

# ========================= أدوات مساعدة =========================
def extract_page_number(txt_file_path, file_base):
    base_name = os.path.basename(txt_file_path)
    name_part = os.path.splitext(base_name)[0]
    try:
        page_num_str = name_part.replace(file_base + '-', '')
        return int(page_num_str)
    except:
        return 0

def process_image(image_file):
    try:
        file_base = os.path.splitext(image_file)[0]
        tesseract_pdf_command = [TESS, image_file, file_base, '-l', LANGS_PDF, '--oem', '1', '--psm', PSM_MODE, 'pdf']
        tesseract_txt_command = [TESS, image_file, file_base, '-l', LANGS_TXT, '--oem', '1', '--psm', PSM_MODE, 'txt']
        subprocess.run(tesseract_pdf_command, check=True)
        subprocess.run(tesseract_txt_command, check=True)
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الصورة {image_file}: {e}")

def remove_empty_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        non_empty_lines = [line for line in lines if line.strip()]
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(non_empty_lines)
    except:
        pass

def merge_pdfs_in_batches(paths, out_path, batch_size=MERGE_BATCH):
    temp_chunks = []
    for i in range(0, len(paths), batch_size):
        chunk = paths[i:i+batch_size]
        tmp = out_path.parent / f"._chunk_{i//batch_size:03d}.pdf"
        with PdfMerger() as m:
            for p in chunk:
                m.append(p.as_posix())
            with tmp.open("wb") as f:
                m.write(f)
        temp_chunks.append(tmp)
    with PdfMerger() as final_m:
        for c in temp_chunks:
            final_m.append(c.as_posix())
        with out_path.open("wb") as f:
            final_m.write(f)
    for c in temp_chunks:
        try: c.unlink()
        except: pass

def process_pdf(pdf_file, epoch_time):
    try:
        file_name = pdf_file.stem
        folder_path = pdf_file.parent / f"{epoch_time}_{file_name}"
        os.makedirs(folder_path, exist_ok=True)

        magick_cmd = [MAGICK, 'convert', '-density', DENSITY, '-colorspace', 'Gray', '-contrast-stretch', '0', '-alpha', 'remove', '-strip', pdf_file.as_posix(), (folder_path / f"{file_name}-%04d.png").as_posix()]
        try:
            subprocess.run(magick_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print("ImageMagick فشل. تفاصيل الخطأ:\n" + (e.stderr or ""))
            cmd = [PDFTOPPM, '-r', DENSITY, '-gray', '-png', pdf_file.as_posix(), (folder_path / file_name).as_posix()]
            subprocess.run(cmd, check=True)
            for p in sorted(folder_path.glob(f"{file_name}-*.png")):
                m = re.search(r"-(\d+)\.png$", p.name)
                if m:
                    nn = int(m.group(1))
                    p.rename(folder_path / f"{file_name}-{nn:04d}.png")

        png_files = sorted([p for p in folder_path.iterdir() if p.suffix == '.png'])
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process_image, png_files)

        ocred_pdfs = sorted([p for p in folder_path.iterdir() if p.suffix == '.pdf'])
        searchable_pdf_path = pdf_file.parent / f"{file_name}-قابل_للبحث.pdf"
        if ocred_pdfs:
            merge_pdfs_in_batches(ocred_pdfs, searchable_pdf_path)

        ocred_txts = sorted([p for p in folder_path.iterdir() if p.suffix == '.txt'], key=lambda x: extract_page_number(x.as_posix(), file_name))
        txt_output_path = pdf_file.parent / f"{file_name}.txt"
        with open(txt_output_path, 'w', encoding='utf-8') as outfile:
            for txt_file in ocred_txts:
                page_number = extract_page_number(txt_file.as_posix(), file_name)
                separator = f"==============================={page_number}===============================\n"
                outfile.write(separator)
                with open(txt_file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n")
        remove_empty_lines(txt_output_path)

        if not KEEP_IMAGES:
            for p in folder_path.iterdir():
                try: p.unlink()
                except: pass
            try: folder_path.rmdir()
            except: pass

        print(f"تمت معالجة {pdf_file.name} بنجاح.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الملف {pdf_file.name}: {e}")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    pdf_files = [p for p in script_dir.iterdir() if p.is_file() and p.suffix.lower() == '.pdf']
    if not pdf_files:
        print("لا توجد ملفات PDF في المجلد الحالي.")
    current_epoch_time = int(calendar.timegm(time.gmtime()))
    for pdf in pdf_files:
        process_pdf(pdf, current_epoch_time)
    print('معالجة الملفات اكتملت')

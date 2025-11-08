from __future__ import annotations
from pathlib import Path
import re
from typing import List, Tuple
from PIL import Image, ImageOps

# ===================== أدوات فرز طبيعي =====================
ARABIC_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "00112233445566778899")

def normalize_digits(s: str) -> str:
    return s.translate(ARABIC_DIGIT_MAP)

def natural_key(s: str):
    parts = re.split(r'(\d+)', normalize_digits(s.lower()))
    return tuple(int(p) if p.isdigit() else p for p in parts)

# ===================== معالجة الصور =====================
def open_image_rgb_fixed(path: Path, bg: Tuple[int,int,int] | None=(255,255,255)) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") and bg is not None:
        base = Image.new("RGB", img.size, bg)
        base.paste(img, mask=img.split()[-1])
        img = base
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return img

# ===================== تنفيذ الخيارات =====================
def convert_each_to_pdf(folder: Path):
    files = [p for p in folder.iterdir() if p.is_file()]
    files.sort(key=lambda p: natural_key(p.name))
    count = 0
    for f in files:
        try:
            img = open_image_rgb_fixed(f)
        except Exception:
            continue
        out = folder / f"{f.stem}.pdf"
        img.save(out, "PDF")
        img.close()
        count += 1
    print(f"تم تحويل {count} صورة إلى ملفات PDF منفصلة في {folder}")

def merge_all_to_pdf(folder: Path, out_name="الصور-مدمجة.pdf"):
    files = [p for p in folder.iterdir() if p.is_file()]
    files.sort(key=lambda p: natural_key(p.name))
    images = []
    for f in files:
        try:
            img = open_image_rgb_fixed(f)
            images.append(img)
        except Exception:
            continue
    if not images:
        print("لا توجد صور صالحة للدمج.")
        return
    out_path = folder / out_name
    images[0].save(out_path, save_all=True, append_images=images[1:], resolution=300)
    for im in images: im.close()
    print(f"تم دمج {len(images)} صورة في ملف واحد: {out_path}")

# ===================== التشغيل =====================
if __name__ == "__main__":
    folder = Path(".").resolve()
    print("اختر العملية:")
    print("1) تحويل كل صورة إلى PDF منفصل")
    print("2) دمج جميع الصور في ملف واحد")
    choice = input("أدخل الرقم: ").strip()
    if choice == "1":
        convert_each_to_pdf(folder)
    elif choice == "2":
        merge_all_to_pdf(folder)
    else:
        print("خيار غير صحيح.")

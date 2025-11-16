# معالج الكتب المصورة

<div dir="rtl">

أداة متقدمة لمعالجة الكتب المصورة وتحويلها إلى نصوص قابلة للبحث باستخدام تقنية OCR (Optical Character Recognition).

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub](https://img.shields.io/github/stars/ayzem88/pdf-ocr-processor?style=social)

</div>

## المميزات

- **تحويل PDF إلى نص قابل للبحث**: تحويل الكتب المصورة إلى PDF قابل للبحث
- **استخراج النص**: استخراج النص من الصور باستخدام OCR
- **دعم متعدد اللغات**: دعم العربية والإنجليزية
- **معالجة متوازية**: معالجة متعددة الخيوط لتسريع العملية
- **دمج الملفات**: دمج ملفات PDF متعددة
- **تحسين الصور**: معالجة الصور قبل OCR لتحسين الدقة
- **قابل للتخصيص**: إعدادات قابلة للتعديل

## المتطلبات

### البرامج المطلوبة

- **Python 3.7+**
- **Tesseract OCR**: لاستخراج النص من الصور
- **ImageMagick**: لمعالجة الصور
- **Poppler**: لتحويل PDF إلى صور

### تثبيت البرامج على macOS

```bash
# تثبيت عبر Homebrew
brew install tesseract
brew install imagemagick
brew install poppler

# تثبيت حزم Python
pip install PyPDF2 Pillow
```

### تثبيت البرامج على Linux

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-ara imagemagick poppler-utils
sudo apt-get install python3-pip
pip3 install PyPDF2 Pillow

# Fedora
sudo dnf install tesseract tesseract-langpack-ara ImageMagick poppler-utils
pip3 install PyPDF2 Pillow
```

## التثبيت

1. استنسخ المستودع:
```bash
git clone https://github.com/ayzem88/pdf-ocr-processor.git
cd pdf-ocr-processor
```

2. ثبت المتطلبات:
```bash
pip install -r requirements.txt
```

## الاستخدام

### الاستخدام الأساسي

```bash
python "معالج الكتب المصورة.py"
```

### الوظائف المتاحة

1. **تحويل PDF إلى قابل للبحث**: تحويل ملف PDF مصور إلى PDF قابل للبحث
2. **جمع وتقسيم**: جمع أو تقسيم ملفات PDF
3. **تحويل وجمع الصور**: تحويل الصور إلى PDF قابل للبحث
4. **فتح قفل**: إزالة الحماية من ملفات PDF

## الإعدادات

يمكنك تعديل الإعدادات في الملف الرئيسي:

```python
CONFIG = {
    'DENSITY': 400,       # دقة الصور (dpi)
    'MAX_WORKERS': 4,     # عدد الخيوط للمعالجة المتوازية
    'PSM': 6,             # نمط تقسيم الصفحة
    'LANG_PDF': 'ara+eng',# لغات OCR لملف PDF
    'LANG_TXT': 'ara+eng',# لغات OCR لملف TXT
    'KEEP_IMAGES': False, # الاحتفاظ بالصور المؤقتة
    'MERGE_BATCH': 200,   # حجم دفعة الدمج
}
```

## هيكل المشروع

```
معالج الكتب المصورة/
├── معالج الكتب المصورة.py    # الملف الرئيسي
├── كشكول/                     # أدوات إضافية
│   ├── 01 تحويل إلى قابل للبحث.py
│   ├── 02 جمع وتقسيم.py
│   ├── 03 تحويل وجمع الصور إلى.py
│   └── 04 فتح قفل.py
├── stopwords.txt              # كلمات الإيقاف
├── requirements.txt           # المتطلبات
└── README.md                  # هذا الملف
```

## الملفات الرئيسية

- `معالج الكتب المصورة.py`: الملف الرئيسي للمعالج
- `كشكول/01 تحويل إلى قابل للبحث.py`: تحويل PDF إلى قابل للبحث
- `كشكول/02 جمع وتقسيم.py`: جمع وتقسيم ملفات PDF
- `كشكول/03 تحويل وجمع الصور إلى.py`: تحويل الصور إلى PDF
- `كشكول/04 فتح قفل.py`: إزالة الحماية من PDF

## المساهمة

نرحب بمساهماتكم! يمكنك المساهمة من خلال:

1. فتح [issue](https://github.com/ayzem88/pdf-ocr-processor/issues) للإبلاغ عن مشاكل أو اقتراح ميزات جديدة
2. إرسال [pull request](https://github.com/ayzem88/pdf-ocr-processor/pulls) لإضافة ميزات أو إصلاح أخطاء
3. تحسين دقة OCR
4. إضافة دعم للغات إضافية

## الترخيص

هذا المشروع مرخص تحت [MIT License](LICENSE) - راجع ملف LICENSE للتفاصيل.

## المطور

تم تطوير هذا المشروع بواسطة [ayzem88](https://github.com/ayzem88)

## التواصل

للاستفسارات أو المساهمة، يمكنك التواصل معي عبر:
- البريد الإلكتروني: [aymen.nji@gmail.com](mailto:aymen.nji@gmail.com)

## ملاحظات

- تأكد من تثبيت جميع البرامج المطلوبة قبل الاستخدام
- دقة OCR تعتمد على جودة الصور الأصلية
- المعالجة المتوازية تسرع العملية ولكنها تستهلك موارد أكثر
- يمكنك تعديل الإعدادات حسب احتياجاتك

## التطوير المستقبلي

- [ ] واجهة رسومية (GUI)
- [ ] دعم المزيد من اللغات
- [ ] تحسين خوارزميات معالجة الصور
- [ ] دعم المزيد من صيغ الملفات
- [ ] معالجة أسرع وأكثر كفاءة
- [ ] دعم Windows
- [ ] واجهة سطر الأوامر (CLI) محسّنة

## الاختبار

```bash
# تثبيت متطلبات التطوير
pip install -r requirements-dev.txt

# تشغيل الاختبارات
python -m pytest tests/

# تشغيل مع تغطية الكود
pytest tests/ --cov=. --cov-report=html
```

## CI/CD

يحتوي المشروع على ملف GitHub Actions workflow في `.github/workflows/ci.yml` للاختبارات التلقائية.

**ملاحظة**: إذا واجهت مشكلة في رفع ملف workflow، يمكنك إضافته يدوياً من واجهة GitHub:
1. اذهب إلى المستودع → Actions
2. اختر "New workflow"
3. انسخ محتوى `.github/workflows/ci.yml`

## المساهمة

نرحب بمساهماتكم! راجع [دليل المساهمة](CONTRIBUTING.md) للتفاصيل.

## سجل التغييرات

راجع [CHANGELOG.md](CHANGELOG.md) لمعرفة التغييرات في كل إصدار.


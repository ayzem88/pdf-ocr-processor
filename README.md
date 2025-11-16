# معالج الكتب المصورة / PDF OCR Processor

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

تم تطوير هذا المشروع بواسطة **أيمن الطيّب بن نجي** ([ayzem88](https://github.com/ayzem88))

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

---

# [English]

<div dir="ltr">

## PDF OCR Processor

An advanced tool for processing scanned books and converting them into searchable text using OCR (Optical Character Recognition) technology.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub](https://img.shields.io/github/stars/ayzem88/pdf-ocr-processor?style=social)

## Features

- **PDF to Searchable Text**: Convert scanned books to searchable PDF
- **Text Extraction**: Extract text from images using OCR
- **Multi-language Support**: Support for Arabic and English
- **Parallel Processing**: Multi-threaded processing for faster execution
- **File Merging**: Merge multiple PDF files
- **Image Enhancement**: Image processing before OCR to improve accuracy
- **Customizable**: Adjustable settings

## Requirements

### Required Software

- **Python 3.7+**
- **Tesseract OCR**: For text extraction from images
- **ImageMagick**: For image processing
- **Poppler**: For PDF to image conversion

### Installation on macOS

```bash
# Install via Homebrew
brew install tesseract
brew install imagemagick
brew install poppler

# Install Python packages
pip install PyPDF2 Pillow
```

### Installation on Linux

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-ara imagemagick poppler-utils
sudo apt-get install python3-pip
pip3 install PyPDF2 Pillow

# Fedora
sudo dnf install tesseract tesseract-langpack-ara ImageMagick poppler-utils
pip3 install PyPDF2 Pillow
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ayzem88/pdf-ocr-processor.git
cd pdf-ocr-processor
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python "معالج الكتب المصورة.py"
```

### Available Functions

1. **Convert PDF to Searchable**: Convert scanned PDF to searchable PDF
2. **Merge and Split**: Merge or split PDF files
3. **Convert and Merge Images**: Convert images to searchable PDF
4. **Unlock**: Remove protection from PDF files

## Configuration

You can modify settings in the main file:

```python
CONFIG = {
    'DENSITY': 400,       # Image resolution (dpi)
    'MAX_WORKERS': 4,     # Number of threads for parallel processing
    'PSM': 6,             # Page segmentation mode
    'LANG_PDF': 'ara+eng',# OCR languages for PDF
    'LANG_TXT': 'ara+eng',# OCR languages for TXT
    'KEEP_IMAGES': False, # Keep temporary images
    'MERGE_BATCH': 200,   # Merge batch size
}
```

## Project Structure

```
pdf-ocr-processor/
├── معالج الكتب المصورة.py    # Main file
├── كشكول/                     # Additional tools
│   ├── 01 تحويل إلى قابل للبحث.py
│   ├── 02 جمع وتقسيم.py
│   ├── 03 تحويل وجمع الصور إلى.py
│   └── 04 فتح قفل.py
├── stopwords.txt              # Stop words
├── requirements.txt           # Requirements
└── README.md                  # This file
```

## Main Files

- `معالج الكتب المصورة.py`: Main processor file
- `كشكول/01 تحويل إلى قابل للبحث.py`: Convert PDF to searchable
- `كشكول/02 جمع وتقسيم.py`: Merge and split PDFs
- `كشكول/03 تحويل وجمع الصور إلى.py`: Convert images to PDF
- `كشكول/04 فتح قفل.py`: Remove PDF protection

## Contributing

We welcome contributions! You can contribute by:

1. Opening an [issue](https://github.com/ayzem88/pdf-ocr-processor/issues) to report problems or suggest new features
2. Submitting a [pull request](https://github.com/ayzem88/pdf-ocr-processor/pulls) to add features or fix bugs
3. Improving OCR accuracy
4. Adding support for additional languages

## License

This project is licensed under [MIT License](LICENSE) - see the LICENSE file for details.

## Developer

Developed by **Ayman Al-Tayyib Ben Naji** ([ayzem88](https://github.com/ayzem88))

## Contact

For inquiries or contributions, you can contact me via:
- Email: [aymen.nji@gmail.com](mailto:aymen.nji@gmail.com)

## Notes

- Make sure to install all required software before use
- OCR accuracy depends on original image quality
- Parallel processing speeds up the process but consumes more resources
- You can adjust settings according to your needs

## Future Development

- [ ] Graphical user interface (GUI)
- [ ] Support for more languages
- [ ] Improved image processing algorithms
- [ ] Support for more file formats
- [ ] Faster and more efficient processing
- [ ] Windows support
- [ ] Enhanced command-line interface (CLI)

## Testing

```bash
# Install development requirements
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run with code coverage
pytest tests/ --cov=. --cov-report=html
```

## CI/CD

The project contains a GitHub Actions workflow file in `.github/workflows/ci.yml` for automated testing.

**Note**: If you encounter issues pushing the workflow file, you can add it manually from the GitHub interface:
1. Go to the repository → Actions
2. Select "New workflow"
3. Copy the contents of `.github/workflows/ci.yml`

## Contributing

We welcome contributions! See [Contributing Guide](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for changes in each version.

</div>


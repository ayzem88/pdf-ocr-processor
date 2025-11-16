"""
إعدادات pytest المشتركة
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def tmp_path():
    """إنشاء مجلد مؤقت للاختبارات"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pdf_path(tmp_path):
    """إنشاء ملف PDF وهمي للاختبار"""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.touch()
    return pdf_path


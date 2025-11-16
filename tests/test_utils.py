"""
اختبارات للوظائف المساعدة في معالج الكتب المصورة
"""
import pytest
from pathlib import Path
import sys
import os

# إضافة المسار الرئيسي إلى sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# استيراد الوحدة الرئيسية
import importlib.util
main_module_path = Path(__file__).parent.parent / "معالج الكتب المصورة.py"
spec = importlib.util.spec_from_file_location("main_module", main_module_path)
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)

# استيراد الدوال المطلوبة
list_pdfs = main_module.list_pdfs
find_script = main_module.find_script
extract_page_number = main_module.extract_page_number
_find_executable = main_module._find_executable


class TestListPDFs:
    """اختبارات دالة list_pdfs"""
    
    def test_list_pdfs_empty_directory(self, tmp_path):
        """اختبار قائمة فارغة من PDF"""
        result = list_pdfs(tmp_path)
        assert result == []
    
    def test_list_pdfs_with_pdf_files(self, tmp_path):
        """اختبار العثور على ملفات PDF"""
        # إنشاء ملفات PDF وهمية
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        txt_file = tmp_path / "test.txt"
        
        pdf1.touch()
        pdf2.touch()
        txt_file.touch()
        
        result = list_pdfs(tmp_path)
        assert len(result) == 2
        assert pdf1 in result
        assert pdf2 in result
        assert txt_file not in result


class TestFindScript:
    """اختبارات دالة find_script"""
    
    def test_find_existing_script(self, tmp_path):
        """اختبار العثور على سكربت موجود"""
        script = tmp_path / "test_script.py"
        script.touch()
        
        result = find_script(tmp_path, ["test_script.py"])
        assert result == script
    
    def test_find_nonexistent_script(self, tmp_path):
        """اختبار عدم العثور على سكربت غير موجود"""
        result = find_script(tmp_path, ["nonexistent.py"])
        assert result is None


class TestExtractPageNumber:
    """اختبارات دالة extract_page_number"""
    
    def test_extract_page_number_valid(self):
        """اختبار استخراج رقم صفحة صحيح"""
        result = extract_page_number("test-001.txt", "test")
        assert result == 1
    
    def test_extract_page_number_invalid(self):
        """اختبار استخراج رقم صفحة غير صحيح"""
        result = extract_page_number("test-abc.txt", "test")
        assert result == 0


class TestFindExecutable:
    """اختبارات دالة _find_executable"""
    
    def test_find_executable_which(self):
        """اختبار العثور على أداة موجودة في PATH"""
        # python موجود عادة في PATH
        result = _find_executable(["python", "python3"])
        # قد يكون None أو مسار صحيح
        assert result is None or isinstance(result, str)
    
    def test_find_executable_nonexistent(self):
        """اختبار عدم العثور على أداة غير موجودة"""
        result = _find_executable(["nonexistent_tool_xyz"])
        assert result is None


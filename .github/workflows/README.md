# GitHub Actions Workflows

<div dir="rtl">

هذا المجلد يحتوي على ملفات GitHub Actions للاختبارات التلقائية.

</div>

## إضافة Workflow

ملف `ci.yml` موجود هنا ولكن قد تحتاج إلى إضافته يدوياً إلى GitHub إذا كان لديك قيود على الصلاحيات.

### الطريقة اليدوية:

1. اذهب إلى المستودع على GitHub
2. اضغط على "Actions" في القائمة العلوية
3. اختر "New workflow"
4. انسخ محتوى `ci.yml` إلى الملف الجديد
5. احفظ الملف

### أو عبر Git:

```bash
git add .github/workflows/ci.yml
git commit -m "إضافة GitHub Actions workflow"
git push origin main
```

**ملاحظة**: قد تحتاج إلى تفعيل GitHub Actions في إعدادات المستودع أولاً.


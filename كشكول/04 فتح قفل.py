import os
import pikepdf

# المجلد الحالي (مكان تشغيل الملف)
current_directory = os.getcwd()

# المرور فقط على الملفات داخل المجلد الحالي
for file in os.listdir(current_directory):
    if file.endswith(".pdf"):
        filepath = os.path.join(current_directory, file)
        print(filepath)
        pdf = pikepdf.open(filepath)
        new_file = "معدل_" + file
        pdf.save(os.path.join(current_directory, new_file))

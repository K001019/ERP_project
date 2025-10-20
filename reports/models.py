#from django.db import models

# Create your models here.
from django.db import models

class Report(models.Model):
    class Meta:
        # هذا النموذج لن ينشئ جدولاً في قاعدة البيانات
        # ولكنه سيسمح لنا بإنشاء صلاحيات مخصصة له
        managed = False
        default_permissions = () # تعطيل صلاحيات الإضافة/التعديل/الحذف الافتراضية
        permissions = [
            ("view_report", "Can view financial and operational reports"),
        ]
        verbose_name = "التقرير"
        verbose_name_plural = "التقارير"
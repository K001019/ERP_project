#from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User # لاستيراد نظام المستخدمين الجاهز من Django

class Employee(models.Model):
    # ربط الموظف بحساب مستخدم للدخول إلى النظام
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="رقم الموظف")
    first_name = models.CharField(max_length=100, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=100, verbose_name="الاسم الأخير")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    hire_date = models.DateField(verbose_name="تاريخ التعيين")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الراتب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "الموظف"
        verbose_name_plural = "الموظفين"
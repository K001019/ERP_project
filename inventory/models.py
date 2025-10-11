#from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# نموذج الموردين
class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم المورد")
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="الشخص المسؤول")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "المورد"
        verbose_name_plural = "الموردين"

# نموذج المنتجات
class Product(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم المنتج")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU (رقم المنتج)")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الشراء")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر البيع")
    quantity_in_stock = models.PositiveIntegerField(default=0, verbose_name="الكمية في المخزون")
    unit_of_measure = models.CharField(max_length=50, verbose_name="وحدة القياس", help_text="مثال: قطعة، كجم، لتر")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المورد")
    reorder_level = models.PositiveIntegerField(default=10, verbose_name="حد إعادة الطلب")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "المنتج"
        verbose_name_plural = "المنتجات"

# نموذج حركة المخزون
class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'إدخال مخزون'),
        ('OUT', 'إخراج مخزون'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES, verbose_name="نوع الحركة")
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    movement_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الحركة")
    moved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المسؤول")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.quantity} من {self.product.name}"

    class Meta:
        verbose_name = "حركة مخزون"
        verbose_name_plural = "حركات المخزون"
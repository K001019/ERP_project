#from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from inventory.models import Product  # استيراد نموذج المنتج من تطبيق المخازن
from employees.models import Employee # استيراد نموذج الموظف (لربط المبيعات بالموظف)

# نموذج العملاء
class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم العميل")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "العميل"
        verbose_name_plural = "العملاء"

# نموذج أوامر المبيعات
class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'قيد الانتظار'),
        ('PROCESSING', 'قيد المعالجة'),
        ('SHIPPED', 'تم الشحن'),
        ('DELIVERED', 'تم التسليم'),
        ('CANCELLED', 'ملغى'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="العميل")
    order_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الطلب")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="حالة الطلب")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="المبلغ الإجمالي")
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تم إنشاؤه بواسطة")

    def __str__(self):
        return f"طلب رقم #{self.id} للعميل {self.customer.name}"

    class Meta:
        verbose_name = "أمر مبيع"
        verbose_name_plural = "أوامر المبيعات"

# نموذج بنود أمر المبيع
class OrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items', verbose_name="أمر المبيع")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المجموع الفرعي")

    # دالة لحساب المجموع الفرعي تلقائياً عند الحفظ
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    class Meta:
        verbose_name = "بند في الطلب"
        verbose_name_plural = "بنود الطلبات"
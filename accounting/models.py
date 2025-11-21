#from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Sum

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('ASSET', 'أصول'),
        ('LIABILITY', 'التزامات'),
        ('EQUITY', 'حقوق ملكية'),
        ('REVENUE', 'إيرادات'),
        ('EXPENSE', 'مصروفات'),
    ]

    name = models.CharField(max_length=200, verbose_name="اسم الحساب")
    account_number = models.CharField(max_length=20, unique=True, verbose_name="رقم الحساب")
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, verbose_name="نوع الحساب")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    def __str__(self):
        return f"{self.account_number} - {self.name}"

    class Meta:
        verbose_name = "حساب"
        verbose_name_plural = "شجرة الحسابات"


class JournalEntry(models.Model):
    date = models.DateField(verbose_name="التاريخ")
    description = models.TextField(verbose_name="الوصف / البيان")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="تم إنشاؤه بواسطة")
    created_at = models.DateTimeField(auto_now_add=True)

    # حقل لربط القيد بمستند آخر (فاتورة مبيعات، أمر شراء، إلخ)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_document = GenericForeignKey('content_type', 'object_id')

    def is_balanced(self):
        """
        يتحقق مما إذا كان مجموع المدين يساوي مجموع الدائن.
        """
        total_debits = self.transactions.aggregate(Sum('debit'))['debit__sum'] or 0
        total_credits = self.transactions.aggregate(Sum('credit'))['credit__sum'] or 0
        return total_debits == total_credits

    def __str__(self):
        return f"قيد يومية #{self.id} بتاريخ {self.date}"

    class Meta:
        verbose_name = "قيد يومية"
        verbose_name_plural = "قيود اليومية"
        ordering = ['-date']


class Transaction(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='transactions', verbose_name="قيد اليومية")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name="الحساب")
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="مدين")
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="دائن")

    def __str__(self):
        return f"حركة على حساب {self.account.name}"
    
    def clean(self):
        # ضمان أن يكون أحد الحقلين (المدين أو الدائن) فقط يحتوي على قيمة
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("لا يمكن أن تكون الحركة مدينة ودائنة في نفس الوقت.")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("يجب إدخال قيمة في حقل المدين أو الدائن.")

    class Meta:
        verbose_name = "حركة محاسبية"
        verbose_name_plural = "الحركات المحاسبية"
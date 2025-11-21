#from django.contrib import admin

# Register your models here.

# accounting/admin.py

from django.contrib import admin
from .models import Account, JournalEntry, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 2  # ابدأ بمدخلين فارغين (واحد للمدين وواحد للدائن)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'name', 'account_type', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('name', 'account_number')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'description', 'is_balanced')
    list_filter = ('date',)
    inlines = [TransactionInline]

    def save_model(self, request, obj, form, change):
        # تعيين المستخدم الحالي كمنشئ للقيد
        if not obj.pk: # عند الإنشاء فقط
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
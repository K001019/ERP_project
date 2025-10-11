#from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Customer, SalesOrder, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # عدد الحقول الفارغة الجديدة التي تظهر

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status', 'total_amount')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name',)
    inlines = [OrderItemInline] # هنا نضيف بنود الطلب مباشرة

admin.site.register(Customer)
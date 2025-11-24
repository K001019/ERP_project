#from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Supplier, Product, StockMovement
from simple_history.admin import SimpleHistoryAdmin
@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'sku', 'quantity_in_stock', 'sale_price', 'supplier')
    list_filter = ('supplier',)
    search_fields = ('name', 'sku')

admin.site.register(Supplier)
admin.site.register(StockMovement)
#```    *(هنا استخدمنا `ProductAdmin` لتخصيص طريقة عرض المنتجات في لوحة التحكم لتكون أكثر فائدة).*
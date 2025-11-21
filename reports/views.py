#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from employees.models import Employee
from inventory.models import Product
from sales.models import SalesOrder, Customer, OrderItem
from django.db.models import Sum, Count
from django.db.models import F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import json


@login_required
def dashboard_view(request):
    # 1. الإحصائيات الأساسية
    employee_count = Employee.objects.count()
    product_count = Product.objects.count()
    sales_order_count = SalesOrder.objects.count()

    # 2. بيانات الرسم البياني الأول: أفضل 5 منتجات مبيعًا (حسب الكمية)
    top_products_data = OrderItem.objects.values('product__name') \
        .annotate(total_sold=Sum('quantity')) \
        .order_by('-total_sold')[:5]
    
    top_products_labels = [item['product__name'] for item in top_products_data]
    top_products_values = [item['total_sold'] for item in top_products_data]

    # 3. بيانات الرسم البياني الثاني: إجمالي المبيعات لآخر 6 أشهر
    six_months_ago = timezone.now() - timedelta(days=90)
    monthly_sales_data = SalesOrder.objects \
        .filter(order_date__gte=six_months_ago) \
        .annotate(month=TruncMonth('order_date')) \
        .values('month') \
        .annotate(total_sales=Sum('total_amount')) \
        .order_by('month')

    # تنسيق البيانات لتكون متوافقة مع Chart.js
    monthly_sales_labels = [item['month'].strftime("%b %Y") for item in monthly_sales_data]
    monthly_sales_values = [float(item['total_sales']) for item in monthly_sales_data]

    context = {
        'employee_count': employee_count,
        'product_count': product_count,
        'sales_order_count': sales_order_count,
        # تحويل البيانات إلى JSON لتمريرها بأمان إلى JavaScript
        'top_products_labels': json.dumps(top_products_labels),
        'top_products_values': json.dumps(top_products_values),
        'monthly_sales_labels': json.dumps(monthly_sales_labels),
        'monthly_sales_values': json.dumps(monthly_sales_values),
    }
    return render(request, 'reports/dashboard.html', context)

# --- دالة العرض الجديدة للتقارير ---
@login_required
@permission_required('reports.view_report', raise_exception=True) # سننشئ هذه الصلاحية لاحقًا
def reports_view(request):
    # التقرير الأول: المنتجات الأكثر مبيعًا (حسب الكمية)
    top_selling_products = OrderItem.objects.values('product__name').annotate(
        total_quantity_sold=Sum('quantity')
    ).order_by('-total_quantity_sold')[:10] # أعلى 10 منتجات

    # التقرير الثاني: العملاء الأكثر شراءً (حسب قيمة الطلبات)
    top_customers = SalesOrder.objects.values('customer__name').annotate(
        total_spent=Sum('total_amount')
    ).order_by('-total_spent')[:10] # أعلى 10 عملاء

    # التقرير الثالث: ملخص المخزون (المنتجات التي على وشك النفاذ)
    low_stock_products = Product.objects.filter(quantity_in_stock__lte=F('reorder_level'))

    context = {
        'top_selling_products': top_selling_products,
        'top_customers': top_customers,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'reports/main_report.html', context)
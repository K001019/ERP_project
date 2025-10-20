#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from employees.models import Employee
from inventory.models import Product
from sales.models import SalesOrder, Customer, OrderItem
from django.db.models import Sum, Count
from django.db.models import F

@login_required # هذا السطر يضمن أن المستخدم يجب أن يكون مسجلاً للدخول لرؤية هذه الصفحة
def dashboard_view(request):
    # إحصائيات بسيطة للعرض
    employee_count = Employee.objects.count()
    product_count = Product.objects.count()
    sales_order_count = SalesOrder.objects.count()
    
    # يمكن إضافة المزيد من الإحصائيات المعقدة هنا لاحقاً
    
    context = {
        'employee_count': employee_count,
        'product_count': product_count,
        'sales_order_count': sales_order_count,
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
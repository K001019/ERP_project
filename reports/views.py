#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from inventory.models import Product
from sales.models import SalesOrder

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
#from django.shortcuts import render

# Create your views here.
# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, StockMovement
from .forms import ProductForm # استيراد النموذج الجديد
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q # استيراد Q object للبحث المعقد
import pandas as pd
from statsmodels.tsa.api import ExponentialSmoothing
from django.db.models.functions import TruncMonth
from django.db.models import Sum
#from .models import StockMovement
# ---- CRUD Views for Products ----

@login_required
@permission_required('inventory.view_product', raise_exception=True)
def product_list_view(request):
    # الحصول على قيمة البحث من الرابط، إذا كانت موجودة
    search_query = request.GET.get('q', None)
    products = Product.objects.all().order_by('name')
    if search_query:
        # استخدام Q objects للبحث في عدة حقول في نفس الوقت
        # __icontains تعني "يحتوي على" وهي غير حساسة لحالة الأحرف
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    context = {
        'products': products,
        'search_query': search_query, # نمرر قيمة البحث للقالب لنتمكن من عرضها في مربع البحث
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
@permission_required('inventory.add_product', raise_exception=True)
def product_create_view(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form': form})

@login_required
@permission_required('inventory.change_product', raise_exception=True)
def product_update_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'product': product})

@login_required
@permission_required('inventory.delete_product', raise_exception=True)
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
@permission_required('inventory.view_product', raise_exception=True) # يمكن إنشاء صلاحية مخصصة لاحقًا
def prediction_view(request):
    # الحصول على جميع المنتجات
    products = Product.objects.all()
    prediction_results = []

    for product in products:
        # جمع بيانات الاستهلاك الشهري من حركة المخزون
        consumption_data = StockMovement.objects.filter(
            product=product,
            movement_type='OUT'
        ).annotate(
            month=TruncMonth('movement_date')
        ).values('month').annotate(
            monthly_consumption=Sum('quantity')
        ).values('month', 'monthly_consumption').order_by('month')

        result = {
            'product_name': product.name,
            'current_stock': product.quantity_in_stock,
            'reorder_level': product.reorder_level,
            'predicted_consumption': 'لا توجد بيانات كافية',
            'suggested_reorder': 0
        }

        if len(consumption_data) >= 3: # نحتاج على الأقل 3 أشهر من البيانات
            try:
                # تحويل البيانات إلى Pandas DataFrame
                df = pd.DataFrame(list(consumption_data))
                df.set_index('month', inplace=True)
                
                # إعداد وتدريب النموذج
                # seasonal_periods=12 إذا كانت لديك بيانات لعدة سنوات
                model = ExponentialSmoothing(df['monthly_consumption'], trend='add', seasonal=None).fit()
                
                # التنبؤ للشهر القادم
                forecast = model.forecast(1) # تنبؤ لفترة واحدة قادمة
                predicted_quantity = int(round(forecast.iloc[0], 0))
                
                # التأكد من أن التنبؤ ليس سالبًا
                predicted_quantity = max(0, predicted_quantity)
                
                result['predicted_consumption'] = predicted_quantity
                
                # حساب الكمية المقترح إعادة طلبها
                # (الاستهلاك المتوقع - المخزون الحالي + حد إعادة الطلب)
                suggested_reorder = predicted_quantity - product.quantity_in_stock + product.reorder_level
                result['suggested_reorder'] = max(0, suggested_reorder)

            except Exception as e:
                result['predicted_consumption'] = f"خطأ في التحليل: {e}"

        prediction_results.append(result)

    return render(request, 'inventory/prediction_report.html', {'results': prediction_results})
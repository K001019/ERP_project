#from django.shortcuts import render

# Create your views here.
# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, StockMovement, PurchaseOrder, PurchaseOrderItem
from .forms import ProductForm, PurchaseOrderForm, PurchaseOrderItemFormSet # استيراد النموذج الجديد
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q # استيراد Q object للبحث المعقد
import pandas as pd
from statsmodels.tsa.api import ExponentialSmoothing
from django.db.models.functions import TruncMonth
from django.db.models import Sum
import csv
from django.http import HttpResponse
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta, date
#from .models import StockMovement
# ---- CRUD Views for Products ----

@login_required
@permission_required('inventory.view_product', raise_exception=True)
def product_list_view(request):
    search_query = request.GET.get('q', None)
    
    # لا نطبق الترتيب هنا بعد الآن
    products_list = Product.objects.select_related('supplier').all()

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    # تطبيق الترتيب هنا
    products_list = products_list.order_by('name')

    # --- الجزء الجديد للترقيم ---
    paginator = Paginator(products_list, 10) # عرض 10 منتجات في كل صفحة
    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        # إذا لم تكن 'page' رقمًا، اعرض الصفحة الأولى
        products = paginator.page(1)
    except EmptyPage:
        # إذا كانت 'page' خارج النطاق، اعرض آخر صفحة من النتائج
        products = paginator.page(paginator.num_pages)
    # --- نهاية جزء الترقيم ---
    
    context = {
        'products': products, # مرر كائن الصفحة بدلاً من القائمة الكاملة
        'search_query': search_query,
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
    """
    دالة عرض سريعة جدًا لعرض نتائج التنبؤ المحسوبة مسبقًا،
    بالإضافة إلى مخطط بياني لنشاط المبيعات اليومي.
    """
    # --------------------------------------------------
    # --- الجزء الأول: إعداد بيانات الجدول (يبقى كما هو) ---
    # --------------------------------------------------
    products = Product.objects.all()
    prediction_results = []
    for product in products:
        predicted_monthly_consumption = round(product.daily_consumption_rate * 30)
        suggested_reorder = predicted_monthly_consumption - product.quantity_in_stock + product.reorder_level
        result = {
            'product_name': product.name,
            'current_stock': product.quantity_in_stock,
            'reorder_level': product.reorder_level,
            'daily_rate': f"{product.daily_consumption_rate:.2f}", 
            'predicted_consumption': predicted_monthly_consumption,
            'suggested_reorder': max(0, suggested_reorder),
            'last_updated': product.prediction_last_updated,
        }
        prediction_results.append(result)

    # --------------------------------------------------
    # --- الجزء الثاني (الجديد): إعداد بيانات المخطط البياني ---
    # --------------------------------------------------
    
    # 1. تحديد النطاق الزمني: آخر 30 يومًا
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    # 2. الاستعلام عن إجمالي كميات المبيعات مجمعة حسب اليوم
    daily_sales_data = StockMovement.objects.filter(
        movement_type='OUT',
        movement_date__date__gte=thirty_days_ago
    ).annotate(
        day=TruncDay('movement_date')  # تجميع حسب اليوم
    ).values('day').annotate(
        daily_total=Sum('quantity')   # حساب المجموع اليومي
    ).order_by('day')

    # 3. معالجة البيانات لملء الأيام التي لا توجد فيها مبيعات (قيمتها صفر)
    # هذا يضمن أن المخطط البياني مستمر ومتصل
    sales_dict = {item['day'].strftime('%Y-%m-%d'): item['daily_total'] for item in daily_sales_data}
    chart_labels = []
    chart_values = []
    
    # حلقة على كل يوم في آخر 30 يومًا
    for i in range(30, -1, -1):
        current_date = timezone.now().date() - timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # إضافة اليوم للتسميات (Labels) في المخطط
        chart_labels.append(current_date.strftime('%d %b')) # مثال: "15 Dec"
        
        # إضافة قيمة المبيعات لهذا اليوم، أو صفر إذا لم تكن هناك مبيعات
        chart_values.append(sales_dict.get(date_str, 0))

    # 4. تجميع كل البيانات في الـ context
    context = {
        'results': prediction_results,
        'sales_chart_labels': json.dumps(chart_labels),
        'sales_chart_values': json.dumps(chart_values),
    }

    return render(request, 'inventory/prediction_report.html', context)

@login_required
@permission_required('inventory.view_product', raise_exception=True)
def export_products_csv(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="products_list.csv"'},
    )
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['اسم المنتج', 'SKU', 'الكمية في المخزون', 'سعر الشراء', 'سعر البيع', 'وحدة القياس', 'المورد'])

    products = Product.objects.all()
    for product in products:
        # نحتاج لجلب اسم المورد بشكل منفصل لأنه علاقة
        supplier_name = product.supplier.name if product.supplier else ''
        writer.writerow([
            product.name,
            product.sku,
            product.quantity_in_stock,
            product.purchase_price,
            product.sale_price,
            product.unit_of_measure,
            supplier_name
        ])

    return response

@login_required
# @permission_required('inventory.view_purchaseorder', raise_exception=True) # سنضيف الصلاحيات لاحقًا
def purchase_order_list_view(request):
    orders = PurchaseOrder.objects.all().order_by('-order_date')
    context = {'orders': orders}
    return render(request, 'inventory/purchase_order_list.html', context)


@login_required
# @permission_required('inventory.view_purchaseorder', raise_exception=True)
def purchase_order_detail_view(request, pk):
    order = get_object_or_404(PurchaseOrder.objects.prefetch_related('items', 'items__product'), pk=pk)
    context = {'order': order}
    return render(request, 'inventory/purchase_order_detail.html', context)


@login_required
# @permission_required('inventory.add_purchaseorder', raise_exception=True)
def purchase_order_create_view(request):
    form = PurchaseOrderForm(request.POST or None)
    formset = PurchaseOrderItemFormSet(request.POST or None, queryset=PurchaseOrderItem.objects.none())

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # حفظ أمر الشراء الرئيسي
                    purchase_order = form.save()
                    
                    # حفظ بنود أمر الشراء وربطها بالأمر الرئيسي
                    items = formset.save(commit=False)
                    for item in items:
                        item.purchase_order = purchase_order
                        item.save()
                    
                    messages.success(request, f"تم إنشاء أمر الشراء #{purchase_order.id} بنجاح.")
                    return redirect('purchase_order_list')
            except Exception as e:
                messages.error(request, f"حدث خطأ أثناء إنشاء أمر الشراء: {e}")
    
    context = {
        'form': form,
        'formset': formset
    }
    return render(request, 'inventory/purchase_order_form.html', context)


@login_required
# @permission_required('inventory.change_purchaseorder', raise_exception=True)
def purchase_order_update_view(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    # لا نسمح بتعديل الطلبات التي تم استلامها بالفعل
    if order.status == 'RECEIVED':
        messages.error(request, "لا يمكن تعديل أمر شراء تم استلامه بالفعل.")
        return redirect('purchase_order_detail', pk=pk)

    form = PurchaseOrderForm(request.POST or None, instance=order)
    formset = PurchaseOrderItemFormSet(request.POST or None, instance=order)

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    messages.success(request, f"تم تحديث أمر الشراء #{order.id} بنجاح.")
                    return redirect('purchase_order_detail', pk=order.pk)
            except Exception as e:
                messages.error(request, f"حدث خطأ أثناء تحديث أمر الشراء: {e}")

    context = {
        'form': form,
        'formset': formset,
        'order': order
    }
    return render(request, 'inventory/purchase_order_form.html', context)


@login_required
# @permission_required('inventory.change_purchaseorder', raise_exception=True) # صلاحية خاصة للاستلام
def receive_purchase_order_view(request, pk):
    order = get_object_or_404(PurchaseOrder.objects.prefetch_related('items__product'), pk=pk)
    
    if order.status == 'RECEIVED':
        messages.warning(request, "هذا الطلب تم استلامه مسبقًا.")
        return redirect('purchase_order_detail', pk=pk)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # تحديث كميات المخزون لكل منتج في الطلب
                for item in order.items.all():
                    product = item.product
                    product.quantity_in_stock += item.quantity
                    product.save()

                    # (اختياري) تسجيل حركة مخزون لإضافتها للسجل
                    StockMovement.objects.create(
                        product=product,
                        movement_type='IN',
                        quantity=item.quantity,
                        moved_by=request.user,
                        notes=f'استلام من أمر شراء رقم #{order.id}'
                    )

                # تحديث حالة أمر الشراء إلى "تم الاستلام"
                order.status = 'RECEIVED'
                order.save()
                
                messages.success(request, f"تم استلام البضاعة وتحديث المخزون بنجاح لأمر الشراء #{order.id}.")
                return redirect('purchase_order_detail', pk=pk)
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء معالجة الاستلام: {e}")

    context = {'order': order}
    return render(request, 'inventory/receive_purchase_order_confirm.html', context)
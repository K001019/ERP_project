#from django.shortcuts import render

# Create your views here.
# sales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer, SalesOrder, OrderItem
from .forms import CustomerForm, SalesOrderForm, OrderItemFormSet # استيراد النماذج الجديدة
from django.db import transaction # مهم جداً للمعاملات الآمنة
from django.contrib import messages # لاستيراد نظام الرسائل


@login_required
def customer_list_view(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'sales/customer_list.html', {'customers': customers})

@login_required
def customer_create_view(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html', {'form': form})

@login_required
def customer_update_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html', {'form': form, 'customer': customer})

@login_required
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'sales/customer_confirm_delete.html', {'customer': customer})

@login_required
def sales_order_list_view(request):
    orders = SalesOrder.objects.all().order_by('-order_date') # عرض الأحدث أولاً
    return render(request, 'sales/sales_order_list.html', {'orders': orders})

@login_required
def sales_order_detail_view(request, pk):
    order = get_object_or_404(SalesOrder.objects.prefetch_related('items', 'items__product'), pk=pk)
    # prefetch_related لتحسين الأداء وتقليل استعلامات قاعدة البيانات
    return render(request, 'sales/sales_order_detail.html', {'order': order})

@login_required
def sales_order_create_view(request):
    form = SalesOrderForm(request.POST or None)
    formset = OrderItemFormSet(request.POST or None, queryset=OrderItem.objects.none())

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # الخطوة 1: حفظ الكائن الرئيسي (الأب) أولاً
                    order = form.save(commit=False)
                    if hasattr(request.user, 'employee_profile'):
                        order.created_by = request.user.employee_profile
                    order.save() # الآن 'order' لديه id في قاعدة البيانات

                    # الخطوة 2: التعامل مع بنود الطلب (الأبناء)
                    total_order_amount = 0
                    
                    # استخراج البيانات من الـ formset للتحقق من المخزون وتحديثه
                    items_to_save = []
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                            product = item_form.cleaned_data.get('product')
                            quantity = item_form.cleaned_data.get('quantity')

                            if product and quantity > 0:
                                # التحقق من المخزون
                                if product.quantity_in_stock < quantity:
                                    messages.error(request, f"الكمية للمنتج '{product.name}' غير متوفرة (المتوفر: {product.quantity_in_stock}).")
                                    raise Exception("Insufficient stock")
                                
                                # تحديث كمية المخزون
                                product.quantity_in_stock -= quantity
                                product.save()

                                # تجهيز كائن OrderItem للحفظ لاحقًا (بدون حفظه الآن)
                                item = item_form.save(commit=False)
                                item.order = order # الربط الصريح مع الأب الذي تم حفظه
                                item.unit_price = product.sale_price
                                item.subtotal = item.unit_price * quantity
                                total_order_amount += item.subtotal
                                items_to_save.append(item)

                    if not items_to_save:
                        messages.error(request, "يجب إضافة منتج واحد على الأقل.")
                        raise Exception("No items in formset")

                    # الخطوة 3: حفظ جميع بنود الطلب دفعة واحدة باستخدام bulk_create
                    OrderItem.objects.bulk_create(items_to_save)
                    
                    # الخطوة 4: تحديث المبلغ الإجمالي للطلب الرئيسي
                    order.total_amount = total_order_amount
                    order.save()

                messages.success(request, f"تم إنشاء أمر المبيع رقم #{order.id} بنجاح.")
                return redirect('sales_order_list')

            except Exception as e:
                print(f"An error occurred: {e}")
                if not any(request.GET.get(messages.DEFAULT_LEVELS['ERROR'], [])):
                    messages.error(request, "حدث خطأ. يرجى مراجعة البيانات والمحاولة مرة أخرى.")

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'sales/sales_order_form.html', context)
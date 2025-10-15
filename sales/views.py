#from django.shortcuts import render

# Create your views here.
# sales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer, SalesOrder, OrderItem
from .forms import CustomerForm, SalesOrderForm, OrderItemFormSet # استيراد النماذج الجديدة
from django.db import transaction # مهم جداً للمعاملات الآمنة
from django.contrib import messages # لاستيراد نظام الرسائل
from inventory.models import Product # <--- أضف هذا السطر لاستيراد نموذج المنتج

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

@login_required
def sales_order_update_view(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    form = SalesOrderForm(request.POST or None, instance=order)
    formset = OrderItemFormSet(request.POST or None, instance=order)

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                    # حلقة لمعالجة كل نموذج في الـ formset
                    for form_item in formset:
                        # إذا لم يكن النموذج صالحًا أو لا يحتوي على بيانات، تجاهله
                        if not form_item.is_valid() or not form_item.has_changed():
                            continue

                        # استخراج البيانات
                        instance = form_item.instance
                        new_quantity = form_item.cleaned_data.get('quantity', 0)
                        is_deleted = form_item.cleaned_data.get('DELETE', False)
                        
                        # الحالة 1: حذف بند موجود
                        if instance.pk and is_deleted:
                            instance.product.quantity_in_stock += instance.quantity
                            instance.product.save()
                            instance.delete()
                            continue

                        # الحالة 2: تعديل بند موجود
                        if instance.pk and not is_deleted:
                            original_quantity = instance.quantity
                            quantity_diff = original_quantity - new_quantity
                            
                            product_to_update = instance.product # استخدام المنتج المرتبط مباشرة
                            
                            if quantity_diff < 0 and abs(quantity_diff) > product_to_update.quantity_in_stock:
                                messages.error(request, f"Not enough stock for '{product_to_update.name}'.")
                                raise Exception("Insufficient stock")
                            
                            product_to_update.quantity_in_stock += quantity_diff
                            product_to_update.save()
                            
                            # حفظ النموذج الفردي لتطبيق التغييرات (مثل الكمية الجديدة)
                            form_item.save()

                        # الحالة 3: إضافة بند جديد
                        elif not instance.pk and not is_deleted:
                            product = form_item.cleaned_data.get('product')
                            if product and new_quantity > 0:
                                if product.quantity_in_stock < new_quantity:
                                    messages.error(request, f"Not enough stock for new item '{product.name}'.")
                                    raise Exception("Insufficient stock")
                                
                                product.quantity_in_stock -= new_quantity
                                product.save()
                                
                                new_item = form_item.save(commit=False)
                                new_item.order = order
                                new_item.unit_price = product.sale_price
                                new_item.save()
                    
                    # إعادة حساب الإجمالي في النهاية
                    order.refresh_from_db()
                    total_amount = sum(item.quantity * item.unit_price for item in order.items.all() if item.unit_price)
                    order.total_amount = total_amount
                    order.save()

                messages.success(request, f"تم تحديث أمر المبيع رقم #{order.id} بنجاح.")
                return redirect('sales_order_list')

            except Exception as e:
                print(f"An error occurred during update: {e}")
                if not any(message.level == messages.ERROR for message in messages.get_messages(request)):
                    messages.error(request, "An error occurred during the update.")
        else:
            messages.error(request, "Invalid data submitted.")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    context = {'form': form, 'formset': formset, 'order': order}
    return render(request, 'sales/sales_order_form.html', context)
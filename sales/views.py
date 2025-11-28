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
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse

@login_required
@permission_required('sales.view_customer', raise_exception=True)
def customer_list_view(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'sales/customer_list.html', {'customers': customers})

@login_required
@permission_required('sales.add_customer', raise_exception=True)
def customer_create_view(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, f"تمت إضافة العميل '{form.instance.name}' بنجاح.")
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html', {'form': form})

@login_required
@permission_required('sales.change_customer', raise_exception=True)
def customer_update_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        messages.success(request, f"تم تحديث بيانات العميل '{form.instance.name}' بنجاح.")
        return redirect('customer_list')
    return render(request, 'sales/customer_form.html', {'form': form, 'customer': customer})

@login_required
@permission_required('sales.delete_customer', raise_exception=True)
def customer_delete_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer_name = customer.name
        customer.delete()
        messages.success(request, f"تم حذف العميل '{customer_name}' بنجاح.")
        return redirect('customer_list')
    return render(request, 'sales/customer_confirm_delete.html', {'customer': customer})

@login_required
@permission_required('sales.view_salesorder', raise_exception=True)
def sales_order_list_view(request):
    # جلب كل أوامر المبيعات
    orders_query = SalesOrder.objects.select_related('customer').all().order_by('-order_date')

    # --- الجزء الجديد للفلترة ---
    # الحصول على قيمة الفلتر من الطلب (request.GET)
    status_filter = request.GET.get('status', None)
    
    # إذا كانت هناك قيمة للفلتر وكانت ضمن الخيارات المتاحة، قم بالتصفية
    if status_filter and status_filter in [choice[0] for choice in SalesOrder.STATUS_CHOICES]:
        orders_query = orders_query.filter(status=status_filter)
    # --- نهاية جزء الفلترة ---

    context = {
        'orders': orders_query,
        'status_choices': SalesOrder.STATUS_CHOICES, # تمرير الخيارات للقالب
        'current_status': status_filter, # تمرير الفلتر الحالي لتمييزه
    }
    return render(request, 'sales/sales_order_list.html', context)

@login_required
@permission_required('sales.view_salesorder', raise_exception=True)
def sales_order_detail_view(request, pk):
    order = get_object_or_404(SalesOrder.objects.prefetch_related('items', 'items__product'), pk=pk)
    # prefetch_related لتحسين الأداء وتقليل استعلامات قاعدة البيانات
    return render(request, 'sales/sales_order_detail.html', {'order': order})

@login_required
@permission_required('sales.add_salesorder', raise_exception=True)
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
@permission_required('sales.change_salesorder', raise_exception=True)
def sales_order_update_view(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    form = SalesOrderForm(request.POST or None, instance=order)
    formset = OrderItemFormSet(request.POST or None, instance=order)

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save() # حفظ التغييرات على أمر البيع الرئيسي (العميل، الحالة)

                    for item_form in formset:
                        if not item_form.is_valid():
                            continue # تجاهل النماذج غير الصالحة

                        instance = item_form.instance
                        new_quantity = item_form.cleaned_data.get('quantity', 0)
                        is_deleted = item_form.cleaned_data.get('DELETE', False)
                        product = item_form.cleaned_data.get('product')

                        # الحالة 1: حذف بند موجود
                        if instance.pk and is_deleted:
                            instance.product.quantity_in_stock += instance.quantity
                            instance.product.save()
                            instance.delete()
                            continue

                        # إذا لم يتغير شيء في النموذج، انتقل للتالي (لتجنب العمليات غير الضرورية)
                        if not item_form.has_changed() and instance.pk:
                            continue

                        # الحالة 2: تعديل بند موجود
                        if instance.pk and not is_deleted:
                            original_quantity = OrderItem.objects.get(pk=instance.pk).quantity
                            quantity_diff = original_quantity - new_quantity
                            product_to_update = instance.product

                            if quantity_diff < 0 and abs(quantity_diff) > product_to_update.quantity_in_stock:
                                messages.error(request, f"الكمية للمنتج '{product_to_update.name}' غير كافية.")
                                raise Exception("Insufficient stock")

                            product_to_update.quantity_in_stock += quantity_diff
                            product_to_update.save()
                            
                            # تحديث الكمية والمجموع الفرعي في البند
                            instance.quantity = new_quantity
                            instance.subtotal = new_quantity * instance.unit_price
                            instance.save()

                        # الحالة 3: إضافة بند جديد (الحل الحاسم هنا)
                        elif not instance.pk and not is_deleted and product and new_quantity > 0:
                            if product.quantity_in_stock < new_quantity:
                                messages.error(request, f"الكمية للمنتج الجديد '{product.name}' غير كافية.")
                                raise Exception("Insufficient stock")
                            
                            product.quantity_in_stock -= new_quantity
                            product.save()
                            
                            # إنشاء البند الجديد مع كل البيانات اللازمة
                            new_item = item_form.save(commit=False)
                            new_item.order = order
                            new_item.unit_price = product.sale_price # <--- هذا السطر يحل المشكلة
                            new_item.subtotal = new_quantity * new_item.unit_price # <--- وهذا يضمن صحة الحساب
                            new_item.save()

                    # أخيرًا، قم بإعادة حساب المبلغ الإجمالي للطلب
                    order.refresh_from_db()
                    total_amount = sum(item.subtotal for item in order.items.all() if item.subtotal is not None)
                    order.total_amount = total_amount
                    order.save()

                messages.success(request, f"تم تحديث أمر المبيع رقم #{order.id} بنجاح.")
                return redirect('sales_order_list')

            except Exception as e:
                print(f"An error occurred during update: {e}")
                if not any(message.level == messages.ERROR for message in messages.get_messages(request)):
                    messages.error(request, "حدث خطأ أثناء التحديث. يرجى المحاولة مرة أخرى.")
        else:
            messages.error(request, "البيانات المدخلة غير صالحة.")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    context = {'form': form, 'formset': formset, 'order': order}
    return render(request, 'sales/sales_order_form.html', context)

@login_required
def get_product_price(request, pk):
    """
    دالة API بسيطة لجلب سعر البيع لمنتج معين.
    """
    try:
        product = Product.objects.get(pk=pk)
        data = {
            'price': product.sale_price
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
@login_required
@permission_required('sales.view_salesorder', raise_exception=True)
def sales_order_invoice_pdf(request, pk):
    """
    دالة لإنشاء وتنزيل فاتورة PDF لأمر مبيع معين.
    """
    order = get_object_or_404(SalesOrder.objects.prefetch_related('items', 'items__product'), pk=pk)
    
    # تحويل القالب إلى سلسلة نصية من HTML مع تمرير بيانات الطلب
    html_string = render_to_string('sales/invoice_template.html', {'order': order})
    
    # إنشاء استجابة HTTP مع النوع المناسب لملف PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice-{order.id}.pdf"'
    
    # استخدام WeasyPrint لكتابة ملف PDF مباشرة في الاستجابة
    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    
    return response
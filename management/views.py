# management/views.py

from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.db import models
from .forms import UserUpdateForm, AdminPasswordChangeForm
from itertools import chain
from operator import attrgetter
from employees.models import Employee
from inventory.models import Product
from sales.models import SalesOrder
from simple_history.utils import get_history_model_for_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
# دالة مساعدة للتحقق مما إذا كان المستخدم مديرًا (superuser)
def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser) # يضمن أن مدراء النظام فقط يمكنهم الوصول
def user_list_view(request):
    # نستخدم prefetch_related لتحسين الأداء وتقليل استعلامات قاعدة البيانات
    users = User.objects.prefetch_related('groups').all().order_by('username')
    context = {
        'users': users
    }
    return render(request, 'management/user_list.html', context)

@login_required
@user_passes_test(is_superuser)
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"تم تحديث بيانات المستخدم '{user.username}' بنجاح.")
            return redirect('user_list')
    
    context = {
        'form': form,
        'user_obj': user # نمرر المستخدم للقالب لعرض اسمه
    }
    return render(request, 'management/user_form.html', context)

@login_required
@user_passes_test(is_superuser)
def change_user_password_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = AdminPasswordChangeForm(user, request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f"تم تغيير كلمة مرور المستخدم '{user.username}' بنجاح.")
            return redirect('user_edit', pk=user.pk) # العودة لصفحة تعديل المستخدم
    
    context = {
        'form': form,
        'user_obj': user
    }
    return render(request, 'management/change_password_form.html', context)

@login_required
@user_passes_test(is_superuser)
def audit_trail_view(request):
    employee_history = Employee.history.all()
    product_history = Product.history.all()
    sales_order_history = SalesOrder.history.all()
    all_history = sorted(
        chain(employee_history, product_history, sales_order_history),
        key=attrgetter('history_date'),
        reverse=True
    )
    # إضافة الخصائص التي نحتاجها في القالب مباشرة إلى كل كائن
    for record in all_history:
        # الحصول على اسم النموذج الأصلي وتحويله إلى slug (نص مناسب للـ URL)
        model_name = record.history_object.__class__.__name__.replace('Historical', '').lower()
        record.model_name_slug = model_name

        # الحصول على الاسم المقروء للنموذج (للجدول)
        record.verbose_name = record.instance._meta.verbose_name
    
    paginated_history = all_history[:100]

    context = {
        'history_records': paginated_history,
    }
    return render(request, 'management/audit_trail.html', context)

@login_required
@user_passes_test(is_superuser)
def history_detail_view(request, model_name, pk, history_id):
    # تحديد النموذج الأصلي بناءً على الاسم
    model_map = {
        'employee': Employee,
        'product': Product,
        'salesorder': SalesOrder,
    }
    model = model_map.get(model_name)
    if not model:
        raise Http404("Model not found")

    # جلب النموذج التاريخي المرتبط
    HistoryModel = get_history_model_for_model(model)
    
    # جلب النسخة التاريخية المحددة
    history_record = get_object_or_404(HistoryModel, history_id=history_id)
    
    # جلب النسخة السابقة للمقارنة
    prev_record = history_record.prev_record
    
    # قائمة لتخزين التغييرات
    changed_fields = []

    # إذا كان هناك سجل سابق (أي أنها ليست عملية "إنشاء")
    if prev_record:
        # استخدام وظيفة diff_against للمقارنة
        delta = history_record.diff_against(prev_record)
        for change in delta.changes:
            changed_fields.append({
                'field': change.field,
                'old': change.old,
                'new': change.new,
            })
            
    context = {
        'record': history_record,
        'changed_fields': changed_fields,
    }
    return render(request, 'management/history_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def manage_permissions_view(request):
    app_labels = ['employees', 'inventory', 'sales', 'reports', 'accounting']
    excluded_models = ['stockmovement', 'orderitem', 'purchaseorderitem', 'transaction', 
                       'historicalemployee', 'historicalproduct', 'historicalsalseorder', 'report'] # استثناء نماذج لا تحتاج لإدارة

    content_types = ContentType.objects.filter(app_label__in=app_labels).exclude(model__in=excluded_models)
    
    permissions = Permission.objects.filter(content_type__in=content_types).select_related('content_type')
    
    groups = Group.objects.all()

    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            selected_permissions_ids = request.POST.getlist('permissions')
            selected_permissions = Permission.objects.filter(id__in=selected_permissions_ids)
            group.permissions.set(selected_permissions)
            messages.success(request, f"تم تحديث صلاحيات دور '{group.name}' بنجاح.")
            return redirect('manage_permissions')

    context = {
        'permissions': permissions,
        'groups': groups,
        'content_types': content_types,
    }
    return render(request, 'management/manage_permissions.html', context)
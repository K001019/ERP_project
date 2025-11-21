# employees/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .models import Employee
from .forms import EmployeeForm
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.contrib import messages
import csv
from django.http import HttpResponse

@login_required
@permission_required('employees.view_employee', raise_exception=True)
def employee_list_view(request):
    employees = Employee.objects.all().order_by('first_name')
    context = {'employees': employees}
    return render(request, 'employees/employee_list.html', context)

@login_required
@permission_required('employees.add_employee', raise_exception=True)
@transaction.atomic
def employee_create_view(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['email'].split('@')[0].lower().replace(' ', '')
            password = User.objects.make_random_password()

            counter = 1
            base_username = username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(username=username, email=form.cleaned_data['email'], password=password)
            
            selected_role = form.cleaned_data.get('role')
            if selected_role:
                user.groups.add(selected_role)
            
            employee = form.save(commit=False)
            employee.user = user
            employee.save()

            messages.success(request, f"تم إنشاء حساب للموظف '{employee.first_name}' بنجاح.")
            
            # رسالة بيانات الدخول الهامة (ستبقى ظاهرة)
            messages.warning(request, f"بيانات الدخول: اسم المستخدم: {username} | كلمة المرور: {password}. يرجى نسخ هذه البيانات قبل مغادرة الصفحة.")
            
            return redirect('employee_list')

    context = {'form': form}
    return render(request, 'employees/employee_form.html', context)

@login_required
@permission_required('employees.change_employee', raise_exception=True)
@transaction.atomic
def employee_update_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    user = employee.user

    initial_data = {}
    if user and user.groups.exists():
        initial_data['role'] = user.groups.first()

    form = EmployeeForm(request.POST or None, instance=employee, initial=initial_data)
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            
            if user:
                selected_role = form.cleaned_data.get('role')
                user.groups.clear()
                if selected_role:
                    user.groups.add(selected_role)
            
            messages.success(request, f"تم تحديث بيانات الموظف '{employee.first_name}' بنجاح.")
            return redirect('employee_list')

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'employees/employee_form.html', context)

@login_required
@permission_required('employees.delete_employee', raise_exception=True)
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee_name = employee.first_name
        # من المهم حذف المستخدم المرتبط، لأن الموظف يعتمد عليه
        if employee.user:
            employee.user.delete()
        
        # بعد حذف المستخدم، سيتم حذف الموظف تلقائيًا بسبب on_delete=models.CASCADE
        # ولكن من الأفضل حذفه صراحة لتجنب أي مشاكل
        employee.delete()
        
        messages.success(request, f"تم حذف الموظف '{employee_name}' وحسابه المرتبط بنجاح.")
        return redirect('employee_list')
    
    context = {'employee': employee}
    return render(request, 'employees/employee_confirm_delete.html', context)

@login_required
@permission_required('employees.view_employee', raise_exception=True)
def export_employees_csv(request):
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="employees_list.csv"'},
    )
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['الاسم الأول', 'الاسم الأخير', 'رقم الموظف', 'البريد الإلكتروني', 'رقم الهاتف', 'تاريخ التعيين', 'الراتب'])

    employees = Employee.objects.all().values_list('first_name', 'last_name', 'employee_id', 'email', 'phone_number', 'hire_date', 'salary')
    for employee in employees:
        writer.writerow(employee)

    return response
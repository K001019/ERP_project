#from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Employee
from .forms import EmployeeForm # استيراد النموذج الذي أنشأناه
from django.shortcuts import render, redirect, get_object_or_404 # أضف redirect و get_object_or_404
# Create your views here.
@login_required
def employee_list_view(request):
    employees = Employee.objects.all().order_by('first_name') # جلب كل الموظفين وترتيبهم بالاسم
    context = {
        'employees': employees,
    }
    return render(request, 'employees/employee_list.html', context)

@login_required
def employee_create_view(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            # يمكنك إضافة رسالة نجاح هنا
            return redirect('employee_list')
    
    context = {'form': form}
    return render(request, 'employees/employee_form.html', context)

@login_required
def employee_update_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('employee_list')
            
    context = {
        'form': form,
        'employee': employee, # نمرر الموظف للقالب لنتمكن من عرض اسمه في العنوان
    }
    return render(request, 'employees/employee_form.html', context)

@login_required
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.delete()
        # يمكنك إضافة رسالة نجاح هنا
        return redirect('employee_list')
        
    context = {
        'employee': employee
    }
    return render(request, 'employees/employee_confirm_delete.html', context)
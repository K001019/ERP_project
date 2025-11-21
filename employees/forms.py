# employees/forms.py
from django import forms
from .models import Employee
from django.contrib.auth.models import User, Group
class EmployeeForm(forms.ModelForm):
    
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False, # اجعله غير إلزامي في حال أردت موظفًا بدون دور
        label="الدور (الصلاحيات)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="اختر الدور الذي سيحدد صلاحيات وصول الموظف للنظام."
    )
    class Meta:
        model = Employee
        # تحديد الحقول التي نريدها أن تظهر في النموذج
        fields = [
            'first_name', 
            'last_name', 
            'employee_id', 
            'email', 
            'phone_number', 
            'hire_date', 
            'salary', 
            'address',
        ]
        
        # إضافة تنسيقات وتحسينات للنموذج (اختياري لكن موصى به)
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
 # لترتيب الحقول كما نريدها أن تظهر
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        # قائمة الحقول بالترتيب المرغوب
        ordered_fields = [
            'first_name', 'last_name', 'employee_id', 'email', 
            'phone_number', 'hire_date', 'salary', 'address', 'role'
        ]
        self.fields = {key: self.fields[key] for key in ordered_fields}
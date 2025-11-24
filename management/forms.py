# management/forms.py

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import SetPasswordForm

class UserUpdateForm(forms.ModelForm):
    # نعيد تعريف الحقول التي نريد التحكم بها
    username = forms.CharField(
        max_length=100,
        required=True,
        label="اسم المستخدم",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label="البريد الإلكتروني",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        required=False,
        label="الحساب نشط",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # حقل لاختيار دور واحد فقط للمستخدم
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="الدور (الصلاحيات)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'role']

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        # إذا كان للمستخدم دور (مجموعة) معين، قم بتعيينه كقيمة ابتدائية لحقل 'role'
        if self.instance.pk and self.instance.groups.exists():
            self.fields['role'].initial = self.instance.groups.first()

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        
        if commit:
            user.save()
            # تحديث الدور (المجموعة)
            selected_role = self.cleaned_data.get('role')
            user.groups.clear() # إزالة الأدوار القديمة
            if selected_role:
                user.groups.add(selected_role) # إضافة الدور الجديد
        
        return user
    
class AdminPasswordChangeForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs['class'] = 'form-control'
        self.fields['new_password1'].label = "كلمة المرور الجديدة"
        self.fields['new_password2'].widget.attrs['class'] = 'form-control'
        self.fields['new_password2'].label = "تأكيد كلمة المرور الجديدة"    
# sales/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Customer, SalesOrder, OrderItem
from inventory.models import Product
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number', 'address']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        # نموذج أمر المبيع الرئيسي
class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

# نموذج بنود الطلب
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}), # أضفنا كلاس خاص للجافاسكريبت
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input'}), # أضفنا كلاس خاص للجافاسكريبت
        }

# إنشاء مجموعة نماذج (Formset) لربط بنود الطلب بأمر المبيع
# سيسمح لنا هذا بإضافة وتعديل عدة بنود في نفس الصفحة
OrderItemFormSet = inlineformset_factory(
    SalesOrder,         # النموذج الأب (Parent Model)
    OrderItem,          # النموذج الابن (Child Model)
    form=OrderItemForm, # النموذج الذي سيُستخدم لكل بند
    extra=1,            # عدد النماذج الفارغة التي ستظهر بشكل افتراضي
    can_delete=True,    # السماح بحذف البنود من الواجهة
    can_delete_extra=True,
    #min_num=1, # يتطلب وجود بند واحد على الأقل
    #validate_min=True,
)
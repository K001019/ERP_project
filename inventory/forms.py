# inventory/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Product, PurchaseOrder, PurchaseOrderItem, Supplier
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 
            'sku', 
            'description', 
            'purchase_price', 
            'sale_price', 
            'quantity_in_stock',
            'unit_of_measure',
            'reorder_level',
            'supplier'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}), # form-select for dropdowns
        }
        
class PurchaseOrderForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="المورد"
    )
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_delivery_date', 'status']
        widgets = {
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)
#from django.shortcuts import render

# Create your views here.
# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, StockMovement
from .forms import ProductForm # استيراد النموذج الجديد
from django.contrib.auth.decorators import login_required, permission_required
# ... (دالة predict_inventory_needs تبقى كما هي)

# ---- CRUD Views for Products ----

@login_required
@permission_required('inventory.view_product', raise_exception=True)
def product_list_view(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'inventory/product_list.html', {'products': products})

@login_required
@permission_required('inventory.add_product', raise_exception=True)
def product_create_view(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form': form})

@login_required
@permission_required('inventory.change_product', raise_exception=True)
def product_update_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'product': product})

@login_required
@permission_required('inventory.delete_product', raise_exception=True)
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})
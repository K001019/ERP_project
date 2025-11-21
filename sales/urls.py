# sales/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.customer_list_view, name='customer_list'),
    path('add/', views.customer_create_view, name='customer_add'),
    path('<int:pk>/edit/', views.customer_update_view, name='customer_edit'),
    path('<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),
]

# مسارات العملاء
customer_patterns = [
    path('', views.customer_list_view, name='customer_list'),
    path('add/', views.customer_create_view, name='customer_add'),
    path('<int:pk>/edit/', views.customer_update_view, name='customer_edit'),
    path('<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),
]

# مسارات أوامر المبيعات
order_patterns = [
    path('', views.sales_order_list_view, name='sales_order_list'),
    path('add/', views.sales_order_create_view, name='sales_order_add'),
    path('<int:pk>/', views.sales_order_detail_view, name='sales_order_detail'),
    path('<int:pk>/edit/', views.sales_order_update_view, name='sales_order_edit'),
    path('<int:pk>/invoice/pdf/', views.sales_order_invoice_pdf, name='sales_order_invoice_pdf'),
]

# --- أنشئ قائمة جديدة لمسارات ה-API ---
api_patterns = [
    path('get-product-price/<int:pk>/', views.get_product_price, name='get_product_price'),
]

urlpatterns = [
    path('customers/', include(customer_patterns)),
    path('orders/', include(order_patterns)),
     # --- أضف هذا السطر لدمج مسارات ה-API ---
    path('api/', include(api_patterns)),
]

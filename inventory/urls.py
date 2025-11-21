# inventory/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('add/', views.product_create_view, name='product_add'),
    path('<int:pk>/edit/', views.product_update_view, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('predict/', views.prediction_view, name='product_prediction'),
    path('export/csv/', views.export_products_csv, name='product_export_csv'),
]

product_patterns = [
    path('', views.product_list_view, name='product_list'),
    path('add/', views.product_create_view, name='product_add'),
    path('<int:pk>/edit/', views.product_update_view, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('export/csv/', views.export_products_csv, name='product_export_csv'),
]
# --- مسارات أوامر الشراء الجديدة ---
purchase_order_patterns = [
    path('', views.purchase_order_list_view, name='purchase_order_list'),
    path('add/', views.purchase_order_create_view, name='purchase_order_add'),
    path('<int:pk>/', views.purchase_order_detail_view, name='purchase_order_detail'),
    path('<int:pk>/edit/', views.purchase_order_update_view, name='purchase_order_edit'),
    path('<int:pk>/receive/', views.receive_purchase_order_view, name='purchase_order_receive'),
]

urlpatterns = [
    path('products/', include(product_patterns)),
    path('purchase-orders/', include(purchase_order_patterns)), # <-- مسار رئيسي لأوامر الشراء
    path('predict/', views.prediction_view, name='product_prediction'), # أبقِ هذا المسار كما هو
]

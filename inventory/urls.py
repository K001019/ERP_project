# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('add/', views.product_create_view, name='product_add'),
    path('<int:pk>/edit/', views.product_update_view, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete_view, name='product_delete'),
]
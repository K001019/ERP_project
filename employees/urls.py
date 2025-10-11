from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list_view, name='employee_list'),
    path('add/', views.employee_create_view, name='employee_add'),
    path('<int:pk>/edit/', views.employee_update_view, name='employee_edit'),
]
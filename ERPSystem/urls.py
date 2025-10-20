"""
URL configuration for ERPSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # أضف include
from reports.views import dashboard_view # استيراد الدالة من تطبيق reports
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'), # عند الدخول للرابط الرئيسي، ستظهر هذه الصفحة
    # مسارات المصادقة (تسجيل الدخول، الخروج، تغيير كلمة المرور، الخ)
    path('accounts/', include('django.contrib.auth.urls')),
    # إضافة مسارات تطبيق الموظفين
    path('employees/', include('employees.urls')),
    # إضافة مسارات تطبيق المخازن
    path('products/', include('inventory.urls')), 
     # إضافة مسارات تطبيق المبيعات للعملاء
    path('customers/', include('sales.urls')),
    path('sales/', include('sales.urls')),
    path('reports/', include('reports.urls')),

]

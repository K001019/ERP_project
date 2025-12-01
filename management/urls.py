# management/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/edit/', views.user_update_view, name='user_edit'),
    path('users/<int:pk>/change-password/', views.change_user_password_view, name='change_user_password'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
    path('audit-trail/details/<str:model_name>/<int:pk>/<int:history_id>/', views.history_detail_view, name='history_detail'),
    path('permissions/', views.manage_permissions_view, name='manage_permissions'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/ask/', views.ask_gemini_view, name='ask_gemini'),
]
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard_view, name='dashboard'),
    path('users/', views.user_management_view, name='user_management'),
    path('jobs/', views.job_management_view, name='job_management'),
    path('analytics/', views.analytics_view, name='analytics'),
]

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('email-sent/<int:user_id>/', views.email_sent_view, name='email_sent'),
    path('verify-email/<int:user_id>/', views.verify_email_view, name='verify_email'),
    path('resend-code/<int:user_id>/', views.resend_verification_code, name='resend_code'),
    path('verification-success/<int:user_id>/', views.verification_success_view, name='verification_success'),
    path('verification-failed/', views.verification_failed_view, name='verification_failed'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
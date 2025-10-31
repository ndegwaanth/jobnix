from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.user_analytics_view, name='user_analytics'),
    path('platform/', views.platform_analytics_view, name='platform_analytics'),
    path('job-seeker/', views.job_seeker_stats_view, name='job_seeker_stats'),
]

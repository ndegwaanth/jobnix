from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('create/', views.job_create_view, name='job_create'),
    path('<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('<int:job_id>/apply/', views.job_apply_view, name='job_apply'),
]
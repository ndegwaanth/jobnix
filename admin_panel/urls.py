from django.urls import path
from . import views
from accounts import views as accounts_views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard_view, name='dashboard'),
    path('users/', views.user_management_view, name='user_management'),
    
    # Job management
    path('jobs/', views.job_management_view, name='job_management'),
    path('jobs/add/', views.job_add_view, name='job_add'),
    path('jobs/<int:job_id>/edit/', views.job_edit_view, name='job_edit'),
    path('jobs/<int:job_id>/delete/', views.job_delete_view, name='job_delete'),
    
    # Course management
    path('courses/', views.course_management_view, name='course_management'),
    path('courses/add/', views.course_add_view, name='course_add'),
    path('courses/<int:course_id>/edit/', views.course_edit_view, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete_view, name='course_delete'),
    
    # Instructor management
    path('instructors/', views.instructor_management_view, name='instructor_management'),
    path('instructors/add/', views.instructor_add_view, name='instructor_add'),
    path('instructors/<int:instructor_id>/edit/', views.instructor_edit_view, name='instructor_edit'),
    
    path('analytics/', views.analytics_view, name='analytics'),
    path('support-tickets/', views.support_tickets_view, name='support_tickets'),
    path('notifications/', views.system_notifications_view, name='system_notifications'),
    
    # Chat
    path('chat/employer/', accounts_views.employer_admin_chat_view, name='admin_employer_chat'),
]

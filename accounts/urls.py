from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('email-sent/<int:user_id>/', views.email_sent_view, name='email_sent'),
    path('verify-email/<int:user_id>/', views.verify_email_view, name='verify_email'),
    path('resend-code/<int:user_id>/', views.resend_verification_code, name='resend_code'),
    path('verification-success/<int:user_id>/', views.verification_success_view, name='verification_success'),
    path('verification-failed/', views.verification_failed_view, name='verification_failed'),
    
    # Dashboard & Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # Youth Dashboard Features
    path('resume-builder/', views.resume_builder_view, name='resume_builder'),
    path('applications/', views.applications_list_view, name='applications_list'),
    path('saved-jobs/', views.saved_jobs_view, name='saved_jobs'),
    path('saved-courses/', views.saved_courses_view, name='saved_courses'),
    path('certificates/', views.certificates_view, name='certificates'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('messages/', views.messages_view, name='messages'),
    path('analytics/', views.profile_analytics_view, name='profile_analytics'),
    
    # Chat
    path('chat/employer-admin/', views.employer_admin_chat_view, name='employer_admin_chat'),
    
    # Employer Dashboard Features
    path('company-profile/', views.company_profile_edit_view, name='company_profile'),
    path('job/post/', views.job_post_create_view, name='job_post_create'),
    path('job/manage/<int:job_id>/', views.job_manage_view, name='job_manage'),
    path('applicants/', views.applicants_view, name='applicants'),
    path('applicants/<int:job_id>/', views.applicants_view, name='applicants_job'),
    path('candidates/search/', views.candidate_search_view, name='candidate_search'),
    path('candidates/<int:candidate_id>/', views.candidate_profile_view, name='candidate_profile'),
    path('candidates/saved/', views.saved_candidates_view, name='saved_candidates'),
    path('interview/<int:application_id>/', views.interview_manage_view, name='interview_manage'),
    path('reports/', views.employer_reports_view, name='employer_reports'),
    path('update-theme/', views.update_theme_view, name='update_theme'),
]
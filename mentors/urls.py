from django.urls import path
from . import views

app_name = 'mentors'

urlpatterns = [
    path('', views.mentorship_list_view, name='mentorship_list'),
    path('mentor/<int:mentor_id>/', views.mentorship_detail_view, name='mentorship_detail'),
    path('my-mentorships/', views.my_mentorships_view, name='my_mentorships'),
    path('mentorship/<int:request_id>/', views.mentorship_detail_mentee_view, name='mentorship_detail_mentee'),
    path('mentorship/<int:request_id>/mentor/', views.mentorship_detail_mentor_view, name='mentorship_detail_mentor'),
    path('register/', views.mentor_register_view, name='mentor_register'),
    path('sessions/<int:request_id>/', views.mentor_sessions_view, name='mentor_sessions'),
]


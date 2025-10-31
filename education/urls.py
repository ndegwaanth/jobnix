from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.course_enroll_view, name='course_enroll'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('institutions/', views.institution_list_view, name='institution_list'),
]

from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.course_enroll_view, name='course_enroll'),
    path('courses/<int:course_id>/payment/', views.course_payment_view, name='course_payment'),
    path('courses/<int:course_id>/save/', views.save_course_view, name='save_course'),
    path('courses/<int:course_id>/learn/', views.course_learn_view, name='course_learn'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
]

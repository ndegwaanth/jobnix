from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Course, Enrollment, CourseModule, CourseContent, SavedCourse


def course_list_view(request):
    """List all available courses"""
    courses = Course.objects.filter(status='active', is_active=True).order_by('-created_at')
    
    # Filter by search
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(skills_taught__icontains=search_query)
        )
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        courses = courses.filter(category=category)
    
    # Filter by level
    level = request.GET.get('level', '')
    if level:
        courses = courses.filter(level=level)
    
    # Filter free courses
    free_only = request.GET.get('free', '')
    if free_only:
        courses = courses.filter(is_free=True)
    
    # Get saved courses for logged in users
    saved_course_ids = []
    if request.user.is_authenticated:
        saved_course_ids = SavedCourse.objects.filter(user=request.user).values_list('course_id', flat=True)
    
    context = {
        'courses': courses,
        'saved_course_ids': saved_course_ids,
        'search_query': search_query,
        'selected_category': category,
        'selected_level': level,
        'categories': Course.objects.filter(status='active').values_list('category', flat=True).distinct(),
        'levels': Course.LEVEL_CHOICES,
    }
    return render(request, 'education/course_list.html', context)


def course_detail_view(request, course_id):
    """Display course details"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Get course modules and contents
    modules = CourseModule.objects.filter(course=course).prefetch_related('contents')
    
    # Also get contents not in modules (direct course content)
    direct_contents = CourseContent.objects.filter(course=course, module__isnull=True)
    
    # Check if user is enrolled
    is_enrolled = False
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        is_enrolled = enrollment is not None
    
    # Check if saved
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedCourse.objects.filter(user=request.user, course=course).exists()
    
    # Increment views
    course.views_count += 1
    course.save(update_fields=['views_count'])
    
    context = {
        'course': course,
        'modules': modules,
        'direct_contents': direct_contents,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'is_saved': is_saved,
    }
    return render(request, 'education/course_detail.html', context)


@login_required
def course_enroll_view(request, course_id):
    """Enroll in a course"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    if request.method == 'POST':
        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'status': 'enrolled'}
        )
        
        if created:
            messages.success(request, f'Successfully enrolled in {course.title}')
            # Create notification
            from accounts.models import Notification
            Notification.objects.create(
                user=request.user,
                notification_type='course_enrollment',
                title='Course Enrollment',
                message=f'You have successfully enrolled in {course.title}',
                link=f'/education/courses/{course.id}/'
            )
        else:
            messages.info(request, 'You are already enrolled in this course')
        
        return redirect('education:course_detail', course_id=course_id)
    
    context = {'course': course}
    return render(request, 'education/course_enroll.html', context)


@login_required
def save_course_view(request, course_id):
    """Save/unsave a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        saved_course, created = SavedCourse.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if not created:
            saved_course.delete()
            messages.success(request, 'Course removed from saved')
        else:
            messages.success(request, 'Course saved')
    
    return redirect('education:course_detail', course_id=course_id)


@login_required
def my_courses_view(request):
    """View user's enrolled courses"""
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course').order_by('-enrolled_at')
    
    # Calculate stats
    total_enrolled = enrollments.count()
    in_progress = enrollments.filter(status='in_progress').count()
    completed = enrollments.filter(status='completed').count()
    
    context = {
        'enrollments': enrollments,
        'stats': {
            'total': total_enrolled,
            'in_progress': in_progress,
            'completed': completed,
        }
    }
    return render(request, 'education/my_courses.html', context)

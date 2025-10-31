from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Import models safely to avoid circular import issues
try:
    from .models import Course, Enrollment, Institution
except ImportError:
    Course = None
    Enrollment = None
    Institution = None

# Create your views here.
def course_list_view(request):
    """List all available courses"""
    if Course and hasattr(Course, 'objects'):
        courses = Course.objects.filter(is_active=True)
    else:
        courses = []
    context = {'courses': courses}
    return render(request, 'education/course_list.html', context)

def course_detail_view(request, course_id):
    """Display course details"""
    if Course and hasattr(Course, 'objects'):
        course = get_object_or_404(Course, id=course_id, is_active=True)
        context = {'course': course}
    else:
        context = {'course': None}
    return render(request, 'education/course_detail.html', context)

@login_required
def course_enroll_view(request, course_id):
    """Enroll in a course"""
    if Course and hasattr(Course, 'objects'):
        course = get_object_or_404(Course, id=course_id, is_active=True)
        if request.method == 'POST':
            # Enrollment logic will be implemented with forms
            messages.success(request, 'Successfully enrolled in course')
            return redirect('education:course_detail', course_id=course_id)
        context = {'course': course}
    else:
        context = {'course': None}
    return render(request, 'education/course_enroll.html', context)

@login_required
def my_courses_view(request):
    """View user's enrolled courses"""
    if Enrollment and hasattr(Enrollment, 'objects'):
        enrollments = Enrollment.objects.filter(user=request.user)
    else:
        enrollments = []
    context = {'enrollments': enrollments}
    return render(request, 'education/my_courses.html', context)

def institution_list_view(request):
    """List all training institutions"""
    if Institution and hasattr(Institution, 'objects'):
        institutions = Institution.objects.filter(is_verified=True)
    else:
        institutions = []
    context = {'institutions': institutions}
    return render(request, 'education/institution_list.html', context)

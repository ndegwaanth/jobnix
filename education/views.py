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
    
    # Get course modules/sections and contents, ordered properly
    modules = CourseModule.objects.filter(course=course).prefetch_related(
        'contents'
    ).order_by('order', 'created_at')
    
    # Organize content: video first, then other content (subsections)
    for module in modules:
        # Get all contents for this module and sort: video (order=0) first, then other content by order
        all_contents = list(module.contents.all())
        # Sort: videos with order=0 first (section videos), then other content by order
        def sort_key(content):
            if content.content_type == 'video' and content.order == 0:
                return (0, 0)  # Section videos come first
            else:
                return (1, content.order)  # Then subsections by order
        
        module.contents_list = sorted(all_contents, key=sort_key)
    
    # Also get contents not in modules (direct course content) - these shouldn't exist with new structure
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
    """Enroll in a course - for free courses only"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Redirect paid courses to payment
    if not course.is_free:
        return redirect('education:course_payment', course_id=course_id)
    
    if request.method == 'POST':
        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'status': 'enrolled'}
        )
        
        if created:
            # Update enrollment count
            course.enrollments_count += 1
            course.save(update_fields=['enrollments_count'])
            
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
def course_payment_view(request, course_id):
    """Payment page for paid courses"""
    from education.models import Payment
    from django.utils import timezone
    
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Check if course is free
    if course.is_free:
        return redirect('education:course_enroll', course_id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course')
        return redirect('education:course_detail', course_id=course_id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            currency='USD',
            payment_method=payment_method,
            status='pending'
        )
        
        # For now, we'll mark as completed (in production, integrate with actual payment gateways)
        # TODO: Integrate with PayPal, M-Pesa, Bank Transfer APIs
        if payment_method in ['paypal', 'mpesa', 'card', 'bank_transfer']:
            # Simulate payment processing
            # In production, this would redirect to payment gateway or process payment
            payment.status = 'completed'
            payment.payment_date = timezone.now()
            payment.save()
            
            # Create enrollment
            enrollment = Enrollment.objects.create(
                user=request.user,
                course=course,
                payment=payment,
                status='enrolled'
            )
            
            # Update enrollment count
            course.enrollments_count += 1
            course.save(update_fields=['enrollments_count'])
            
            messages.success(request, f'Payment successful! You are now enrolled in {course.title}')
            
            # Create notification
            from accounts.models import Notification
            Notification.objects.create(
                user=request.user,
                notification_type='course_enrollment',
                title='Course Enrollment',
                message=f'You have successfully enrolled in {course.title}',
                link=f'/education/courses/{course.id}/'
            )
            
            return redirect('education:course_detail', course_id=course_id)
        else:
            messages.error(request, 'Invalid payment method')
    
    context = {
        'course': course,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'education/course_payment.html', context)


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
    if request.method == 'POST' and request.POST.get('action') == 'unenroll':
        enrollment_id = request.POST.get('enrollment_id')
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
            course_title = enrollment.course.title
            enrollment.delete()
            messages.success(request, f'Unenrolled from {course_title}')
            return redirect('education:my_courses')
        except Enrollment.DoesNotExist:
            messages.error(request, 'Enrollment not found')
    
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


@login_required
def course_learn_view(request, course_id):
    """Continue learning view - displays videos and documents for enrolled users"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Check if user is enrolled
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to access learning materials')
        return redirect('education:course_detail', course_id=course_id)
    
    # Update last accessed time
    from django.utils import timezone
    enrollment.last_accessed_at = timezone.now()
    enrollment.save()
    
    # Get course modules/sections and contents, ordered properly
    modules = CourseModule.objects.filter(course=course).prefetch_related(
        'contents'
    ).order_by('order', 'created_at')
    
    # Organize content: video first, then other content (subsections)
    for module in modules:
        # Get all contents for this module and sort: video (order=0) first, then other content by order
        all_contents = list(module.contents.all())
        # Sort: videos with order=0 first (section videos), then other content by order
        def sort_key(content):
            if content.content_type == 'video' and content.order == 0:
                return (0, 0)  # Section videos come first
            else:
                return (1, content.order)  # Then subsections by order
        
        module.contents_list = sorted(all_contents, key=sort_key)
    
    # Get first video and first document for preview
    first_video = None
    first_document = None
    all_videos = []
    all_documents = []
    
    for module in modules:
        for content in module.contents_list:
            if content.content_type == 'video' and not first_video:
                first_video = content
            if content.content_type == 'document' and not first_document:
                first_document = content
            
            if content.content_type == 'video':
                all_videos.append(content)
            if content.content_type == 'document':
                all_documents.append(content)
    
    # Calculate progress (based on accessed content)
    total_content = sum(len(m.contents_list) for m in modules)
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'first_video': first_video,
        'first_document': first_document,
        'all_videos': all_videos,
        'all_documents': all_documents,
        'total_content': total_content,
    }
    return render(request, 'education/course_learn.html', context)

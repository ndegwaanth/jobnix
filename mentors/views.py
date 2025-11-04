from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Mentor, MentorshipRequest, MentorshipSession, MentorshipGoal, MentorshipResource
from accounts.models import User


@login_required
def mentorship_list_view(request):
    """View all available mentors"""
    if request.user.role != 'youth':
        messages.error(request, 'Only youth/job seekers can browse mentors.')
        return redirect('accounts:dashboard')
    
    # Get active mentors
    mentors = Mentor.objects.filter(status='active', is_verified=True).select_related('user')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        mentors = mentors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(expertise_areas__icontains=search_query) |
            Q(industry__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Filter by expertise
    expertise = request.GET.get('expertise', '')
    if expertise:
        mentors = mentors.filter(expertise_areas__icontains=expertise)
    
    # Calculate match scores (simple AI matching based on skills/interests)
    mentee_skills = []
    if hasattr(request.user, 'youth_profile') and request.user.youth_profile:
        mentee_skills = request.user.youth_profile.skills.split(',') if request.user.youth_profile.skills else []
    
    mentor_list = []
    for mentor in mentors:
        # Simple matching algorithm
        mentor_expertise = [e.strip().lower() for e in mentor.expertise_areas.split(',') if e.strip()]
        mentee_skills_lower = [s.strip().lower() for s in mentee_skills if s.strip()]
        
        match_score = 0
        if mentee_skills_lower:
            matches = sum(1 for skill in mentee_skills_lower if any(skill in exp or exp in skill for exp in mentor_expertise))
            match_score = (matches / len(mentee_skills_lower)) * 100 if mentee_skills_lower else 0
        
        mentor_list.append({
            'mentor': mentor,
            'match_score': round(match_score, 1),
            'has_active_request': MentorshipRequest.objects.filter(
                mentee=request.user, mentor=mentor, status__in=['pending', 'accepted']
            ).exists()
        })
    
    # Sort by match score
    mentor_list.sort(key=lambda x: x['match_score'], reverse=True)
    
    context = {
        'mentors': mentor_list,
        'search_query': search_query,
        'expertise': expertise,
    }
    return render(request, 'mentors/mentorship_list.html', context)


@login_required
def mentorship_detail_view(request, mentor_id):
    """View mentor details and request mentorship"""
    if request.user.role != 'youth':
        messages.error(request, 'Only youth/job seekers can request mentorship.')
        return redirect('accounts:dashboard')
    
    mentor = get_object_or_404(Mentor, id=mentor_id, status='active')
    
    # Check if already has active request
    existing_request = MentorshipRequest.objects.filter(
        mentee=request.user, mentor=mentor, status__in=['pending', 'accepted']
    ).first()
    
    # Get mentor stats
    total_sessions = MentorshipSession.objects.filter(mentorship__mentor=mentor).count()
    completed_sessions = MentorshipSession.objects.filter(mentorship__mentor=mentor, status='completed').count()
    active_mentees = MentorshipRequest.objects.filter(mentor=mentor, status='accepted').count()
    
    # Calculate match score
    mentee_skills = []
    if hasattr(request.user, 'youth_profile') and request.user.youth_profile:
        mentee_skills = request.user.youth_profile.skills.split(',') if request.user.youth_profile.skills else []
    
    mentor_expertise = [e.strip().lower() for e in mentor.expertise_areas.split(',') if e.strip()]
    mentee_skills_lower = [s.strip().lower() for s in mentee_skills if s.strip()]
    
    match_score = 0
    if mentee_skills_lower:
        matches = sum(1 for skill in mentee_skills_lower if any(skill in exp or exp in skill for exp in mentor_expertise))
        match_score = (matches / len(mentee_skills_lower)) * 100 if mentee_skills_lower else 0
    
    # Request mentorship
    if request.method == 'POST' and not existing_request:
        message = request.POST.get('message', '').strip()
        goals = request.POST.get('goals', '').strip()
        
        if message and goals:
            mentorship_request = MentorshipRequest.objects.create(
                mentee=request.user,
                mentor=mentor,
                message=message,
                goals=goals,
                match_score=match_score
            )
            messages.success(request, 'Mentorship request sent successfully!')
            return redirect('mentors:my_mentorships')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'mentor': mentor,
        'existing_request': existing_request,
        'match_score': round(match_score, 1),
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'active_mentees': active_mentees,
    }
    return render(request, 'mentors/mentorship_detail.html', context)


@login_required
def my_mentorships_view(request):
    """View user's mentorship requests and active mentorships"""
    if request.user.role == 'youth':
        # Mentee view
        mentorship_requests = MentorshipRequest.objects.filter(mentee=request.user).select_related('mentor', 'mentor__user').order_by('-created_at')
        
        context = {
            'mentorship_requests': mentorship_requests,
            'active_mentorships': mentorship_requests.filter(status='accepted'),
            'pending_requests': mentorship_requests.filter(status='pending'),
        }
        return render(request, 'mentors/my_mentorships_youth.html', context)
    
    elif request.user.role in ['employer', 'institution']:
        # Mentor view
        try:
            mentor_profile = request.user.mentor_profile
            mentorship_requests = MentorshipRequest.objects.filter(mentor=mentor_profile).select_related('mentee').order_by('-created_at')
            
            # Handle request actions
            if request.method == 'POST':
                request_id = request.POST.get('request_id')
                action = request.POST.get('action')
                
                if request_id and action:
                    mentorship_req = get_object_or_404(MentorshipRequest, id=request_id, mentor=mentor_profile)
                    
                    if action == 'accept':
                        mentorship_req.status = 'accepted'
                        mentorship_req.responded_at = timezone.now()
                        mentorship_req.save()
                        mentor_profile.total_mentees += 1
                        mentor_profile.save()
                        messages.success(request, 'Mentorship request accepted!')
                    elif action == 'reject':
                        mentorship_req.status = 'rejected'
                        mentorship_req.responded_at = timezone.now()
                        mentorship_req.save()
                        messages.success(request, 'Mentorship request rejected.')
                    
                    return redirect('mentors:my_mentorships')
            
            context = {
                'mentor_profile': mentor_profile,
                'mentorship_requests': mentorship_requests,
                'pending_requests': mentorship_requests.filter(status='pending'),
                'active_mentorships': mentorship_requests.filter(status='accepted'),
            }
            return render(request, 'mentors/my_mentorships_mentor.html', context)
        except Mentor.DoesNotExist:
            messages.info(request, 'You need to register as a mentor first.')
            return redirect('mentors:mentor_register')
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')


@login_required
def mentorship_detail_mentee_view(request, request_id):
    """View mentorship details for mentee"""
    if request.user.role != 'youth':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    mentorship = get_object_or_404(MentorshipRequest, id=request_id, mentee=request.user)
    sessions = MentorshipSession.objects.filter(mentorship=mentorship).order_by('-scheduled_at')
    goals = MentorshipGoal.objects.filter(mentorship=mentorship).order_by('-created_at')
    resources = MentorshipResource.objects.filter(mentorship=mentorship).order_by('-created_at')
    
    context = {
        'mentorship': mentorship,
        'sessions': sessions,
        'goals': goals,
        'resources': resources,
    }
    return render(request, 'mentors/mentorship_detail_mentee.html', context)


@login_required
def mentorship_detail_mentor_view(request, request_id):
    """View mentorship details for mentor"""
    try:
        mentor_profile = request.user.mentor_profile
        mentorship = get_object_or_404(MentorshipRequest, id=request_id, mentor=mentor_profile)
        sessions = MentorshipSession.objects.filter(mentorship=mentorship).order_by('-scheduled_at')
        goals = MentorshipGoal.objects.filter(mentorship=mentorship).order_by('-created_at')
        
        # Handle session creation
        if request.method == 'POST' and 'create_session' in request.POST:
            scheduled_at = request.POST.get('scheduled_at')
            duration = request.POST.get('duration_minutes', 60)
            meeting_link = request.POST.get('meeting_link', '')
            meeting_type = request.POST.get('meeting_type', 'video')
            agenda = request.POST.get('agenda', '')
            
            if scheduled_at:
                try:
                    scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('T', ' '))
                    MentorshipSession.objects.create(
                        mentorship=mentorship,
                        scheduled_at=scheduled_datetime,
                        duration_minutes=int(duration),
                        meeting_link=meeting_link,
                        meeting_type=meeting_type,
                        agenda=agenda
                    )
                    messages.success(request, 'Session scheduled successfully!')
                    return redirect('mentors:mentorship_detail_mentor', request_id=request_id)
                except Exception as e:
                    messages.error(request, f'Error creating session: {str(e)}')
        
        # Handle resource sharing
        if request.method == 'POST' and 'share_resource' in request.POST:
            resource_type = request.POST.get('resource_type', 'link')
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            url = request.POST.get('url', '')
            file = request.FILES.get('file')
            
            if title and (url or file):
                MentorshipResource.objects.create(
                    mentorship=mentorship,
                    resource_type=resource_type,
                    title=title,
                    description=description,
                    url=url,
                    file=file
                )
                messages.success(request, 'Resource shared successfully!')
                return redirect('mentors:mentorship_detail_mentor', request_id=request_id)
        
        context = {
            'mentorship': mentorship,
            'sessions': sessions,
            'goals': goals,
        }
        return render(request, 'mentors/mentorship_detail_mentor.html', context)
    except Mentor.DoesNotExist:
        messages.error(request, 'You are not registered as a mentor.')
        return redirect('accounts:dashboard')


@login_required
def mentor_register_view(request):
    """Register as a mentor"""
    if request.user.role not in ['employer', 'institution']:
        messages.error(request, 'Only employers and institutions can register as mentors.')
        return redirect('accounts:dashboard')
    
    # Check if already registered
    if hasattr(request.user, 'mentor_profile'):
        messages.info(request, 'You are already registered as a mentor.')
        return redirect('mentors:my_mentorships')
    
    if request.method == 'POST':
        bio = request.POST.get('bio', '').strip()
        expertise_areas = request.POST.get('expertise_areas', '').strip()
        years_of_experience = request.POST.get('years_of_experience', 0)
        current_position = request.POST.get('current_position', '').strip()
        company = request.POST.get('company', '').strip()
        industry = request.POST.get('industry', '').strip()
        languages = request.POST.get('languages', 'English').strip()
        availability_hours = request.POST.get('availability_hours', '').strip()
        max_mentees = request.POST.get('max_mentees', 10)
        hourly_rate = request.POST.get('hourly_rate', 0)
        
        if bio and expertise_areas:
            mentor = Mentor.objects.create(
                user=request.user,
                bio=bio,
                expertise_areas=expertise_areas,
                years_of_experience=int(years_of_experience) if years_of_experience else 0,
                current_position=current_position,
                company=company,
                industry=industry,
                languages=languages,
                availability_hours=availability_hours,
                max_mentees=int(max_mentees) if max_mentees else 10,
                hourly_rate=float(hourly_rate) if hourly_rate else 0.00,
                status='pending'
            )
            messages.success(request, 'Mentor registration submitted! Waiting for admin approval.')
            return redirect('mentors:my_mentorships')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'mentors/mentor_register.html')


@login_required
def mentor_sessions_view(request, request_id):
    """View and manage mentorship sessions"""
    try:
        mentor_profile = request.user.mentor_profile
        mentorship = get_object_or_404(MentorshipRequest, id=request_id, mentor=mentor_profile)
    except Mentor.DoesNotExist:
        if request.user.role == 'youth':
            mentorship = get_object_or_404(MentorshipRequest, id=request_id, mentee=request.user)
        else:
            messages.error(request, 'Access denied.')
            return redirect('accounts:dashboard')
    
    sessions = MentorshipSession.objects.filter(mentorship=mentorship).order_by('-scheduled_at')
    
    context = {
        'mentorship': mentorship,
        'sessions': sessions,
    }
    return render(request, 'mentors/mentor_sessions.html', context)

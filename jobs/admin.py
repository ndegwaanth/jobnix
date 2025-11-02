from django.contrib import admin
from .models import Job, Application, SavedJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'location', 'work_type', 'status', 'date_posted', 'is_active', 'views_count')
    list_filter = ('status', 'work_type', 'experience_level', 'is_active', 'is_featured', 'date_posted')
    search_fields = ('job_title', 'company_name', 'location', 'job_description', 'job_id')
    readonly_fields = ('job_id', 'date_posted', 'created_at', 'updated_at', 'views_count', 'applications_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_title', 'company_name', 'company', 'location', 'is_remote', 'work_type')
        }),
        ('Job Details', {
            'fields': ('job_description', 'qualifications', 'skills_required', 'experience_level', 'years_of_experience')
        }),
        ('Compensation', {
            'fields': ('salary_range_min', 'salary_range_max', 'salary_currency', 'salary_display')
        }),
        ('Application', {
            'fields': ('application_deadline', 'application_link', 'application_instructions')
        }),
        ('Tracking', {
            'fields': ('job_id', 'source', 'status', 'is_active', 'is_featured')
        }),
        ('Analytics', {
            'fields': ('views_count', 'applications_count')
        }),
        ('Metadata', {
            'fields': ('approved_by', 'approved_at', 'date_posted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'match_score', 'applied_at')
    list_filter = ('status', 'applied_at', 'match_score')
    search_fields = ('applicant__username', 'applicant__email', 'job__job_title', 'job__company_name')
    readonly_fields = ('applied_at', 'updated_at', 'reviewed_at')
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'applicant', 'status', 'match_score')
        }),
        ('Documents', {
            'fields': ('cover_letter', 'resume')
        }),
        ('Notes', {
            'fields': ('applicant_notes', 'employer_notes')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at', 'reviewed_at')
        }),
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'job__job_title')

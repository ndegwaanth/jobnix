from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Enrollment, Certificate, SavedCourse, CourseModule, CourseContent


class CourseContentInline(admin.TabularInline):
    """Inline admin for course content"""
    model = CourseContent
    extra = 1
    fields = ('content_type', 'title', 'video_url', 'video_file', 'document_file', 'document_url', 'external_link', 'order', 'is_free_preview')
    verbose_name = "Content Item"
    verbose_name_plural = "Course Content"


class CourseModuleInline(admin.TabularInline):
    """Inline admin for course modules"""
    model = CourseModule
    extra = 1
    fields = ('title', 'description', 'order')
    verbose_name = "Module"
    verbose_name_plural = "Course Modules"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model"""
    list_display = ('title', 'institution', 'category', 'level', 'status', 'is_free', 'enrollments_count', 'views_count', 'created_at')
    list_filter = ('status', 'level', 'is_free', 'category', 'created_at')
    search_fields = ('title', 'description', 'category', 'skills_taught')
    readonly_fields = ('enrollments_count', 'completion_count', 'views_count', 'created_at', 'updated_at', 'approved_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'institution', 'instructor')
        }),
        ('Course Details', {
            'fields': ('category', 'skills_taught', 'level', 'duration_hours', 'price', 'is_free')
        }),
        ('Media', {
            'fields': ('thumbnail', 'video_intro_url')
        }),
        ('Status & Dates', {
            'fields': ('status', 'is_active', 'start_date', 'end_date', 'approved_by', 'approved_at')
        }),
        ('Analytics', {
            'fields': ('enrollments_count', 'completion_count', 'views_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [CourseModuleInline]
    
    def save_model(self, request, obj, form, change):
        """Auto-approve courses created by admin/staff"""
        if not change and not obj.approved_by:  # New course
            if request.user.is_staff:
                obj.status = 'active'
                obj.approved_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    """Admin interface for CourseModule"""
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'course__title', 'description')
    ordering = ('course', 'order')
    inlines = [CourseContentInline]


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    """Admin interface for CourseContent with rich editing"""
    list_display = ('title', 'course', 'module', 'content_type', 'order', 'is_free_preview', 'created_at')
    list_filter = ('content_type', 'is_free_preview', 'course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'module', 'order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'module', 'content_type', 'title', 'description', 'order')
        }),
        ('Video Content', {
            'fields': ('video_url', 'video_file', 'video_duration'),
            'classes': ('collapse',)
        }),
        ('Document Content', {
            'fields': ('document_file', 'document_url'),
            'classes': ('collapse',)
        }),
        ('Link Content', {
            'fields': ('external_link', 'link_title'),
            'classes': ('collapse',)
        }),
        ('Text Content', {
            'fields': ('text_content',),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_free_preview', 'duration_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on content type"""
        form = super().get_form(request, obj, **kwargs)
        # You can add custom JavaScript here to show/hide fields based on content_type
        return form


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment"""
    list_display = ('user', 'course', 'status', 'progress_percentage', 'enrolled_at', 'last_accessed_at')
    list_filter = ('status', 'course', 'enrolled_at')
    search_fields = ('user__username', 'user__email', 'course__title')
    readonly_fields = ('enrolled_at', 'updated_at')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface for Certificate"""
    list_display = ('user', 'course', 'certificate_number', 'issued_at')
    list_filter = ('course', 'issued_at')
    search_fields = ('user__username', 'course__title', 'certificate_number')
    readonly_fields = ('certificate_number', 'issued_at')


@admin.register(SavedCourse)
class SavedCourseAdmin(admin.ModelAdmin):
    """Admin interface for SavedCourse"""
    list_display = ('user', 'course', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'course__title')

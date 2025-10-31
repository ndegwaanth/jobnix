from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification, JobSeekerProfile, EmployerProfile, InstitutionProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'is_verified')}),
    )


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'is_verified', 'created_at', 'expires_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('email', 'code')
    readonly_fields = ('created_at', 'verified_at')


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'education_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'skills')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'industry', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'industry', 'created_at')
    search_fields = ('company_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InstitutionProfile)
class InstitutionProfileAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'user', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('institution_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

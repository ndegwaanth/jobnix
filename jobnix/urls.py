"""
URL configuration for jobnix project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Landing page (root URL)
    path('', accounts_views.landing_view, name='landing'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('education/', include('education.urls')),
    path('analytics/', include('analytics.urls')),
    path('admin_panel/', include('admin_panel.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

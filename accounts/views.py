from django.shortcuts import render

# Create your views here.
def landing_view(request):
    return render(request, 'accounts/landing.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def logout_view(request):
    return render(request, 'accounts/logout.html')

def register_view(request):
    return render(request, 'accounts/register.html')

def profile_view(request):
    return render(request, 'accounts/profile.html')

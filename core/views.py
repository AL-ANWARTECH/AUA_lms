from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    """User dashboard view"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/dashboard.html', context)
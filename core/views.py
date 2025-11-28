from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            login(request, user)  # Automatically log in the user after registration
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard view"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/dashboard.html', context)
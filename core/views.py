from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from .models import Course, Category, Module, Enrollment

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    
    def get_success_url(self):
        """Redirect based on user role after successful login"""
        user = self.request.user
        if user.role == 'student':
            return reverse_lazy('student_dashboard')
        elif user.role == 'instructor':
            return reverse_lazy('instructor_dashboard')
        elif user.role == 'admin':
            return reverse_lazy('admin_dashboard')
        else:
            return reverse_lazy('dashboard')  # fallback

def home(request):
    """Home page view"""
    # Get 3 most recent courses for the home page
    recent_courses = Course.objects.filter(is_active=True)[:3]
    context = {
        'recent_courses': recent_courses
    }
    return render(request, 'core/home.html', context)

def course_list(request):
    """Public course listing page"""
    courses = Course.objects.filter(is_active=True).select_related('instructor', 'category')
    
    # Add search functionality
    query = request.GET.get('q')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(instructor__username__icontains=query)
        )
    
    # Add category filter
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    # Get all categories for the filter dropdown
    categories = Category.objects.all()
    
    context = {
        'courses': courses,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id else None
    }
    return render(request, 'core/course_list.html', context)

def course_detail(request, pk):
    """Course detail page with modules and lessons"""
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated and request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    # Get course modules and lessons
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled
    }
    return render(request, 'core/course_detail.html', context)

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
    """Generic dashboard view"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def student_dashboard(request):
    """Student-specific dashboard"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    """Instructor-specific dashboard"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/instructor_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin-specific dashboard"""
    context = {
        'user_role': request.user.role,
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def create_course(request):
    """Allow instructors to create a new course"""
    if request.user.role != 'instructor':
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .course_forms import CourseForm
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save()
            return redirect('course_detail', pk=course.pk)
    else:
        from .course_forms import CourseForm
        form = CourseForm(user=request.user)
    
    return render(request, 'core/create_course.html', {'form': form})

@login_required
def create_module(request, course_pk):
    """Allow instructors to create a module for a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .course_forms import ModuleForm
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            return redirect('course_detail', pk=course.pk)
    else:
        from .course_forms import ModuleForm
        form = ModuleForm()
    
    return render(request, 'core/create_module.html', {
        'form': form,
        'course': course
    })

@login_required
def create_lesson(request, module_pk):
    """Allow instructors to create a lesson for a module"""
    module = get_object_or_404(Module, pk=module_pk)
    
    if request.user.role != 'instructor' or module.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .course_forms import LessonForm
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            return redirect('course_detail', pk=module.course.pk)
    else:
        from .course_forms import LessonForm
        form = LessonForm()
    
    return render(request, 'core/create_lesson.html', {
        'form': form,
        'module': module
    })

def logout_view(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
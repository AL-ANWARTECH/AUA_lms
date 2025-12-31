from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from .models import Course, Category, Module, Enrollment, Lesson, Quiz, Question, AnswerOption, QuizAttempt, QuizAnswer

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
    enrollment = None
    completed_lessons = []
    
    if request.user.is_authenticated and request.user.role == 'student':
        enrollment_obj = Enrollment.objects.filter(student=request.user, course=course).first()
        is_enrolled = enrollment_obj is not None
        if is_enrolled:
            enrollment = enrollment_obj
            completed_lessons = list(enrollment.completed_lessons.values_list('pk', flat=True))
    
    # Get course modules and lessons
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'completed_lessons': completed_lessons
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
    """Student-specific dashboard with enrolled courses"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Get courses the student is enrolled in
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course__instructor', 'course__category')
    
    context = {
        'user_role': request.user.role,
        'enrollments': enrollments
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    """Instructor-specific dashboard with course management"""
    if request.user.role != 'instructor':
        return redirect('dashboard')
    
    # Get courses created by this instructor
    courses = Course.objects.filter(instructor=request.user).select_related('category').prefetch_related('modules')
    
    context = {
        'user_role': request.user.role,
        'courses': courses
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

@login_required
def enroll_course(request, pk):
    """Allow students to enroll in a course"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    # Check if already enrolled
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )
    
    if created:
        messages.success(request, f'You have successfully enrolled in {course.title}!')
    else:
        messages.info(request, f'You are already enrolled in {course.title}.')
    
    return redirect('course_detail', pk=pk)

@login_required
def unenroll_course(request, pk):
    """Allow students to unenroll from a course"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.delete()
        messages.success(request, f'You have successfully unenrolled from {course.title}.')
    except Enrollment.DoesNotExist:
        messages.warning(request, f'You were not enrolled in {course.title}.')
    
    return redirect('student_dashboard')

@login_required
def lesson_detail(request, pk):
    """Lesson detail page with completion tracking"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to access this lesson.")
        return redirect('course_detail', pk=course.pk)
    
    # Check if lesson is already completed
    is_completed = enrollment.completed_lessons.filter(pk=pk).exists()
    
    context = {
        'lesson': lesson,
        'course': course,
        'is_completed': is_completed,
        'enrollment': enrollment
    }
    return render(request, 'core/lesson_detail.html', context)

@login_required
def complete_lesson(request, pk):
    """Mark a lesson as completed"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to complete lessons.")
        return redirect('course_detail', pk=course.pk)
    
    # Add lesson to completed lessons
    enrollment.completed_lessons.add(lesson)
    messages.success(request, f'Lesson "{lesson.title}" marked as completed!')
    
    # Redirect to next lesson or back to course
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__gt=lesson.order
    ).order_by('order').first()
    
    if next_lesson:
        return redirect('lesson_detail', pk=next_lesson.pk)
    else:
        # Check for next module
        next_module = Module.objects.filter(
            course=course,
            order__gt=lesson.module.order
        ).order_by('order').first()
        
        if next_module:
            next_lesson = next_module.lessons.order_by('order').first()
            if next_lesson:
                return redirect('lesson_detail', pk=next_lesson.pk)
    
    # If no next lesson/module, go back to course
    return redirect('course_detail', pk=course.pk)

@login_required
def uncomplete_lesson(request, pk):
    """Mark a lesson as not completed"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to modify lesson completion.")
        return redirect('course_detail', pk=course.pk)
    
    # Remove lesson from completed lessons
    enrollment.completed_lessons.remove(lesson)
    messages.success(request, f'Lesson "{lesson.title}" marked as incomplete.')
    
    return redirect('lesson_detail', pk=pk)

@login_required
def create_quiz(request, lesson_pk):
    """Create a quiz for a lesson"""
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    
    if request.user.role != 'instructor' or lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .quiz_forms import QuizForm
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created successfully!')
            return redirect('manage_quiz', pk=quiz.pk)
    else:
        from .quiz_forms import QuizForm
        form = QuizForm()
    
    return render(request, 'core/create_quiz.html', {
        'form': form,
        'lesson': lesson
    })

@login_required
def manage_quiz(request, pk):
    """Manage quiz questions"""
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.user.role != 'instructor' or quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    questions = quiz.questions.all()
    
    context = {
        'quiz': quiz,
        'questions': questions
    }
    return render(request, 'core/manage_quiz.html', context)

@login_required
def create_question(request, quiz_pk):
    """Create a question for a quiz"""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    
    if request.user.role != 'instructor' or quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .quiz_forms import QuestionForm
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            return redirect('edit_question', pk=question.pk)
    else:
        from .quiz_forms import QuestionForm
        form = QuestionForm()
    
    return render(request, 'core/create_question.html', {
        'form': form,
        'quiz': quiz
    })

@login_required
def edit_question(request, pk):
    """Edit a question and its answer options"""
    question = get_object_or_404(Question, pk=pk)
    
    if request.user.role != 'instructor' or question.quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .quiz_forms import QuestionForm, AnswerOptionFormSet
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerOptionFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Question updated successfully!")
            return redirect('manage_quiz', pk=question.quiz.pk)
    else:
        from .quiz_forms import QuestionForm, AnswerOptionFormSet
        form = QuestionForm(instance=question)
        formset = AnswerOptionFormSet(instance=question)
    
    return render(request, 'core/edit_question.html', {
        'form': form,
        'formset': formset,
        'question': question
    })

@login_required
def take_quiz(request, quiz_pk):
    """Take a quiz"""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    lesson = quiz.lesson
    course = lesson.module.course
    
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to take this quiz.")
        return redirect('course_detail', pk=course.pk)
    
    # Check if user can take the quiz
    attempt_count = QuizAttempt.objects.filter(
        quiz=quiz, 
        student=request.user
    ).count()
    
    if attempt_count >= quiz.max_attempts:
        messages.error(request, "You have reached the maximum number of attempts for this quiz.")
        return redirect('lesson_detail', pk=lesson.pk)
    
    questions = quiz.questions.all().prefetch_related('answer_options')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'lesson': lesson
    }
    return render(request, 'core/take_quiz.html', context)

@login_required
def submit_quiz(request, quiz_pk):
    """Submit quiz answers and calculate score"""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    lesson = quiz.lesson
    course = lesson.module.course
    
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return redirect('course_detail', pk=course.pk)
    
    # Check if user can take the quiz
    attempt_count = QuizAttempt.objects.filter(
        quiz=quiz, 
        student=request.user
    ).count()
    
    if attempt_count >= quiz.max_attempts:
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        # Create quiz attempt
        attempt_number = attempt_count + 1
        quiz_attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            attempt_number=attempt_number,
            score=0  # Will calculate after processing answers
        )
        
        # Process answers
        score = 0
        total_points = 0
        
        for question in quiz.questions.all():
            total_points += question.points
            
            if question.question_type == 'multiple_choice':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        answer_option = AnswerOption.objects.get(
                            id=answer_id, 
                            question=question
                        )
                        is_correct = answer_option.is_correct
                        QuizAnswer.objects.create(
                            quiz_attempt=quiz_attempt,
                            question=question,
                            selected_option=answer_option,
                            is_correct=is_correct
                        )
                        if is_correct:
                            score += question.points
                    except AnswerOption.DoesNotExist:
                        pass
            elif question.question_type == 'true_false':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        answer_option = AnswerOption.objects.get(
                            id=answer_id, 
                            question=question
                        )
                        is_correct = answer_option.is_correct
                        QuizAnswer.objects.create(
                            quiz_attempt=quiz_attempt,
                            question=question,
                            selected_option=answer_option,
                            is_correct=is_correct
                        )
                        if is_correct:
                            score += question.points
                    except AnswerOption.DoesNotExist:
                        pass
            elif question.question_type == 'short_answer':
                text_answer = request.POST.get(f'question_{question.id}')
                if text_answer:
                    # For now, we'll mark all short answers as incorrect
                    # In a real system, you'd need to implement answer matching
                    is_correct = False
                    QuizAnswer.objects.create(
                        quiz_attempt=quiz_attempt,
                        question=question,
                        text_answer=text_answer,
                        is_correct=is_correct
                    )
        
        # Calculate final score percentage
        if total_points > 0:
            quiz_attempt.score = (score / total_points) * 100
        else:
            quiz_attempt.score = 0
        quiz_attempt.save()
        
        # Check if passed
        if quiz_attempt.score >= quiz.passing_score:
            messages.success(
                request, 
                f"Quiz completed! Score: {quiz_attempt.score:.1f}% (Passed!)"
            )
            # Mark lesson as completed if quiz was passed
            enrollment.completed_lessons.add(lesson)
        else:
            messages.info(
                request, 
                f"Quiz completed! Score: {quiz_attempt.score:.1f}% (Need {quiz.passing_score}% to pass)"
            )
        
        return redirect('lesson_detail', pk=lesson.pk)
    
    return redirect('take_quiz', quiz_pk=quiz_pk)

def logout_view(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import (
    CustomUserCreationForm, UserUpdateForm, ReportGenerationForm, DashboardWidgetForm, 
    AccessibilitySettingsForm, QuizForm, QuestionForm, AnswerOptionFormSet, LessonForm, 
    ModuleForm, CourseForm, AssignmentForm, CertificateTemplateForm, NotificationPreferenceForm, 
    CertificateClaimForm
)
from .models import (
    Course, Category, Module, Enrollment, Lesson, Quiz, Question, AnswerOption, 
    QuizAttempt, QuizAnswer, Assignment, Submission, Grade, CourseGrade, Forum, 
    Topic, Post, TopicTag, Certificate, CertificateTemplate, Notification, 
    NotificationPreference, Analytics, Report, DashboardWidget, AccessibilitySettings, 
    AccessibilityAudit, ScreenReaderContent, KeyboardShortcut, CustomUser
)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO
import os
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta
import json

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
    recent_courses = Course.objects.filter(is_active=True)[:3]
    
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    context = {
        'recent_courses': recent_courses,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/home.html', context)

def course_list(request):
    """Public course listing page"""
    courses = Course.objects.filter(is_active=True).select_related('instructor', 'category')
    
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    query = request.GET.get('q')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(instructor__username__icontains=query)
        )
    
    # Handle both ID (number) and Name (text) for category
    category_input = request.GET.get('category')
    selected_category = None

    if category_input:
        if category_input.isdigit():
            # If input is a number (e.g. ?category=1), filter by ID
            courses = courses.filter(category_id=category_input)
            selected_category = int(category_input)
        else:
            # If input is text (e.g. ?category=forex), filter by Name
            courses = courses.filter(category__name__icontains=category_input)
            # Find the ID for the dropdown UI to show selected
            cat_obj = Category.objects.filter(name__icontains=category_input).first()
            if cat_obj:
                selected_category = cat_obj.id
    
    categories = Category.objects.all()
    
    context = {
        'courses': courses,
        'categories': categories,
        'query': query,
        'selected_category': selected_category,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/course_list.html', context)

def course_detail(request, pk):
    """Course detail page with modules and lessons"""
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    is_enrolled = False
    enrollment = None
    completed_lessons = []
    
    if request.user.is_authenticated and request.user.role == 'student':
        enrollment_obj = Enrollment.objects.filter(student=request.user, course=course).first()
        is_enrolled = enrollment_obj is not None
        if is_enrolled:
            enrollment = enrollment_obj
            completed_lessons = list(enrollment.completed_lessons.values_list('pk', flat=True))
    
    modules = course.modules.all().prefetch_related('lessons')
    
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'completed_lessons': completed_lessons,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/course_detail.html', context)

def register(request):
    """User registration view"""
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            login(request, user)  # Automatically log in the user after registration
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form, 'unread_notifications': unread_notifications})

@login_required
def dashboard(request):
    """Generic dashboard view"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    context = {
        'user_role': request.user.role,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def profile(request):
    """Allow users to edit their profile"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    if request.method == 'POST':
        # Pass request.FILES to handle image uploads
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/profile.html', context)

@login_required
def student_dashboard(request):
    """Student-specific dashboard with enrolled courses"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course__instructor', 'course__category')
    
    context = {
        'user_role': request.user.role,
        'enrollments': enrollments,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    """Instructor-specific dashboard with course management"""
    if request.user.role != 'instructor':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    courses = Course.objects.filter(instructor=request.user).select_related('category').prefetch_related('modules')
    
    context = {
        'user_role': request.user.role,
        'courses': courses,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/instructor_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin-specific dashboard"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    context = {
        'user_role': request.user.role,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def create_course(request):
    """Allow instructors to create a new course"""
    if request.user.role != 'instructor':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            course = form.save()
            Forum.objects.create(course=course)
            CertificateTemplate.objects.create(course=course)
            create_notification(
                recipient=course.instructor,
                title=f"New course created: {course.title}",
                message=f"You have successfully created the course '{course.title}'.",
                notification_type='course_update',
                related_course=course
            )
            log_analytics_event(
                'course_enrollment',
                course=course,
                user=course.instructor,
                value=1.0,
                metadata={'action': 'create_course'}
            )
            return redirect('course_detail', pk=course.pk)
    else:
        form = CourseForm(user=request.user)
    
    return render(request, 'core/create_course.html', {'form': form, 'unread_notifications': unread_notifications})

@login_required
def create_module(request, course_pk):
    """Allow instructors to create a module for a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            for enrollment in course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New module added: {module.title}",
                    message=f"A new module '{module.title}' has been added to the course '{course.title}'.",
                    notification_type='course_update',
                    related_course=course,
                    related_module=module
                )
            return redirect('course_detail', pk=course.pk)
    else:
        form = ModuleForm()
    
    return render(request, 'core/create_module.html', {
        'form': form,
        'course': course,
        'unread_notifications': unread_notifications
    })

@login_required
def create_lesson(request, module_pk):
    """Allow instructors to create a lesson for a module"""
    module = get_object_or_404(Module, pk=module_pk)
    
    if request.user.role != 'instructor' or module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            lesson.save()
            for enrollment in module.course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New lesson added: {lesson.title}",
                    message=f"A new lesson '{lesson.title}' has been added to the course '{module.course.title}'.",
                    notification_type='course_update',
                    related_course=module.course,
                    related_module=module,
                    related_lesson=lesson
                )
            return redirect('course_detail', pk=module.course.pk)
    else:
        form = LessonForm()
    
    return render(request, 'core/create_lesson.html', {
        'form': form,
        'module': module,
        'unread_notifications': unread_notifications
    })

@login_required
def enroll_course(request, pk):
    """Allow students to enroll in a course"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )
    
    if created:
        messages.success(request, f'You have successfully enrolled in {course.title}!')
        create_notification(
            recipient=request.user,
            title=f"Enrolled in {course.title}",
            message=f"You have successfully enrolled in the course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
        create_notification(
            recipient=course.instructor,
            title=f"New student enrolled: {request.user.username}",
            message=f"{request.user.username} has enrolled in your course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
    else:
        messages.info(request, f'You are already enrolled in {course.title}.')
    
    return redirect('course_detail', pk=pk)

@login_required
def unenroll_course(request, pk):
    """Allow students to unenroll from a course"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    course = get_object_or_404(Course, pk=pk, is_active=True)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.delete()
        messages.success(request, f'You have successfully unenrolled from {course.title}.')
        create_notification(
            recipient=request.user,
            title=f"Unenrolled from {course.title}",
            message=f"You have successfully unenrolled from the course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
    except Enrollment.DoesNotExist:
        messages.warning(request, f'You were not enrolled in {course.title}.')
    
    return redirect('student_dashboard')

@login_required
def lesson_detail(request, pk):
    """Lesson detail page with completion tracking and navigation"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to access this lesson.")
        return redirect('course_detail', pk=course.pk)
    
    is_completed = enrollment.completed_lessons.filter(pk=pk).exists()
    completed_lesson_ids = list(enrollment.completed_lessons.values_list('pk', flat=True))

    # Calculate Previous and Next lessons across all modules
    all_lessons = []
    for module in course.modules.order_by('order'):
        all_lessons.extend(module.lessons.order_by('order'))
    
    current_index = -1
    for i, l in enumerate(all_lessons):
        if l.pk == lesson.pk:
            current_index = i
            break
    
    previous_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
    
    context = {
        'lesson': lesson,
        'course': course,
        'is_completed': is_completed,
        'enrollment': enrollment,
        'completed_lesson_ids': completed_lesson_ids,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/lesson_detail.html', context)

@login_required
def complete_lesson(request, pk):
    """Mark a lesson as completed and redirect to the next lesson"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to complete lessons.")
        return redirect('course_detail', pk=course.pk)
    
    # Mark as completed
    enrollment.completed_lessons.add(lesson)
    
    # Create notification (optional)
    create_notification(
        recipient=request.user,
        title=f"Lesson completed: {lesson.title}",
        message=f"You have completed the lesson '{lesson.title}' in course '{course.title}'.",
        notification_type='course_update',
        related_course=course,
        related_module=lesson.module,
        related_lesson=lesson
    )

    # Find Next Lesson logic
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__gt=lesson.order
    ).order_by('order').first()
    
    if not next_lesson:
        next_module = Module.objects.filter(
            course=course,
            order__gt=lesson.module.order
        ).order_by('order').first()
        
        if next_module:
            next_lesson = next_module.lessons.order_by('order').first()
    
    # Redirect
    if next_lesson:
        messages.success(request, f'Completed: "{lesson.title}". Starting next lesson.')
        return redirect('lesson_detail', pk=next_lesson.pk)
    else:
        messages.success(request, f'Congratulations! You have completed the course "{course.title}"!')
        return redirect('course_detail', pk=course.pk)

@login_required
def uncomplete_lesson(request, pk):
    """Mark a lesson as not completed"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.module.course
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to modify lesson completion.")
        return redirect('course_detail', pk=course.pk)
    
    enrollment.completed_lessons.remove(lesson)
    messages.success(request, f'Lesson "{lesson.title}" marked as incomplete.')
    
    return redirect('lesson_detail', pk=pk)

@login_required
def create_quiz(request, lesson_pk):
    """Create a quiz for a lesson"""
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    
    if request.user.role != 'instructor' or lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created successfully!')
            for enrollment in lesson.module.course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New quiz available: {quiz.title}",
                    message=f"A new quiz '{quiz.title}' has been added to the course '{lesson.module.course.title}'.",
                    notification_type='course_update',
                    related_course=lesson.module.course,
                    related_module=lesson.module
                )
            return redirect('manage_quiz', pk=quiz.pk)
    else:
        form = QuizForm()
    
    return render(request, 'core/create_quiz.html', {
        'form': form,
        'lesson': lesson,
        'unread_notifications': unread_notifications
    })

@login_required
def manage_quiz(request, pk):
    """Manage quiz questions"""
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.user.role != 'instructor' or quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    questions = quiz.questions.all()
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/manage_quiz.html', context)

@login_required
def create_question(request, quiz_pk):
    """Create a question for a quiz"""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    
    if request.user.role != 'instructor' or quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            return redirect('edit_question', pk=question.pk)
    else:
        form = QuestionForm()
    
    return render(request, 'core/create_question.html', {
        'form': form,
        'quiz': quiz,
        'unread_notifications': unread_notifications
    })

@login_required
def edit_question(request, pk):
    """Edit a question and its answer options"""
    question = get_object_or_404(Question, pk=pk)
    
    if request.user.role != 'instructor' or question.quiz.lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerOptionFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Question updated successfully!")
            return redirect('manage_quiz', pk=question.quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerOptionFormSet(instance=question)
    
    return render(request, 'core/edit_question.html', {
        'form': form,
        'formset': formset,
        'question': question,
        'unread_notifications': unread_notifications
    })

@login_required
def take_quiz(request, quiz_pk):
    """Take a quiz"""
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    lesson = quiz.lesson
    course = lesson.module.course
    
    if request.user.role != 'student':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to take this quiz.")
        return redirect('course_detail', pk=course.pk)
    
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
        'lesson': lesson,
        'unread_notifications': unread_notifications
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
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return redirect('course_detail', pk=course.pk)
    
    attempt_count = QuizAttempt.objects.filter(
        quiz=quiz, 
        student=request.user
    ).count()
    
    if attempt_count >= quiz.max_attempts:
        return redirect('lesson_detail', pk=lesson.pk)
    
    if request.method == 'POST':
        attempt_number = attempt_count + 1
        quiz_attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            attempt_number=attempt_number,
            score=0
        )
        
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
                    is_correct = False
                    QuizAnswer.objects.create(
                        quiz_attempt=quiz_attempt,
                        question=question,
                        text_answer=text_answer,
                        is_correct=is_correct
                    )
        
        if total_points > 0:
            quiz_attempt.score = (score / total_points) * 100
        else:
            quiz_attempt.score = 0
        quiz_attempt.save()
        
        if quiz_attempt.score >= quiz.passing_score:
            messages.success(
                request, 
                f"Quiz completed! Score: {quiz_attempt.score:.1f}% (Passed!)"
            )
            enrollment.completed_lessons.add(lesson)
            create_notification(
                recipient=request.user,
                title=f"Quiz passed: {quiz.title}",
                message=f"You have passed the quiz '{quiz.title}' with a score of {quiz_attempt.score:.1f}%.",
                notification_type='grade_update',
                related_course=course,
                related_module=lesson.module
            )
        else:
            messages.info(
                request, 
                f"Quiz completed! Score: {quiz_attempt.score:.1f}% (Need {quiz.passing_score}% to pass)"
            )
            create_notification(
                recipient=request.user,
                title=f"Quiz failed: {quiz.title}",
                message=f"You have failed the quiz '{quiz.title}' with a score of {quiz_attempt.score:.1f}%.",
                notification_type='grade_update',
                related_course=course,
                related_module=lesson.module
            )
        
        return redirect('lesson_detail', pk=lesson.pk)
    
    return redirect('take_quiz', quiz_pk=quiz_pk)

@login_required
def create_assignment(request, lesson_pk):
    """Create an assignment for a lesson"""
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    
    if request.user.role != 'instructor' or lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()
            messages.success(request, f'Assignment "{assignment.title}" created successfully!')
            for enrollment in lesson.module.course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New assignment: {assignment.title}",
                    message=f"A new assignment '{assignment.title}' has been added to the course '{lesson.module.course.title}'. Due date: {assignment.due_date.strftime('%B %d, %Y')}",
                    notification_type='assignment_due',
                    related_course=lesson.module.course,
                    related_module=lesson.module
                )
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        form = AssignmentForm()
    
    return render(request, 'core/create_assignment.html', {
        'form': form,
        'lesson': lesson,
        'unread_notifications': unread_notifications
    })

@login_required
def student_gradebook(request):
    """Show student's gradebook"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course', 'course__instructor')
    
    gradebook_data = []
    for enrollment in enrollments:
        grades = enrollment.grades.all().order_by('-date_recorded')
        course_grade = getattr(enrollment, 'course_grade', None)
        
        gradebook_data.append({
            'course': enrollment.course,
            'grades': grades,
            'course_grade': course_grade
        })
    
    context = {
        'gradebook_data': gradebook_data,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/student_gradebook.html', context)

@login_required
def instructor_gradebook(request, course_pk):
    """Show instructor's gradebook for a specific course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    assignments = Assignment.objects.filter(lesson__module__course=course).prefetch_related('submissions')
    quizzes = Quiz.objects.filter(lesson__module__course=course)
    
    gradebook_data = []
    for enrollment in enrollments:
        student_grades = {
            'student': enrollment.student,
            'assignments': [],
            'quizzes': [],
            'course_grade': getattr(enrollment, 'course_grade', None)
        }
        
        for assignment in assignments:
            try:
                submission = assignment.submissions.get(student=enrollment.student)
                student_grades['assignments'].append({
                    'assignment': assignment,
                    'submission': submission,
                    'grade': submission.grade
                })
            except Submission.DoesNotExist:
                student_grades['assignments'].append({
                    'assignment': assignment,
                    'submission': None,
                    'grade': None
                })
        
        for quiz in quizzes:
            quiz_grades = enrollment.grades.filter(quiz=quiz).order_by('-date_recorded')
            student_grades['quizzes'].extend([{
                'quiz': quiz,
                'grade': grade
            } for grade in quiz_grades])
        
        gradebook_data.append(student_grades)
    
    context = {
        'course': course,
        'gradebook_data': gradebook_data,
        'assignments': assignments,
        'quizzes': quizzes,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/instructor_gradebook.html', context)

@login_required
def record_grade(request, enrollment_pk, grade_type, item_pk):
    """Record a grade for an assignment or quiz"""
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)
    
    if request.user.role != 'instructor' or enrollment.course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        score = float(request.POST.get('score', 0))
        max_points = float(request.POST.get('max_points', 100))
        
        if grade_type == 'assignment':
            assignment = get_object_or_404(Assignment, pk=item_pk)
            grade, created = Grade.objects.get_or_create(
                enrollment=enrollment,
                assignment=assignment,
                defaults={
                    'score': score,
                    'max_points': max_points,
                    'grade_type': 'assignment'
                }
            )
            if not created:
                grade.score = score
                grade.max_points = max_points
                grade.save()
        elif grade_type == 'quiz':
            quiz = get_object_or_404(Quiz, pk=item_pk)
            grade, created = Grade.objects.get_or_create(
                enrollment=enrollment,
                quiz=quiz,
                defaults={
                    'score': score,
                    'max_points': max_points,
                    'grade_type': 'quiz'
                }
            )
            if not created:
                grade.score = score
                grade.max_points = max_points
                grade.save()
        
        course_grade, created = CourseGrade.objects.get_or_create(enrollment=enrollment)
        course_grade.save() 
        
        if grade_type == 'assignment':
            create_notification(
                recipient=enrollment.student,
                title=f"Grade recorded for {assignment.title}",
                message=f"Your grade for assignment '{assignment.title}' has been recorded: {score}/{max_points}",
                notification_type='grade_update',
                related_course=enrollment.course
            )
        elif grade_type == 'quiz':
            create_notification(
                recipient=enrollment.student,
                title=f"Grade recorded for {quiz.title}",
                message=f"Your grade for quiz '{quiz.title}' has been recorded: {score}/{max_points}",
                notification_type='grade_update',
                related_course=enrollment.course
            )
        
        messages.success(request, "Grade recorded successfully!")
    
    redirect_url = request.POST.get('redirect_url', 'dashboard')
    return redirect(redirect_url)

@login_required
def course_forum(request, course_pk):
    """Show course forum with topics"""
    course = get_object_or_404(Course, pk=course_pk)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    is_enrolled = False
    if request.user.is_authenticated and request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to access the forum.")
        return redirect('course_detail', pk=course.pk)
    
    forum, created = Forum.objects.get_or_create(course=course)
    
    topics = forum.topics.all().prefetch_related('author', 'posts')
    
    context = {
        'course': course,
        'forum': forum,
        'topics': topics,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/course_forum.html', context)

@login_required
def create_topic(request, forum_pk):
    """Create a new topic in a forum"""
    forum = get_object_or_404(Forum, pk=forum_pk)
    course = forum.course
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to create topics.")
        return redirect('course_forum', course_pk=course.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        
        if title and content:
            topic = Topic.objects.create(
                forum=forum,
                title=title,
                content=content,
                author=request.user
            )
            messages.success(request, f'Topic "{topic.title}" created successfully!')
            create_notification(
                recipient=course.instructor,
                title=f"New topic created: {topic.title}",
                message=f"{request.user.username} has created a new topic '{topic.title}' in course '{course.title}'.",
                notification_type='forum_post',
                related_course=course
            )
            return redirect('topic_detail', topic_pk=topic.pk)
        else:
            messages.error(request, "Please fill in both title and content.")
    
    context = {
        'forum': forum,
        'course': course,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/create_topic.html', context)

@login_required
def topic_detail(request, topic_pk):
    """Show topic with all its posts"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    forum = topic.forum
    course = forum.course
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to access this topic.")
        return redirect('course_forum', course_pk=course.pk)
    
    posts = topic.posts.all().prefetch_related('author')
    
    context = {
        'topic': topic,
        'forum': forum,
        'course': course,
        'posts': posts,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/topic_detail.html', context)

@login_required
def create_post(request, topic_pk):
    """Create a new post in a topic"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    forum = topic.forum
    course = forum.course
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to create posts.")
        return redirect('topic_detail', topic_pk=topic.pk)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            post = Post.objects.create(
                topic=topic,
                content=content,
                author=request.user
            )
            messages.success(request, "Post created successfully!")
            if post.topic.author != request.user:
                create_notification(
                    recipient=post.topic.author,
                    title=f"New reply to your topic: {post.topic.title}",
                    message=f"{request.user.username} replied to your topic '{post.topic.title}'",
                    notification_type='forum_post',
                    related_course=course
                )
            create_notification(
                recipient=course.instructor,
                title=f"New post in {post.topic.title}",
                message=f"{request.user.username} made a new post in topic '{post.topic.title}' in course '{course.title}'.",
                notification_type='forum_post',
                related_course=course
            )
            return redirect('topic_detail', topic_pk=topic.pk)
        else:
            messages.error(request, "Please enter content for your post.")
    
    return redirect('topic_detail', topic_pk=topic.pk)

# --- CERTIFICATES: CLAIM AND GENERATE LOGIC ---

@login_required
def claim_certificate(request, course_pk):
    """Allow user to input name before generating certificate"""
    course = get_object_or_404(Course, pk=course_pk)
    
    # 1. Check Enrollment
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled to claim a certificate.")
        return redirect('course_detail', pk=course.pk)

    # 2. Check Progress (Must be 100%)
    if enrollment.progress_percentage() < 100:
        messages.warning(request, "You must complete 100% of the course to claim your certificate.")
        return redirect('course_detail', pk=course.pk)

    # 3. Handle Form
    if request.method == 'POST':
        form = CertificateClaimForm(request.POST)
        if form.is_valid():
            # Create or Update Certificate
            certificate, created = Certificate.objects.get_or_create(enrollment=enrollment)
            certificate.full_name = form.cleaned_data['full_name']
            certificate.save()
            
            if created:
                messages.success(request, "Certificate generated successfully!")
                create_notification(
                    recipient=request.user,
                    title=f"Certificate Claimed: {course.title}",
                    message=f"You have claimed your certificate for '{course.title}'.",
                    notification_type='certificate_earned',
                    related_course=course
                )
            
            return redirect('generate_certificate', enrollment_pk=enrollment.pk)
    else:
        # Pre-fill with current user name
        initial_name = request.user.get_full_name() or request.user.username
        if hasattr(enrollment, 'certificate'):
            initial_name = enrollment.certificate.full_name
        form = CertificateClaimForm(initial={'full_name': initial_name})

    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'core/claim_certificate.html', {
        'form': form,
        'course': course,
        'unread_notifications': unread_notifications
    })

@login_required
def generate_certificate(request, enrollment_pk):
    """Download the PDF certificate with Dynamic Logo, Signature, QR Code and CEO Name"""
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)
    
    if request.user != enrollment.student and request.user != enrollment.course.instructor:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    # Get certificate (redirect if not claimed)
    try:
        certificate = enrollment.certificate
    except Certificate.DoesNotExist:
        return redirect('claim_certificate', course_pk=enrollment.course.pk)

    # --- PDF GENERATION SETUP ---
    buffer = BytesIO()
    # Use Landscape
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # 1. Load Template
    try:
        template = enrollment.course.certificate_template
    except CertificateTemplate.DoesNotExist:
        template = CertificateTemplate.objects.create(course=enrollment.course)

    # 2. Draw Background (If uploaded)
    if template.background_image:
        try:
            # Draws the full template background (Logos, borders, fixed text)
            p.drawImage(template.background_image.path, 0, 0, width=width, height=height)
        except:
            pass
    
    # --- IF NO BACKGROUND, DRAW FALLBACK BORDER ---
    if not template.background_image:
        # Outer Border (Blue)
        p.setStrokeColor(HexColor('#0d6efd'))
        p.setLineWidth(12)
        p.rect(20, 20, width-40, height-40)
        # Inner Border (Black)
        p.setStrokeColor(HexColor('#000000'))
        p.setLineWidth(2)
        p.rect(35, 35, width-70, height-70)
        # Fallback Title
        p.setFillColor(HexColor('#000000'))
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2.0, height - 1.5*inch, "AUA TECHNOLOGIES LIMITED")

    # --- 3. DRAW LOGO (Dynamic) ---
    if template.logo:
        try:
            # Position: Top Left Area
            p.drawImage(template.logo.path, 50, height - 120, width=120, height=80, mask='auto', preserveAspectRatio=True)
        except:
            pass

    # --- 4. DRAW SIGNATURE (Dynamic) ---
    if template.signature:
        try:
            # Position: Bottom Leftish/Center (Above CEO Name)
            # Adjust coordinates (x=100, y=115) to fit nicely above the line
            p.drawImage(template.signature.path, 100, 115, width=150, height=60, mask='auto', preserveAspectRatio=True)
        except:
            pass

    # --- TEXT OVERLAYS ---
    
    # Certificate Title
    p.setFillColor(HexColor('#0d6efd')) # Blue
    p.setFont("Helvetica-Bold", 36)
    p.drawCentredString(width/2.0, height - 2.5*inch, template.title)
    
    # Intro
    p.setFillColor(HexColor('#555555')) # Dark Gray
    p.setFont("Helvetica", 16)
    p.drawCentredString(width/2.0, height - 3.2*inch, template.description)
    
    # STUDENT NAME (Centered & Bold)
    p.setFillColor(HexColor('#000000')) # Black
    p.setFont("Helvetica-Bold", 32)
    p.drawCentredString(width/2.0, height - 4.2*inch, certificate.full_name) 
    
    # Underline Name
    p.setLineWidth(1)
    p.setStrokeColor(HexColor('#000000'))
    p.line(width/2.0 - 200, height - 4.3*inch, width/2.0 + 200, height - 4.3*inch)

    # Body Text
    p.setFillColor(HexColor('#555555')) # Dark Gray
    p.setFont("Helvetica", 14)
    
    date_str = certificate.issued_at.strftime('%d/%m/%Y')
    
    line1 = "\"In recognition of successfully completing the prescribed"
    line2 = f"training module in {enrollment.course.title} and having met all"
    line3 = f"requirements for the award, issued on {date_str}.\""
    
    text_start_y = height - 5.0*inch
    p.drawCentredString(width/2.0, text_start_y, line1)
    p.drawCentredString(width/2.0, text_start_y - 25, line2)
    p.drawCentredString(width/2.0, text_start_y - 50, line3)
    
    # CEO Name and Title
    p.setFillColor(HexColor('#000000'))
    p.setFont("Helvetica-Bold", 14)
    
    # Signature Line
    p.setLineWidth(1)
    p.line(100, 115, 250, 115) 
    
    # Name & Title
    p.drawString(100, 100, "MUSAB ABBAS SANI")
    p.setFont("Helvetica", 12)
    p.drawString(100, 85, "CEO")

    # QR Code (Bottom Right)
    qr_data = f"VERIFIED AUA CERTIFICATE\nName: {certificate.full_name}\nCourse: {enrollment.course.title}\nID: {certificate.certificate_id}\nDate: {date_str}\nSigned: MUSAB ABBAS SANI"
    qr = qrcode.make(qr_data)
    
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    qr_image = ImageReader(qr_buffer)
    p.drawImage(qr_image, width - 180, 50, width=100, height=100)
    
    p.setFont("Helvetica", 8)
    p.drawRightString(width - 80, 40, f"ID: {certificate.certificate_id}")

    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="certificate_{certificate.certificate_id}.pdf"'
    
    return response

# ... (Keep remaining views: student_certificates, instructor_certificates, etc.) ...
# Note: The rest of the file remains as you provided, ensure you keep the other views below generate_certificate.
# For brevity in this response, I'm confirming the generate_certificate logic is the key change.
# Please ensure you copy the entire file content if you are replacing the whole file.

@login_required
def student_certificates(request):
    """Show student's certificates"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    certificates = Certificate.objects.filter(
        enrollment__student=request.user,
        is_active=True
    ).select_related('enrollment__course', 'enrollment__student')
    
    context = {
        'certificates': certificates,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/student_certificates.html', context)

@login_required
def instructor_certificates(request, course_pk=None):
    """Show certificates for students in a specific course OR list all courses."""
    if course_pk is None:
        if request.user.role != 'instructor':
            return redirect('dashboard')
        
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()

        courses = Course.objects.filter(instructor=request.user)
        
        return render(request, 'core/instructor_certificates_list.html', {
            'courses': courses,
            'unread_notifications': unread_notifications
        })

    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    certificates = Certificate.objects.filter(
        enrollment__course=course,
        is_active=True
    ).select_related('enrollment__student')
    
    context = {
        'course': course,
        'certificates': certificates,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/instructor_certificates.html', context)

@login_required
def manage_certificate_template(request, course_pk):
    """Manage certificate template for a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        template = course.certificate_template
    except CertificateTemplate.DoesNotExist:
        template = CertificateTemplate.objects.create(course=course)
    
    if request.method == 'POST':
        from .forms import CertificateTemplateForm
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Certificate template updated successfully!")
            return redirect('manage_certificate_template', course_pk=course.pk)
    else:
        from .forms import CertificateTemplateForm
        form = CertificateTemplateForm(instance=template)
    
    context = {
        'form': form,
        'course': course,
        'template': template,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/manage_certificate_template.html', context)

@login_required
def check_certificate_eligibility(request, course_pk):
    """Check if user is eligible for certificate"""
    course = get_object_or_404(Course, pk=course_pk)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to check certificate eligibility.")
        return redirect('course_detail', pk=course.pk)
    
    progress = enrollment.progress_percentage()
    
    context = {
        'course': course,
        'progress': progress,
        'is_eligible': progress >= 80,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/certificate_eligibility.html', context)

@login_required
def notifications_list(request):
    """Show user's notifications"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    notifications = Notification.objects.filter(recipient=request.user).select_related('related_course')
    
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/notifications_list.html', context)

@login_required
def notification_preference(request):
    """Manage notification preferences"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        from .forms import NotificationPreferenceForm
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully!")
            return redirect('notification_preference')
    else:
        from .forms import NotificationPreferenceForm
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/notification_preference.html', context)

@login_required
def mark_notification_read(request, notification_pk):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, pk=notification_pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    redirect_url = request.GET.get('redirect_url', 'notifications_list')
    return redirect(redirect_url)

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read!")
    
    redirect_url = request.GET.get('redirect_url', 'notifications_list')
    return redirect(redirect_url)

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.user.role == 'instructor':
        courses = Course.objects.filter(instructor=request.user)
        analytics_data = Analytics.objects.filter(course__in=courses)
    else:
        analytics_data = Analytics.objects.all()
    
    total_enrollments = analytics_data.filter(analytics_type='course_enrollment').count()
    total_completions = analytics_data.filter(analytics_type='course_completion').count()
    total_lessons_completed = analytics_data.filter(analytics_type='lesson_completion').count()
    total_quiz_attempts = analytics_data.filter(analytics_type='quiz_attempt').count()
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_analytics = analytics_data.filter(date_recorded__gte=thirty_days_ago)
    
    enrollment_trend = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        count = recent_analytics.filter(
            analytics_type='course_enrollment',
            date_recorded__date=date.date()
        ).count()
        enrollment_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    context = {
        'total_enrollments': total_enrollments,
        'total_completions': total_completions,
        'total_lessons_completed': total_lessons_completed,
        'total_quiz_attempts': total_quiz_attempts,
        'enrollment_trend': list(reversed(enrollment_trend)),
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/analytics_dashboard.html', context)

@login_required
def generate_report(request):
    """Generate custom reports"""
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.method == 'POST':
        from .forms import ReportGenerationForm
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            report_data = generate_report_data(report.report_type, form.cleaned_data['start_date'], form.cleaned_data['end_date'])
            report.data = report_data
            
            report.save()
            messages.success(request, f"Report '{report.title}' generated successfully!")
            return redirect('view_report', report_pk=report.pk)
    else:
        from .forms import ReportGenerationForm
        form = ReportGenerationForm()
    
    context = {
        'form': form,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/generate_report.html', context)

@login_required
def view_report(request, report_pk):
    """View a specific report"""
    report = get_object_or_404(Report, pk=report_pk)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.user.role not in ['admin'] and report.generated_by != request.user:
        return redirect('dashboard')
    
    context = {
        'report': report,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/view_report.html', context)

@login_required
def course_analytics(request, course_pk):
    """Analytics for a specific course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.user.role == 'instructor' and course.instructor != request.user:
        return redirect('dashboard')
    elif request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    analytics_data = Analytics.objects.filter(course=course)
    
    total_enrollments = analytics_data.filter(analytics_type='course_enrollment').count()
    total_completions = analytics_data.filter(analytics_type='course_completion').count()
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = (total_completions / total_enrollments) * 100
    
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    student_progress = []
    for enrollment in enrollments:
        progress = enrollment.progress_percentage()
        student_progress.append({
            'student': enrollment.student.username,
            'progress': progress,
            'completed_lessons': enrollment.completed_lessons.count()
        })
    
    lesson_completion_data = []
    for module in course.modules.all():
        for lesson in module.lessons.all():
            completed_count = Enrollment.objects.filter(
                course=course,
                completed_lessons=lesson
            ).count()
            total_enrolled = course.enrollments.count()
            
            completion_percentage = 0
            if total_enrolled > 0:
                completion_percentage = (completed_count / total_enrolled) * 100
            
            lesson_completion_data.append({
                'lesson': lesson.title,
                'module': module.title,
                'completion_percentage': completion_percentage
            })
    
    context = {
        'course': course,
        'total_enrollments': total_enrollments,
        'total_completions': total_completions,
        'completion_rate': completion_rate,
        'student_progress': student_progress,
        'lesson_completion_data': lesson_completion_data,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/course_analytics.html', context)

@login_required
def student_analytics(request, student_pk):
    """Analytics for a specific student"""
    student = get_object_or_404(CustomUser, pk=student_pk)
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    if request.user.role == 'instructor':
        student_courses = Course.objects.filter(instructor=request.user, enrollments__student=student).distinct()
        if not student_courses.exists():
            return redirect('dashboard')
    
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    
    total_courses = enrollments.count()
    completed_courses = 0
    total_progress = 0
    
    course_data = []
    for enrollment in enrollments:
        progress = enrollment.progress_percentage()
        total_progress += progress
        
        if progress >= 80:
            completed_courses += 1
        
        course_data.append({
            'course': enrollment.course.title,
            'progress': progress,
            'completed_lessons': enrollment.completed_lessons.count(),
            'total_lessons': enrollment.course.lessons.count()
        })
    
    average_progress = 0
    if total_courses > 0:
        average_progress = total_progress / total_courses
    
    grades = Grade.objects.filter(enrollment__student=student).select_related('enrollment__course')
    
    context = {
        'student': student,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'average_progress': average_progress,
        'course_data': course_data,
        'grades': grades,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/student_analytics.html', context)

@login_required
def accessibility_settings(request):
    """Manage user accessibility preferences"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    settings, created = AccessibilitySettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        from .forms import AccessibilitySettingsForm
        form = AccessibilitySettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Accessibility settings updated successfully!")
            return redirect('accessibility_settings')
    else:
        from .forms import AccessibilitySettingsForm
        form = AccessibilitySettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/accessibility_settings.html', context)

@login_required
def toggle_accessibility_mode(request, mode):
    """Toggle specific accessibility modes"""
    settings, created = AccessibilitySettings.objects.get_or_create(user=request.user)
    
    if mode == 'high_contrast':
        settings.high_contrast_mode = not settings.high_contrast_mode
    elif mode == 'large_text':
        settings.large_text_mode = not settings.large_text_mode
    elif mode == 'reduced_motion':
        settings.reduced_motion_mode = not settings.reduced_motion_mode
    elif mode == 'screen_reader':
        settings.screen_reader_optimized = not settings.screen_reader_optimized
    elif mode == 'keyboard_nav':
        settings.keyboard_navigation_enabled = not settings.keyboard_navigation_enabled
    
    settings.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'enabled': getattr(settings, f'{mode.replace("-", "_")}_mode')})
    
    return redirect('accessibility_settings')

def accessibility_statement(request):
    """Display accessibility statement and compliance information"""
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    context = {
        'statement': """
        <h2>Accessibility Statement</h2>
        <p>We are committed to ensuring digital accessibility for all users. Our website and application are designed to meet WCAG 2.1 AA standards.</p>
        
        <h3>Our Commitment</h3>
        <p>We continuously work to improve the accessibility of our platform for people with disabilities and older adults.</p>
        
        <h3>Features Available</h3>
        <ul>
            <li>Keyboard navigation support</li>
            <li>Screen reader compatibility</li>
            <li>High contrast mode</li>
            <li>Large text option</li>
            <li>Reduced motion settings</li>
            <li>Focus indicators</li>
        </ul>
        
        <h3>Feedback</h3>
        <p>If you encounter any accessibility barriers, please contact us at accessibility@example.com</p>
        """,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/accessibility_statement.html', context)

def keyboard_shortcuts(request):
    """Display available keyboard shortcuts"""
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    shortcuts = KeyboardShortcut.objects.filter(is_active=True)
    
    context = {
        'shortcuts': shortcuts,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/keyboard_shortcuts.html', context)

@login_required
def accessibility_audit_log(request):
    """View accessibility audit logs (admin only)"""
    if request.user.role not in ['admin', 'instructor']:
        return redirect('dashboard')
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    audits = AccessibilityAudit.objects.all().select_related('performed_by').order_by('-created_at')
    
    context = {
        'audits': audits,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/accessibility_audit_log.html', context)

@login_required
def run_accessibility_scan(request):
    """Simulate running an accessibility scan (admin only)"""
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    # In a real system, this would run actual accessibility scanning tools
    # For now, we'll simulate finding some issues
    
    findings = [
        "Missing alt text on 3 images",
        "Low contrast ratio on 2 elements",
        "Missing form labels on 1 input",
        "Keyboard trap detected on modal",
    ]
    
    for finding in findings:
        AccessibilityAudit.objects.create(
            audit_type='automated',
            performed_by=request.user,
            findings=finding,
            severity='medium'
        )
    
    messages.success(request, f"Accessibility scan completed. Found {len(findings)} potential issues.")
    return redirect('accessibility_audit_log')

def accessibility_resources(request):
    """Provide accessibility resources and tools"""
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
    
    resources = [
        {
            'title': 'Web Content Accessibility Guidelines (WCAG)',
            'url': 'https://www.w3.org/WAI/WCAG21/quickref/',
            'description': 'Official guidelines for web accessibility'
        },
        {
            'title': 'Screen Reader Testing',
            'url': 'https://webaim.org/articles/screenreader_testing/',
            'description': 'How to test with screen readers'
        },
        {
            'title': 'Color Contrast Checker',
            'url': 'https://webaim.org/resources/contrastchecker/',
            'description': 'Tool to check color contrast ratios'
        },
        {
            'title': 'Keyboard Navigation',
            'url': 'https://webaim.org/articles/keyboard/',
            'description': 'Best practices for keyboard accessibility'
        },
    ]
    
    context = {
        'resources': resources,
        'unread_notifications': unread_notifications
    }
    return render(request, 'core/accessibility_resources.html', context)

def create_notification(recipient, title, message, notification_type='general', related_course=None, related_module=None, related_lesson=None):
    """Helper function to create a notification"""
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_course=related_course,
        related_module=related_module,
        related_lesson=related_lesson
    )
    return notification

def log_analytics_event(analytics_type, course=None, user=None, value=1.0, metadata=None):
    """Helper function to log analytics events"""
    if metadata is None:
        metadata = {}
    
    Analytics.objects.create(
        analytics_type=analytics_type,
        course=course,
        user=user,
        value=value,
        metadata=metadata
    )

def generate_report_data(report_type, start_date, end_date):
    """Generate data for different report types"""
    data = {}
    
    if report_type == 'course_performance':
        courses = Course.objects.all()
        data['courses'] = []
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            total_enrolled = enrollments.count()
            total_completed = 0
            avg_progress = 0
            
            for enrollment in enrollments:
                progress = enrollment.progress_percentage()
                if progress >= 80:
                    total_completed += 1
                avg_progress += progress
            
            avg_progress = avg_progress / total_enrolled if total_enrolled > 0 else 0
            
            data['courses'].append({
                'title': course.title,
                'instructor': course.instructor.username,
                'enrolled': total_enrolled,
                'completed': total_completed,
                'completion_rate': (total_completed / total_enrolled * 100) if total_enrolled > 0 else 0,
                'avg_progress': avg_progress
            })
    
    elif report_type == 'student_progress':
        students = CustomUser.objects.filter(role='student')
        data['students'] = []
        for student in students:
            enrollments = Enrollment.objects.filter(student=student)
            total_courses = enrollments.count()
            avg_progress = 0
            completed_courses = 0
            
            for enrollment in enrollments:
                progress = enrollment.progress_percentage()
                avg_progress += progress
                if progress >= 80:
                    completed_courses += 1
            
            avg_progress = avg_progress / total_courses if total_courses > 0 else 0
            
            data['students'].append({
                'username': student.username,
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'avg_progress': avg_progress
            })
    
    elif report_type == 'user_engagement':
        data['total_users'] = CustomUser.objects.count()
        data['active_students'] = CustomUser.objects.filter(role='student').count()
        data['instructors'] = CustomUser.objects.filter(role='instructor').count()
        
        analytics_in_range = Analytics.objects.filter(
            date_recorded__date__gte=start_date,
            date_recorded__date__lte=end_date
        )
        
        data['activity_summary'] = {
            'enrollments': analytics_in_range.filter(analytics_type='course_enrollment').count(),
            'completions': analytics_in_range.filter(analytics_type='course_completion').count(),
            'lesson_completions': analytics_in_range.filter(analytics_type='lesson_completion').count(),
            'quiz_attempts': analytics_in_range.filter(analytics_type='quiz_attempt').count(),
        }
    
    elif report_type == 'grade_distribution':
        grades = Grade.objects.filter(
            date_recorded__date__gte=start_date,
            date_recorded__date__lte=end_date
        )
        
        data['grade_stats'] = {
            'total_grades': grades.count(),
            'avg_score': grades.aggregate(Avg('score'))['score__avg'] or 0,
            'avg_max_points': grades.aggregate(Avg('max_points'))['max_points__avg'] or 0,
        }
        
        data['by_type'] = {}
        for grade_type in ['quiz', 'assignment', 'exam']:
            type_grades = grades.filter(grade_type=grade_type)
            data['by_type'][grade_type] = {
                'count': type_grades.count(),
                'avg_score': type_grades.aggregate(Avg('score'))['score__avg'] or 0,
            }
    
    elif report_type == 'certificate_issuance':
        certificates = Certificate.objects.filter(
            issued_at__date__gte=start_date,
            issued_at__date__lte=end_date
        )
        
        data['certificates'] = {
            'total_issued': certificates.count(),
            'by_course': {}
        }
        
        for cert in certificates:
            course_title = cert.enrollment.course.title
            if course_title not in data['certificates']['by_course']:
                data['certificates']['by_course'][course_title] = 0
            data['certificates']['by_course'][course_title] += 1
    
    return data

def logout_view(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
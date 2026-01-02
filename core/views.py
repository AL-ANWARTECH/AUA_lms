from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from .models import Course, Category, Module, Enrollment, Lesson, Quiz, Question, AnswerOption, QuizAttempt, QuizAnswer, Assignment, Submission, Grade, CourseGrade, Forum, Topic, Post, TopicTag, Certificate, CertificateTemplate, Notification, NotificationPreference, Analytics, Report, DashboardWidget
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from io import BytesIO
import os
from django.http import HttpResponse
from .certificate_forms import CertificateTemplateForm
from .notification_forms import NotificationPreferenceForm
from .analytics_forms import ReportGenerationForm, DashboardWidgetForm
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
            # Create forum for the course automatically
            Forum.objects.create(course=course)
            # Create certificate template for the course automatically
            CertificateTemplate.objects.create(course=course)
            # Create notification for all enrolled students
            create_notification(
                recipient=course.instructor,
                title=f"New course created: {course.title}",
                message=f"You have successfully created the course '{course.title}'.",
                notification_type='course_update',
                related_course=course
            )
            # Log analytics event
            log_analytics_event(
                'course_enrollment',
                course=course,
                user=course.instructor,
                value=1.0,
                metadata={'action': 'create_course'}
            )
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
            # Create notification for all enrolled students
            for enrollment in course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New module added: {module.title}",
                    message=f"A new module '{module.title}' has been added to the course '{course.title}'.",
                    notification_type='course_update',
                    related_course=course,
                    related_module=module
                )
            # Log analytics event
            log_analytics_event(
                'course_enrollment',
                course=course,
                user=course.instructor,
                value=1.0,
                metadata={'action': 'create_module', 'module_id': module.id}
            )
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
            # Create notification for all enrolled students
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
            # Log analytics event
            log_analytics_event(
                'course_enrollment',
                course=module.course,
                user=module.course.instructor,
                value=1.0,
                metadata={'action': 'create_lesson', 'lesson_id': lesson.id}
            )
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
        # Create notification for the student
        create_notification(
            recipient=request.user,
            title=f"Enrolled in {course.title}",
            message=f"You have successfully enrolled in the course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
        # Create notification for the instructor
        create_notification(
            recipient=course.instructor,
            title=f"New student enrolled: {request.user.username}",
            message=f"{request.user.username} has enrolled in your course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
        # Log analytics event
        log_analytics_event(
            'course_enrollment',
            course=course,
            user=request.user,
            value=1.0,
            metadata={'action': 'enroll_course'}
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
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.delete()
        messages.success(request, f'You have successfully unenrolled from {course.title}.')
        # Create notification for the student
        create_notification(
            recipient=request.user,
            title=f"Unenrolled from {course.title}",
            message=f"You have successfully unenrolled from the course '{course.title}'.",
            notification_type='enrollment',
            related_course=course
        )
        # Log analytics event
        log_analytics_event(
            'course_enrollment',
            course=course,
            user=request.user,
            value=-1.0,
            metadata={'action': 'unenroll_course'}
        )
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
    
    # Create notification for the student
    create_notification(
        recipient=request.user,
        title=f"Lesson completed: {lesson.title}",
        message=f"You have completed the lesson '{lesson.title}' in course '{course.title}'.",
        notification_type='course_update',
        related_course=course,
        related_module=lesson.module,
        related_lesson=lesson
    )
    
    # Log analytics event
    log_analytics_event(
        'lesson_completion',
        course=course,
        user=request.user,
        value=1.0,
        metadata={'action': 'complete_lesson', 'lesson_id': lesson.id}
    )
    
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
    
    # Create notification for the student
    create_notification(
        recipient=request.user,
        title=f"Lesson marked as incomplete: {lesson.title}",
        message=f"You have marked the lesson '{lesson.title}' as incomplete in course '{course.title}'.",
        notification_type='course_update',
        related_course=course,
        related_module=lesson.module,
        related_lesson=lesson
    )
    
    # Log analytics event
    log_analytics_event(
        'lesson_completion',
        course=course,
        user=request.user,
        value=-1.0,
        metadata={'action': 'uncomplete_lesson', 'lesson_id': lesson.id}
    )
    
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
            # Create notification for all enrolled students
            for enrollment in lesson.module.course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New quiz available: {quiz.title}",
                    message=f"A new quiz '{quiz.title}' has been added to the course '{lesson.module.course.title}'.",
                    notification_type='course_update',
                    related_course=lesson.module.course,
                    related_module=lesson.module
                )
            # Log analytics event
            log_analytics_event(
                'course_enrollment',
                course=lesson.module.course,
                user=lesson.module.course.instructor,
                value=1.0,
                metadata={'action': 'create_quiz', 'quiz_id': quiz.id}
            )
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
            # Create notification for the student
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
            # Create notification for the student
            create_notification(
                recipient=request.user,
                title=f"Quiz failed: {quiz.title}",
                message=f"You have failed the quiz '{quiz.title}' with a score of {quiz_attempt.score:.1f}%.",
                notification_type='grade_update',
                related_course=course,
                related_module=lesson.module
            )
        
        # Log analytics event
        log_analytics_event(
            'quiz_attempt',
            course=course,
            user=request.user,
            value=quiz_attempt.score,
            metadata={'action': 'submit_quiz', 'quiz_id': quiz.id, 'score': quiz_attempt.score}
        )
        
        return redirect('lesson_detail', pk=lesson.pk)
    
    return redirect('take_quiz', quiz_pk=quiz_pk)

@login_required
def create_assignment(request, lesson_pk):
    """Create an assignment for a lesson"""
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    
    if request.user.role != 'instructor' or lesson.module.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .assignment_forms import AssignmentForm
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()
            messages.success(request, f'Assignment "{assignment.title}" created successfully!')
            # Create notification for all enrolled students
            for enrollment in lesson.module.course.enrollments.all():
                create_notification(
                    recipient=enrollment.student,
                    title=f"New assignment: {assignment.title}",
                    message=f"A new assignment '{assignment.title}' has been added to the course '{lesson.module.course.title}'. Due date: {assignment.due_date.strftime('%B %d, %Y')}",
                    notification_type='assignment_due',
                    related_course=lesson.module.course,
                    related_module=lesson.module
                )
            # Log analytics event
            log_analytics_event(
                'course_enrollment',
                course=lesson.module.course,
                user=lesson.module.course.instructor,
                value=1.0,
                metadata={'action': 'create_assignment', 'assignment_id': assignment.id}
            )
            return redirect('lesson_detail', pk=lesson.pk)
    else:
        from .assignment_forms import AssignmentForm
        form = AssignmentForm()
    
    return render(request, 'core/create_assignment.html', {
        'form': form,
        'lesson': lesson
    })

@login_required
def student_gradebook(request):
    """Show student's gradebook"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Get all enrollments for this student
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course', 'course__instructor')
    
    # Get grades for each enrollment
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
        'gradebook_data': gradebook_data
    }
    return render(request, 'core/student_gradebook.html', context)

@login_required
def instructor_gradebook(request, course_pk):
    """Show instructor's gradebook for a specific course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    # Get all students enrolled in this course
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    
    # Get all assignments and quizzes for this course
    assignments = Assignment.objects.filter(lesson__module__course=course).prefetch_related('submissions')
    quizzes = Quiz.objects.filter(lesson__module__course=course)
    
    # Prepare gradebook data
    gradebook_data = []
    for enrollment in enrollments:
        student_grades = {
            'student': enrollment.student,
            'assignments': [],
            'quizzes': [],
            'course_grade': getattr(enrollment, 'course_grade', None)
        }
        
        # Get assignment grades
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
        
        # Get quiz grades
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
        'quizzes': quizzes
    }
    return render(request, 'core/instructor_gradebook.html', context)

@login_required
def record_grade(request, enrollment_pk, grade_type, item_pk):
    """Record a grade for an assignment or quiz"""
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)
    
    if request.user.role != 'instructor' or enrollment.course.instructor != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        score = float(request.POST.get('score', 0))
        max_points = float(request.POST.get('max_points', 100))
        
        # Create or update grade
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
        
        # Update course grade
        course_grade, created = CourseGrade.objects.get_or_create(enrollment=enrollment)
        course_grade.save()  # This will recalculate the final grade
        
        # Create notification for the student
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
        
        # Log analytics event
        log_analytics_event(
            'grade_distribution',
            course=course,
            user=enrollment.student,
            value=score,
            metadata={'action': 'record_grade', 'grade_type': grade_type, 'score': score, 'max_points': max_points}
        )
        
        messages.success(request, "Grade recorded successfully!")
    
    redirect_url = request.POST.get('redirect_url', 'dashboard')
    return redirect(redirect_url)

@login_required
def course_forum(request, course_pk):
    """Show course forum with topics"""
    course = get_object_or_404(Course, pk=course_pk)
    
    # Check if user is enrolled in the course
    is_enrolled = False
    if request.user.is_authenticated and request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    # Check if user is the instructor
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    # Only enrolled students and instructors can access the forum
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to access the forum.")
        return redirect('course_detail', pk=course.pk)
    
    # Get forum for this course
    forum, created = Forum.objects.get_or_create(course=course)
    
    # Get topics for this forum
    topics = forum.topics.all().prefetch_related('author', 'posts')
    
    context = {
        'course': course,
        'forum': forum,
        'topics': topics
    }
    return render(request, 'core/course_forum.html', context)

@login_required
def create_topic(request, forum_pk):
    """Create a new topic in a forum"""
    forum = get_object_or_404(Forum, pk=forum_pk)
    course = forum.course
    
    # Check if user is enrolled in the course
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    # Check if user is the instructor
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    # Only enrolled students and instructors can create topics
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
            # Create notification for the instructor
            create_notification(
                recipient=course.instructor,
                title=f"New topic created: {topic.title}",
                message=f"{request.user.username} has created a new topic '{topic.title}' in course '{course.title}'.",
                notification_type='forum_post',
                related_course=course
            )
            # Log analytics event
            log_analytics_event(
                'forum_activity',
                course=course,
                user=request.user,
                value=1.0,
                metadata={'action': 'create_topic', 'topic_id': topic.id}
            )
            return redirect('topic_detail', topic_pk=topic.pk)
        else:
            messages.error(request, "Please fill in both title and content.")
    
    context = {
        'forum': forum,
        'course': course
    }
    return render(request, 'core/create_topic.html', context)

@login_required
def topic_detail(request, topic_pk):
    """Show topic with all its posts"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    forum = topic.forum
    course = forum.course
    
    # Check if user is enrolled in the course
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    # Check if user is the instructor
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    # Only enrolled students and instructors can access the topic
    if not (is_enrolled or is_instructor):
        messages.error(request, "You must be enrolled in the course to access this topic.")
        return redirect('course_forum', course_pk=course.pk)
    
    posts = topic.posts.all().prefetch_related('author')
    
    context = {
        'topic': topic,
        'forum': forum,
        'course': course,
        'posts': posts
    }
    return render(request, 'core/topic_detail.html', context)

@login_required
def create_post(request, topic_pk):
    """Create a new post in a topic"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    forum = topic.forum
    course = forum.course
    
    # Check if user is enrolled in the course
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    # Check if user is the instructor
    is_instructor = (request.user.role == 'instructor' and course.instructor == request.user)
    
    # Only enrolled students and instructors can create posts
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
            # Create notification for the topic author
            if post.topic.author != request.user:
                create_notification(
                    recipient=post.topic.author,
                    title=f"New reply to your topic: {post.topic.title}",
                    message=f"{request.user.username} replied to your topic '{post.topic.title}'",
                    notification_type='forum_post',
                    related_course=course
                )
            # Create notification for the instructor
            create_notification(
                recipient=course.instructor,
                title=f"New post in {post.topic.title}",
                message=f"{request.user.username} made a new post in topic '{post.topic.title}' in course '{course.title}'.",
                notification_type='forum_post',
                related_course=course
            )
            # Log analytics event
            log_analytics_event(
                'forum_activity',
                course=course,
                user=request.user,
                value=1.0,
                metadata={'action': 'create_post', 'post_id': post.id}
            )
            return redirect('topic_detail', topic_pk=topic.pk)
        else:
            messages.error(request, "Please enter content for your post.")
    
    return redirect('topic_detail', topic_pk=topic.pk)

@login_required
def generate_certificate(request, enrollment_pk):
    """Generate and download a certificate for course completion"""
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)
    
    # Check if user is the student who earned the certificate or instructor
    is_student = (request.user.role == 'student' and enrollment.student == request.user)
    is_instructor = (request.user.role == 'instructor' and enrollment.course.instructor == request.user)
    
    if not (is_student or is_instructor):
        messages.error(request, "You don't have permission to access this certificate.")
        return redirect('dashboard')
    
    # Check if course is completed (80% or more progress)
    if enrollment.progress_percentage() < 80:
        messages.error(request, "You must complete at least 80% of the course to earn a certificate.")
        return redirect('course_detail', pk=enrollment.course.pk)
    
    # Check if certificate already exists
    certificate, created = Certificate.objects.get_or_create(enrollment=enrollment)
    
    if created:
        # Certificate was just created
        messages.success(request, "Certificate generated successfully!")
        # Create notification for the student
        create_notification(
            recipient=enrollment.student,
            title=f"Certificate earned: {enrollment.course.title}",
            message=f"You have earned a certificate for completing the course '{enrollment.course.title}'.",
            notification_type='certificate_earned',
            related_course=enrollment.course
        )
        # Log analytics event
        log_analytics_event(
            'certificate_issuance',
            course=enrollment.course,
            user=enrollment.student,
            value=1.0,
            metadata={'action': 'generate_certificate', 'certificate_id': certificate.certificate_id}
        )
    
    # Generate PDF certificate
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Try to get course-specific template, fallback to global template
    try:
        template = enrollment.course.certificate_template
    except CertificateTemplate.DoesNotExist:
        # Create a default template if none exists
        template = CertificateTemplate.objects.create(
            course=enrollment.course,
            title="Certificate of Completion",
            description="This is to certify that the student has successfully completed the course."
        )
    
    # Use default values if template is not set
    title = template.title
    description = template.description
    font_size = template.font_size
    text_color = template.text_color
    
    # Convert hex color to RGB
    try:
        color_code = text_color.lstrip('#')
        r = int(color_code[:2], 16) / 255.0
        g = int(color_code[2:4], 16) / 255.0
        b = int(color_code[4:], 16) / 255.0
        text_color_obj = Color(r, g, b)
    except:
        text_color_obj = Color(0, 0, 0)  # Default black
    
    # Draw certificate background if available
    if template.background_image:
        try:
            p.drawImage(template.background_image.path, 0, 0, width, height)
        except:
            pass  # Ignore if image is not available
    
    # Draw certificate content
    p.setFont("Helvetica-Bold", font_size + 6)
    p.setFillColor(text_color_obj)
    p.drawCentredString(width/2.0, height - 2*inch, title)
    
    p.setFont("Helvetica", font_size)
    p.drawCentredString(width/2.0, height - 2.5*inch, description)
    
    p.setFont("Helvetica-Bold", font_size + 4)
    p.drawCentredString(width/2.0, height - 3.5*inch, enrollment.student.get_full_name() or enrollment.student.username)
    
    p.setFont("Helvetica", font_size)
    p.drawCentredString(width/2.0, height - 4*inch, f"for completing the course:")
    p.setFont("Helvetica-Bold", font_size + 2)
    p.drawCentredString(width/2.0, height - 4.5*inch, enrollment.course.title)
    
    p.setFont("Helvetica", font_size - 2)
    p.drawCentredString(width/2.0, height - 6*inch, f"Certificate ID: {certificate.certificate_id}")
    p.drawCentredString(width/2.0, height - 6.3*inch, f"Issued on: {certificate.issued_at.strftime('%B %d, %Y')}")
    
    p.setFont("Helvetica-Oblique", font_size - 4)
    p.drawCentredString(width/2.0, height - 7*inch, "Instructor: " + enrollment.course.instructor.get_full_name() or enrollment.course.instructor.username)
    
    p.showPage()
    p.save()
    
    # Get PDF value
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_id}.pdf"'
    
    return response

@login_required
def student_certificates(request):
    """Show student's certificates"""
    if request.user.role != 'student':
        return redirect('dashboard')
    
    # Get all certificates for this student
    certificates = Certificate.objects.filter(
        enrollment__student=request.user,
        is_active=True
    ).select_related('enrollment__course', 'enrollment__student')
    
    context = {
        'certificates': certificates
    }
    return render(request, 'core/student_certificates.html', context)

@login_required
def instructor_certificates(request, course_pk):
    """Show certificates for students in a specific course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    # Get certificates for this course
    certificates = Certificate.objects.filter(
        enrollment__course=course,
        is_active=True
    ).select_related('enrollment__student')
    
    context = {
        'course': course,
        'certificates': certificates
    }
    return render(request, 'core/instructor_certificates.html', context)

@login_required
def manage_certificate_template(request, course_pk):
    """Manage certificate template for a course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role != 'instructor' or course.instructor != request.user:
        return redirect('dashboard')
    
    try:
        template = course.certificate_template
    except CertificateTemplate.DoesNotExist:
        template = CertificateTemplate.objects.create(course=course)
    
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, "Certificate template updated successfully!")
            return redirect('manage_certificate_template', course_pk=course.pk)
    else:
        form = CertificateTemplateForm(instance=template)
    
    context = {
        'form': form,
        'course': course,
        'template': template
    }
    return render(request, 'core/manage_certificate_template.html', context)

@login_required
def check_certificate_eligibility(request, course_pk):
    """Check if user is eligible for certificate"""
    course = get_object_or_404(Course, pk=course_pk)
    
    # Check if user is enrolled in the course
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        messages.error(request, "You must be enrolled in the course to check certificate eligibility.")
        return redirect('course_detail', pk=course.pk)
    
    progress = enrollment.progress_percentage()
    
    context = {
        'course': course,
        'progress': progress,
        'is_eligible': progress >= 80
    }
    return render(request, 'core/certificate_eligibility.html', context)

@login_required
def notifications_list(request):
    """Show user's notifications"""
    notifications = Notification.objects.filter(recipient=request.user).select_related('related_course')
    
    # Mark all notifications as read when viewing
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications
    }
    return render(request, 'core/notifications_list.html', context)

@login_required
def notification_preference(request):
    """Manage notification preferences"""
    # Get or create notification preferences for the user
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully!")
            return redirect('notification_preference')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form
    }
    return render(request, 'core/notification_preference.html', context)

@login_required
def mark_notification_read(request, notification_pk):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, pk=notification_pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to the original page or notifications list
    redirect_url = request.GET.get('redirect_url', 'notifications_list')
    return redirect(redirect_url)

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read!")
    
    # Redirect to the original page or notifications list
    redirect_url = request.GET.get('redirect_url', 'notifications_list')
    return redirect(redirect_url)

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    # Get analytics data for the dashboard
    if request.user.role == 'instructor':
        # For instructors, get data for their courses
        courses = Course.objects.filter(instructor=request.user)
        analytics_data = Analytics.objects.filter(course__in=courses)
    else:
        # For admins, get all data
        analytics_data = Analytics.objects.all()
    
    # Calculate key metrics
    total_enrollments = analytics_data.filter(analytics_type='course_enrollment').count()
    total_completions = analytics_data.filter(analytics_type='course_completion').count()
    total_lessons_completed = analytics_data.filter(analytics_type='lesson_completion').count()
    total_quiz_attempts = analytics_data.filter(analytics_type='quiz_attempt').count()
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_analytics = analytics_data.filter(date_recorded__gte=thirty_days_ago)
    
    # Prepare data for charts
    # Enrollment trend data
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
        'enrollment_trend': list(reversed(enrollment_trend))
    }
    return render(request, 'core/analytics_dashboard.html', context)

@login_required
def generate_report(request):
    """Generate custom reports"""
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            # Generate report data based on type
            report_data = generate_report_data(report.report_type, form.cleaned_data['start_date'], form.cleaned_data['end_date'])
            report.data = report_data
            
            report.save()
            messages.success(request, f"Report '{report.title}' generated successfully!")
            return redirect('view_report', report_pk=report.pk)
    else:
        form = ReportGenerationForm()
    
    context = {
        'form': form
    }
    return render(request, 'core/generate_report.html', context)

@login_required
def view_report(request, report_pk):
    """View a specific report"""
    report = get_object_or_404(Report, pk=report_pk)
    
    # Check permissions
    if request.user.role not in ['admin'] and report.generated_by != request.user:
        return redirect('dashboard')
    
    context = {
        'report': report
    }
    return render(request, 'core/view_report.html', context)

@login_required
def course_analytics(request, course_pk):
    """Analytics for a specific course"""
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.user.role == 'instructor' and course.instructor != request.user:
        return redirect('dashboard')
    elif request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    # Get course-specific analytics
    analytics_data = Analytics.objects.filter(course=course)
    
    # Calculate course metrics
    total_enrollments = analytics_data.filter(analytics_type='course_enrollment').count()
    total_completions = analytics_data.filter(analytics_type='course_completion').count()
    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = (total_completions / total_enrollments) * 100
    
    # Get student progress data
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    student_progress = []
    for enrollment in enrollments:
        progress = enrollment.progress_percentage()
        student_progress.append({
            'student': enrollment.student.username,
            'progress': progress,
            'completed_lessons': enrollment.completed_lessons.count()
        })
    
    # Get lesson completion data
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
        'lesson_completion_data': lesson_completion_data
    }
    return render(request, 'core/course_analytics.html', context)

@login_required
def student_analytics(request, student_pk):
    """Analytics for a specific student"""
    student = get_object_or_404(CustomUser, pk=student_pk)
    
    if request.user.role not in ['instructor', 'admin']:
        return redirect('dashboard')
    
    # Check if user can view this student's data
    if request.user.role == 'instructor':
        # Instructor can only see students in their courses
        student_courses = Course.objects.filter(instructor=request.user, enrollments__student=student).distinct()
        if not student_courses.exists():
            return redirect('dashboard')
    
    # Get student's enrollments and progress
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    
    # Calculate overall metrics
    total_courses = enrollments.count()
    completed_courses = 0
    total_progress = 0
    
    course_data = []
    for enrollment in enrollments:
        progress = enrollment.progress_percentage()
        total_progress += progress
        
        if progress >= 80:  # Considered completed if 80% or more
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
    
    # Get student's grades
    grades = Grade.objects.filter(enrollment__student=student).select_related('enrollment__course')
    
    context = {
        'student': student,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'average_progress': average_progress,
        'course_data': course_data,
        'grades': grades
    }
    return render(request, 'core/student_analytics.html', context)

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
        # Course performance data
        courses = Course.objects.all()
        data['courses'] = []
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            total_enrolled = enrollments.count()
            total_completed = 0
            avg_progress = 0
            
            for enrollment in enrollments:
                progress = enrollment.progress_percentage()
                if progress >= 80:  # 80% or more considered completed
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
        # Student progress data
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
        # User engagement data
        data['total_users'] = CustomUser.objects.count()
        data['active_students'] = CustomUser.objects.filter(role='student').count()
        data['instructors'] = CustomUser.objects.filter(role='instructor').count()
        
        # Activity in the date range
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
        # Grade distribution data
        grades = Grade.objects.filter(
            date_recorded__date__gte=start_date,
            date_recorded__date__lte=end_date
        )
        
        data['grade_stats'] = {
            'total_grades': grades.count(),
            'avg_score': grades.aggregate(Avg('score'))['score__avg'] or 0,
            'avg_max_points': grades.aggregate(Avg('max_points'))['max_points__avg'] or 0,
        }
        
        # Distribution by grade type
        data['by_type'] = {}
        for grade_type in ['quiz', 'assignment', 'exam']:
            type_grades = grades.filter(grade_type=grade_type)
            data['by_type'][grade_type] = {
                'count': type_grades.count(),
                'avg_score': type_grades.aggregate(Avg('score'))['score__avg'] or 0,
            }
    
    elif report_type == 'certificate_issuance':
        # Certificate issuance data
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

def logout_view(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course, Category, Module, Lesson, Enrollment, Quiz, Question, AnswerOption, QuizAttempt, QuizAnswer, Assignment, Submission, Grade, CourseGrade

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'created_at', 'is_active')
    list_filter = ('category', 'instructor', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'instructor', 'category', 'thumbnail')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'order', 'created_at')
    list_filter = ('content_type', 'module__course')
    search_fields = ('title', 'module__title', 'module__course__title')
    ordering = ('module', 'order')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'get_progress')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('student__username', 'course__title')
    
    def get_progress(self, obj):
        return f"{obj.progress_percentage()}%"
    get_progress.short_description = 'Progress'

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'time_limit', 'max_attempts', 'passing_score')
    list_filter = ('lesson__module__course',)
    search_fields = ('title', 'lesson__title')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'points', 'order')
    list_filter = ('quiz__lesson__module__course', 'question_type')
    search_fields = ('text', 'quiz__title')

@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('question__quiz__lesson__module__course', 'is_correct')
    search_fields = ('text', 'question__text')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'attempt_number', 'score', 'completed_at')
    list_filter = ('quiz__lesson__module__course', 'student', 'completed_at')
    search_fields = ('student__username', 'quiz__title')

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('quiz_attempt', 'question', 'is_correct')
    list_filter = ('quiz_attempt__quiz__lesson__module__course', 'is_correct')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'due_date', 'max_points')
    list_filter = ('lesson__module__course', 'due_date')
    search_fields = ('title', 'lesson__title')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'grade')
    list_filter = ('assignment__lesson__module__course', 'student', 'submitted_at')
    search_fields = ('student__username', 'assignment__title')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'get_student_name', 'get_course_name', 'score', 'max_points', 'percentage', 'grade_type', 'date_recorded')
    list_filter = ('grade_type', 'date_recorded', 'enrollment__course')
    search_fields = ('enrollment__student__username', 'enrollment__course__title')
    
    def get_student_name(self, obj):
        return obj.enrollment.student.username
    get_student_name.short_description = 'Student'
    
    def get_course_name(self, obj):
        return obj.enrollment.course.title
    get_course_name.short_description = 'Course'

@admin.register(CourseGrade)
class CourseGradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'final_grade', 'letter_grade')
    list_filter = ('enrollment__course', 'letter_grade')
    search_fields = ('enrollment__student__username', 'enrollment__course__title')
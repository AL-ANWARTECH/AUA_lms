from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course, Category, Module, Lesson, Enrollment, Quiz, Question, AnswerOption, QuizAttempt, QuizAnswer, Assignment, Submission, Grade, CourseGrade, Forum, Topic, Post, TopicTag, TopicTagging, Certificate, CertificateTemplate, Notification, NotificationPreference, Analytics, Report, DashboardWidget

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

@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'is_active')
    list_filter = ('is_active', 'course__title')
    search_fields = ('course__title', 'title')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'author', 'created_at', 'is_pinned', 'is_closed')
    list_filter = ('forum__course__title', 'author', 'is_pinned', 'is_closed', 'created_at')
    search_fields = ('title', 'content', 'author__username')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'topic', 'created_at', 'is_edited')
    list_filter = ('topic__forum__course__title', 'author', 'created_at')
    search_fields = ('content', 'author__username', 'topic__title')

@admin.register(TopicTag)
class TopicTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    list_filter = ('name',)
    search_fields = ('name',)

@admin.register(TopicTagging)
class TopicTaggingAdmin(admin.ModelAdmin):
    list_display = ('topic', 'tag')
    list_filter = ('topic__forum__course__title', 'tag__name')
    search_fields = ('topic__title', 'tag__name')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'get_student_name', 'get_course_name', 'issued_at', 'is_active')
    list_filter = ('is_active', 'issued_at', 'enrollment__course__title')
    search_fields = ('certificate_id', 'enrollment__student__username', 'enrollment__course__title')
    
    def get_student_name(self, obj):
        return obj.enrollment.student.username
    get_student_name.short_description = 'Student'
    
    def get_course_name(self, obj):
        return obj.enrollment.course.title
    get_course_name.short_description = 'Course'

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_course_name', 'is_active')
    list_filter = ('is_active', 'course__title')
    search_fields = ('title', 'course__title')
    
    def get_course_name(self, obj):
        return obj.course.title if obj.course else "Global Template"
    get_course_name.short_description = 'Course'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at', 'recipient__username')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at',)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'in_app_notifications', 'course_updates', 'grade_updates', 'forum_posts', 'assignment_due')
    list_filter = ('email_notifications', 'in_app_notifications', 'user__username')
    search_fields = ('user__username',)

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('analytics_type', 'course', 'user', 'date_recorded', 'value')
    list_filter = ('analytics_type', 'date_recorded', 'course__title', 'user__username')
    search_fields = ('course__title', 'user__username')
    readonly_fields = ('date_recorded',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'generated_at', 'is_active')
    list_filter = ('report_type', 'generated_at', 'generated_by__username', 'is_active')
    search_fields = ('title', 'generated_by__username')

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('widget_type', 'user', 'position', 'is_visible')
    list_filter = ('widget_type', 'user__username', 'is_visible')
    search_fields = ('user__username',)
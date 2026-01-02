from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses_taught')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'pk': self.pk})

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='text')
    content = models.TextField(blank=True)  # For text content
    video_url = models.URLField(blank=True, null=True)  # For video lessons
    file = models.FileField(upload_to='lesson_files/', blank=True, null=True)  # For PDFs
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit = models.IntegerField(help_text="Time limit in minutes", null=True, blank=True)
    max_attempts = models.IntegerField(default=1, help_text="Maximum number of attempts allowed")
    passing_score = models.FloatField(default=70.0, help_text="Minimum score percentage to pass")
    
    def __str__(self):
        return f"Quiz: {self.title} for {self.lesson.title}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    points = models.IntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q: {self.text[:50]}..."

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_options')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Option: {self.text[:30]}..."

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    attempt_number = models.PositiveIntegerField()
    score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_taken = models.IntegerField(help_text="Time taken in seconds", null=True, blank=True)
    
    class Meta:
        unique_together = ('quiz', 'student', 'attempt_number')
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Attempt #{self.attempt_number})"

class QuizAnswer(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)  # For short answer questions
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Answer to {self.question.text[:30]}..."

class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_lessons = models.ManyToManyField(Lesson, blank=True, related_name='completed_by')
    
    class Meta:
        unique_together = ('student', 'course')
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def progress_percentage(self):
        """Calculate completion percentage based on actual lessons"""
        total_lessons = self.course.lessons.count()  # Get actual lesson count
        completed_lessons = self.completed_lessons.count()
        if total_lessons == 0:
            return 0
        return round((completed_lessons / total_lessons) * 100, 2)

# Add a property to Course model to get all lessons
@property
def lessons(self):
    """Get all lessons in the course"""
    from django.db.models import Prefetch
    return Lesson.objects.filter(module__course=self)

# Add this to the Course class
Course.add_to_class('lessons', lessons)

class Assignment(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='assignment')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.IntegerField(default=100)
    
    def __str__(self):
        return f"Assignment: {self.title} for {self.lesson.title}"

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('assignment', 'student')
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True)
    score = models.FloatField()  # Actual points earned
    max_points = models.FloatField()  # Max possible points
    date_recorded = models.DateTimeField(auto_now_add=True)
    grade_type = models.CharField(max_length=20, choices=[
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
    ])
    
    def percentage(self):
        """Calculate percentage score"""
        if self.max_points > 0:
            return (self.score / self.max_points) * 100
        return 0
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.score}/{self.max_points}"

class CourseGrade(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='course_grade')
    final_grade = models.FloatField(null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    
    def calculate_final_grade(self):
        """Calculate final grade based on all assignments/quizzes"""
        grades = self.enrollment.grades.all()
        if not grades:
            return 0
        
        total_score = 0
        total_max = 0
        for grade in grades:
            total_score += grade.score
            total_max += grade.max_points
        
        if total_max > 0:
            return (total_score / total_max) * 100
        return 0
    
    def get_letter_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def save(self, *args, **kwargs):
        """Auto-calculate final grade and letter grade"""
        if not self.final_grade:
            self.final_grade = self.calculate_final_grade()
        if not self.letter_grade:
            self.letter_grade = self.get_letter_grade(self.final_grade)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.enrollment.course.title}: {self.letter_grade}"

class Forum(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='forum')
    title = models.CharField(max_length=200, default='Course Forum')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Forum: {self.course.title}"

class Topic(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='topics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title

class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Post by {self.author.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class TopicTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    
    def __str__(self):
        return self.name

class TopicTagging(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(TopicTag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('topic', 'tag')

class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.CharField(max_length=20, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Certificate for {self.enrollment.student.username} - {self.enrollment.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID
            import random
            import string
            self.certificate_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

class CertificateTemplate(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='certificate_template', null=True, blank=True)
    title = models.CharField(max_length=200, default="Certificate of Completion")
    description = models.TextField(default="This is to certify that the student has successfully completed the course.")
    background_image = models.ImageField(upload_to='certificates/backgrounds/', null=True, blank=True)
    font_size = models.IntegerField(default=14)
    text_color = models.CharField(max_length=7, default='#000000')  # Hex color
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        course_name = self.course.title if self.course else "Global Template"
        return f"Template for {course_name}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('course_update', 'Course Update'),
        ('grade_update', 'Grade Update'),
        ('forum_post', 'Forum Post'),
        ('assignment_due', 'Assignment Due'),
        ('certificate_earned', 'Certificate Earned'),
        ('enrollment', 'Enrollment'),
        ('general', 'General'),
    ]
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    related_module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True)
    related_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

class NotificationPreference(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    grade_updates = models.BooleanField(default=True)
    forum_posts = models.BooleanField(default=True)
    assignment_due = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"

class Analytics(models.Model):
    """Store analytics data for courses and users"""
    ANALYTICS_TYPES = [
        ('course_enrollment', 'Course Enrollment'),
        ('course_completion', 'Course Completion'),
        ('lesson_completion', 'Lesson Completion'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('assignment_submission', 'Assignment Submission'),
        ('forum_activity', 'Forum Activity'),
        ('user_engagement', 'User Engagement'),
    ]
    
    analytics_type = models.CharField(max_length=25, choices=ANALYTICS_TYPES)  # Increased max_length to 25
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    date_recorded = models.DateTimeField(auto_now_add=True)
    value = models.FloatField(default=1.0)
    metadata = models.JSONField(default=dict, blank=True)  # For additional data
    
    class Meta:
        ordering = ['-date_recorded']
    
    def __str__(self):
        return f"{self.analytics_type} - {self.course.title if self.course else 'N/A'} - {self.date_recorded.strftime('%Y-%m-%d')}"

class Report(models.Model):
    """Store generated reports"""
    REPORT_TYPES = [
        ('course_performance', 'Course Performance'),
        ('student_progress', 'Student Progress'),
        ('user_engagement', 'User Engagement'),
        ('system_usage', 'System Usage'),
        ('grade_distribution', 'Grade Distribution'),
        ('certificate_issuance', 'Certificate Issuance'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # Store report data as JSON
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.generated_by.username} - {self.generated_at.strftime('%Y-%m-%d')}"

class DashboardWidget(models.Model):
    """Configurable dashboard widgets for analytics"""
    WIDGET_TYPES = [
        ('enrollment_chart', 'Enrollment Chart'),
        ('progress_chart', 'Progress Chart'),
        ('grade_distribution', 'Grade Distribution'),
        ('recent_activities', 'Recent Activities'),
        ('user_statistics', 'User Statistics'),
        ('course_statistics', 'Course Statistics'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)  # Widget-specific configuration
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.widget_type} for {self.user.username}"

class AccessibilitySettings(models.Model):
    """Store accessibility preferences for users"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='accessibility_settings')
    high_contrast_mode = models.BooleanField(default=False)
    large_text_mode = models.BooleanField(default=False)
    reduced_motion_mode = models.BooleanField(default=False)
    screen_reader_optimized = models.BooleanField(default=True)
    keyboard_navigation_enabled = models.BooleanField(default=True)
    focus_indicator_enabled = models.BooleanField(default=True)
    caption_preference = models.BooleanField(default=True)
    audio_volume_level = models.IntegerField(default=50, help_text="Default volume level (0-100)")
    preferred_font_size = models.CharField(max_length=10, default='medium', choices=[
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('x-large', 'Extra Large'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Accessibility settings for {self.user.username}"

class AccessibilityAudit(models.Model):
    """Track accessibility compliance audits"""
    AUDIT_TYPES = [
        ('automated', 'Automated Scan'),
        ('manual', 'Manual Review'),
        ('user_feedback', 'User Feedback'),
        ('compliance_check', 'Compliance Check'),
    ]
    
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPES)
    performed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    findings = models.TextField()
    severity = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.audit_type} - {self.severity} - {'Resolved' if self.resolved else 'Pending'}"

class ScreenReaderContent(models.Model):
    """Alternative content for screen readers"""
    page_section = models.CharField(max_length=100, help_text="Name of the page section")
    content_type = models.CharField(max_length=50, choices=[
        ('navigation', 'Navigation'),
        ('form', 'Form'),
        ('media', 'Media'),
        ('data_table', 'Data Table'),
        ('chart', 'Chart'),
        ('other', 'Other'),
    ])
    alternative_text = models.TextField(help_text="Descriptive text for screen readers")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Screen reader content for {self.page_section}"

class KeyboardShortcut(models.Model):
    """Define keyboard shortcuts for common actions"""
    ACTION_CHOICES = [
        ('navigate_home', 'Navigate to Home'),
        ('open_menu', 'Open Menu'),
        ('search_focus', 'Focus Search'),
        ('skip_to_content', 'Skip to Content'),
        ('toggle_sidebar', 'Toggle Sidebar'),
        ('previous_item', 'Previous Item'),
        ('next_item', 'Next Item'),
        ('select_item', 'Select Item'),
        ('close_modal', 'Close Modal'),
        ('save_changes', 'Save Changes'),
        ('cancel_action', 'Cancel Action'),
    ]
    
    key_combination = models.CharField(max_length=20, help_text="e.g., Ctrl+S, Alt+F, Tab")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    is_global = models.BooleanField(default=True, help_text="Available on all pages")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.key_combination} - {self.action}"
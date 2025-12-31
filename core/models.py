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
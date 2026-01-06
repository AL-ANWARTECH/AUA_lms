from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import (
    Course, Module, Lesson, Quiz, Question, AnswerOption, 
    Assignment, Submission, Grade, Topic, Post, Category,
    CertificateTemplate, Report, DashboardWidget, 
    NotificationPreference, AccessibilitySettings
)

User = get_user_model()

# --- 1. USER REGISTRATION FORM ---
class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]
    
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential Address'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select', 'id': 'roleSelect'}))

    bio = forms.CharField(
        required=False, 
        label="Educational Background",
        widget=forms.Textarea(attrs={'class': 'form-control instructor-field', 'rows': 3, 'placeholder': 'Tell us about your education...'})
    )
    portfolio_website = forms.URLField(
        required=False, 
        widget=forms.URLInput(attrs={'class': 'form-control instructor-field', 'placeholder': 'https://yourportfolio.com'})
    )
    identity_document = forms.FileField(
        required=False, 
        label="Upload ID/CV (Optional)",
        widget=forms.FileInput(attrs={'class': 'form-control instructor-field'})
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role', 
            'phone_number', 'date_of_birth', 'address', 'profile_picture',
            'bio', 'portfolio_website', 'identity_document'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})

# --- 2. COURSE MANAGEMENT FORMS ---
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'thumbnail', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not Category.objects.exists() and 'category' in self.fields:
            self.fields.pop('category')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.instructor = self.user
        if commit:
            instance.save()
        return instance

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'content', 'video_url', 'file', 'duration', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- 3. QUIZ & ASSIGNMENT FORMS ---
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'max_attempts', 'passing_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option Text'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

AnswerOptionFormSet = forms.inlineformset_factory(
    Question, AnswerOption, form=AnswerOptionForm, 
    extra=4, max_num=10, can_delete=True
)

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'max_points']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file', 'submission_text']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'submission_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Text answer or link...'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# --- 4. FORUM & COMMUNICATION ---
class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

# --- 5. SYSTEM SETTINGS ---
class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['title', 'description', 'background_image', 'font_size', 'text_color', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'font_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReportGenerationForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    class Meta:
        model = Report
        fields = ['title', 'report_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
        }

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        fields = ['widget_type', 'position', 'is_visible', 'config']
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON Config'}),
        }

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['email_notifications', 'in_app_notifications', 'course_updates', 'grade_updates', 'forum_posts', 'assignment_due']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grade_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'forum_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assignment_due': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AccessibilitySettingsForm(forms.ModelForm):
    class Meta:
        model = AccessibilitySettings
        fields = [
            'high_contrast_mode', 'large_text_mode', 'reduced_motion_mode', 
            'screen_reader_optimized', 'keyboard_navigation_enabled', 
            'focus_indicator_enabled', 'caption_preference', 'audio_volume_level', 'preferred_font_size'
        ]
        widgets = {
            'high_contrast_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'large_text_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reduced_motion_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'screen_reader_optimized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'keyboard_navigation_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'focus_indicator_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'caption_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'audio_volume_level': forms.NumberInput(attrs={'class': 'form-range', 'type': 'range', 'min': 0, 'max': 100}),
            'preferred_font_size': forms.Select(attrs={'class': 'form-select'}),
        }

# --- 6. USER PROFILE UPDATE FORM ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'address', 'date_of_birth', 'profile_picture', 
            'bio', 'portfolio_website'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'portfolio_website': forms.URLInput(attrs={'class': 'form-control'}),
        }

# --- 7. CERTIFICATE CLAIM FORM (NEW) ---
class CertificateClaimForm(forms.Form):
    full_name = forms.CharField(
        max_length=200, 
        label="Name on Certificate",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': 'e.g. John Doe'
        }),
        help_text="Please verify the spelling. This is how it will appear on your certificate."
    )
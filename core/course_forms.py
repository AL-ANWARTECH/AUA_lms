from django import forms
from .models import Course, Module, Lesson, Category

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'thumbnail', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Introduction to Python Programming'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'What will students learn in this course?'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Publish Course Immediately',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Extract user before init
        super().__init__(*args, **kwargs)
        
        # Conditionally hide category if none exist
        if not Category.objects.exists():
            if 'category' in self.fields:
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
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Module 1: Basics'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'content', 'video_url', 'file', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lesson Title'}),
            'content_type': forms.Select(attrs={'class': 'form-select', 'id': 'contentTypeSelect'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter lesson text content...'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'video_url': 'Required if content type is "Video". Supports YouTube links.',
            'file': 'Required if content type is "PDF" or "File".',
        }
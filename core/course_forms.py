from django import forms
from .models import Course, Module, Lesson
from django.utils.translation import gettext_lazy as _

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'thumbnail', 'is_active']
        labels = {
            'title': _('Course Title'),
            'description': _('Description'),
            'category': _('Category'),
            'thumbnail': _('Thumbnail'),
            'is_active': _('Active'),
        }
        help_texts = {
            'title': _('Enter a descriptive title for your course'),
            'description': _('Provide a detailed description of the course content'),
            'thumbnail': _('Upload an image that represents your course'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Pass the user during initialization
        super().__init__(*args, **kwargs)
        
        # Only show categories field if categories exist
        from .models import Category
        if not Category.objects.exists():
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
        labels = {
            'title': _('Module Title'),
            'description': _('Description'),
            'order': _('Order'),
        }
        help_texts = {
            'title': _('Enter a title for this module'),
            'description': _('Provide a brief description of the module content'),
            'order': _('Position of this module in the course sequence'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'content', 'video_url', 'file', 'order']
        labels = {
            'title': _('Lesson Title'),
            'content_type': _('Content Type'),
            'content': _('Content'),
            'video_url': _('Video URL'),
            'file': _('File Upload'),
            'order': _('Order'),
        }
        help_texts = {
            'title': _('Enter a title for this lesson'),
            'content_type': _('Select the type of content for this lesson'),
            'content': _('Enter the text content for this lesson'),
            'video_url': _('Enter a URL to a video (YouTube, Vimeo, etc.)'),
            'file': _('Upload a file (PDF, document, etc.)'),
            'order': _('Position of this lesson in the module sequence'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
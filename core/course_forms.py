from django import forms
from .models import Course, Module, Lesson

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'thumbnail', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
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
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content_type', 'content', 'video_url', 'file', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
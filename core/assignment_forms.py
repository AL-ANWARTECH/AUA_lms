from django import forms
from .models import Assignment, Submission, Grade

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'max_points']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Final Project: Portfolio Website'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed instructions for students...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submission_file', 'submission_text']
        widgets = {
            'submission_file': forms.FileInput(attrs={'class': 'form-control'}),
            'submission_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Add any comments or paste a link to your work here...'
            }),
        }
        labels = {
            'submission_file': 'Upload File',
            'submission_text': 'Text / Link',
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['score', 'feedback']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Constructive feedback for the student...'
            }),
        }
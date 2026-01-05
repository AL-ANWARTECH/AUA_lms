from django import forms
from .models import Quiz, Question, AnswerOption

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'max_attempts', 'passing_score']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Mid-Term Assessment'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Instructions for students...'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Minutes (leave blank for unlimited)'
            }),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
        help_texts = {
            'time_limit': 'Time in minutes. Leave empty for no limit.',
            'passing_score': 'Percentage required to pass (e.g., 70).',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order']
        
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Enter the question text here...'
            }),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['text', 'is_correct', 'order']
        
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Answer Option'
            }),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Order'}),
        }

# FormSet for managing multiple answers within a single question view
AnswerOptionFormSet = forms.inlineformset_factory(
    Question, 
    AnswerOption, 
    form=AnswerOptionForm, 
    extra=4,       # Default to 4 options (A, B, C, D)
    max_num=10,    # Cap at 10 options
    can_delete=True
)
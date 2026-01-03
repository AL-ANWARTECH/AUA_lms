from django import forms
from .models import Quiz, Question, AnswerOption
from django.utils.translation import gettext_lazy as _

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'max_attempts', 'passing_score']
        labels = {
            'title': _('Quiz Title'),
            'description': _('Description'),
            'time_limit': _('Time Limit (minutes)'),
            'max_attempts': _('Maximum Attempts'),
            'passing_score': _('Passing Score (%)'),
        }
        help_texts = {
            'title': _('Enter a descriptive title for the quiz'),
            'description': _('Provide a brief description of the quiz'),
            'time_limit': _('Time limit in minutes (leave blank for no limit)'),
            'max_attempts': _('Maximum number of attempts allowed for this quiz'),
            'passing_score': _('Minimum score percentage required to pass'),
        }
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
        labels = {
            'text': _('Question Text'),
            'question_type': _('Question Type'),
            'points': _('Points'),
            'order': _('Order'),
        }
        help_texts = {
            'text': _('Enter the question text'),
            'question_type': _('Select the type of question'),
            'points': _('Points awarded for correct answer'),
            'order': _('Position of this question in the quiz'),
        }
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
        labels = {
            'text': _('Answer Text'),
            'is_correct': _('Is Correct'),
            'order': _('Order'),
        }
        help_texts = {
            'text': _('Enter the answer option text'),
            'is_correct': _('Check this box if this is the correct answer'),
            'order': _('Position of this answer option'),
        }
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

AnswerOptionFormSet = forms.inlineformset_factory(
    Question, 
    AnswerOption, 
    form=AnswerOptionForm, 
    extra=4,
    max_num=10,
    can_delete=True,
    labels={
        'text': _('Answer Text'),
        'is_correct': _('Is Correct'),
        'order': _('Order'),
    }
)
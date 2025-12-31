from django import forms
from .models import Quiz, Question, AnswerOption

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'max_attempts', 'passing_score']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }

class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 1}),
        }

AnswerOptionFormSet = forms.inlineformset_factory(
    Question, 
    AnswerOption, 
    form=AnswerOptionForm, 
    extra=4,
    max_num=10,
    can_delete=True
)
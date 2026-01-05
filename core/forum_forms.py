from django import forms
from .models import Topic, Post

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'What is this discussion about?'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6, 
                'placeholder': 'Elaborate on your question or topic to help others understand...'
            }),
        }
        
        help_texts = {
            'title': 'Keep it short and descriptive.',
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Type your reply here... Be respectful and constructive.'
            }),
        }
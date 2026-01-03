from django import forms
from .models import Assignment
from django.utils.translation import gettext_lazy as _

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'max_points']
        labels = {
            'title': _('Assignment Title'),
            'description': _('Description'),
            'due_date': _('Due Date'),
            'max_points': _('Maximum Points'),
        }
        help_texts = {
            'title': _('Enter a descriptive title for the assignment'),
            'description': _('Provide detailed instructions for the assignment'),
            'due_date': _('Set the deadline for the assignment'),
            'max_points': _('Maximum points that can be earned'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications', 
            'in_app_notifications', 
            'course_updates', 
            'grade_updates', 
            'forum_posts', 
            'assignment_due'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grade_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'forum_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assignment_due': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
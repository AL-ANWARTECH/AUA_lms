from django import forms
from .models import NotificationPreference
from django.utils.translation import gettext_lazy as _

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
        labels = {
            'email_notifications': _('Email Notifications'),
            'in_app_notifications': _('In-App Notifications'),
            'course_updates': _('Course Updates'),
            'grade_updates': _('Grade Updates'),
            'forum_posts': _('Forum Posts'),
            'assignment_due': _('Assignment Due Dates'),
        }
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grade_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'forum_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assignment_due': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
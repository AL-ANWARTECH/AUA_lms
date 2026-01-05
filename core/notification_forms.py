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
            # 'form-check-input' works with the form-switch class in Bootstrap 5
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grade_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'forum_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assignment_due': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'email_notifications': 'Email Alerts',
            'in_app_notifications': 'In-App Bell',
            'course_updates': 'Course Content',
            'grade_updates': 'Grades & Feedback',
            'forum_posts': 'Discussion Replies',
            'assignment_due': 'Deadlines',
        }

        help_texts = {
            'email_notifications': 'Receive critical updates via your registered email address.',
            'grade_updates': 'Get notified immediately when an instructor grades your work.',
            'assignment_due': 'Receive reminders 24 hours before an assignment is due.',
        }
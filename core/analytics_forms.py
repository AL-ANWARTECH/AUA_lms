from django import forms
from .models import Report, DashboardWidget
from django.utils.translation import gettext_lazy as _

class ReportGenerationForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label=_('Start Date'))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label=_('End Date'))
    
    class Meta:
        model = Report
        fields = ['title', 'report_type']
        labels = {
            'title': _('Report Title'),
            'report_type': _('Report Type'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
        }

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget  # This should match your model name
        fields = ['widget_type', 'position', 'is_visible', 'config']
        labels = {
            'widget_type': _('Widget Type'),
            'position': _('Position'),
            'is_visible': _('Is Visible'),
            'config': _('Configuration'),
        }
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
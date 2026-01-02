from django import forms
from .models import Report, DashboardWidget

class ReportGenerationForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Report
        fields = ['title', 'report_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
        }

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        fields = ['widget_type', 'position', 'is_visible', 'config']
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
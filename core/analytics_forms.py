from django import forms
from .models import Report, DashboardWidget

class ReportGenerationForm(forms.ModelForm):
    # Extra fields for filtering (not directly on the model, but used during generation)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="Start Date"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="End Date"
    )
    
    class Meta:
        model = Report
        fields = ['title', 'report_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Monthly Enrollment Stats'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
        }

class DashboardWidgetForm(forms.ModelForm):
    class Meta:
        model = DashboardWidget
        fields = ['widget_type', 'position', 'is_visible', 'config']
        
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'config': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': '{"limit": 5, "chart_type": "bar"}' # JSON hint
            }),
        }
        
        help_texts = {
            'config': 'Enter optional configuration in valid JSON format.',
            'position': 'Order in which this widget appears (lower numbers first).',
        }
from django import forms
from .models import CertificateTemplate

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['title', 'description', 'background_image', 'font_size', 'text_color', 'is_active']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'e.g., Certificate of Completion'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'e.g., This certifies that {{ student_name }} has successfully completed...'
            }),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'font_size': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Default: 120'
            }),
            # Native Color Picker Widget
            'text_color': forms.TextInput(attrs={
                'class': 'form-control form-control-color', 
                'type': 'color', 
                'title': 'Choose text color'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        help_texts = {
            'description': 'You can use placeholders like {{ student }} and {{ course }} in the text.',
            'font_size': 'Size of the student name font in pixels.',
        }
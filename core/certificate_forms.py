from django import forms
from .models import CertificateTemplate

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['title', 'description', 'background_image', 'font_size', 'text_color', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
        }
from django import forms
from .models import CertificateTemplate
from django.utils.translation import gettext_lazy as _

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['title', 'description', 'background_image', 'font_size', 'text_color', 'is_active']
        labels = {
            'title': _('Certificate Title'),
            'description': _('Description'),
            'background_image': _('Background Image'),
            'font_size': _('Font Size'),
            'text_color': _('Text Color'),
            'is_active': _('Active'),
        }
        help_texts = {
            'description': _('The description that appears on the certificate'),
            'background_image': _('Optional background image for the certificate'),
            'font_size': _('Font size for the certificate text'),
            'text_color': _('Color of the text on the certificate'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'font_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
from django import forms
from .models import AccessibilitySettings

class AccessibilitySettingsForm(forms.ModelForm):
    class Meta:
        model = AccessibilitySettings
        fields = [
            'high_contrast_mode',
            'large_text_mode',
            'reduced_motion_mode',
            'screen_reader_optimized',
            'keyboard_navigation_enabled',
            'focus_indicator_enabled',
            'caption_preference',
            'audio_volume_level',
            'preferred_font_size'
        ]
        widgets = {
            'high_contrast_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'large_text_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reduced_motion_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'screen_reader_optimized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'keyboard_navigation_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'focus_indicator_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'caption_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'audio_volume_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'preferred_font_size': forms.Select(attrs={'class': 'form-select'}),
        }
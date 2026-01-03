from django import forms
from .models import AccessibilitySettings
from django.utils.translation import gettext_lazy as _

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
        labels = {
            'high_contrast_mode': _('High Contrast Mode'),
            'large_text_mode': _('Large Text Mode'),
            'reduced_motion_mode': _('Reduced Motion Mode'),
            'screen_reader_optimized': _('Screen Reader Optimized'),
            'keyboard_navigation_enabled': _('Keyboard Navigation Enabled'),
            'focus_indicator_enabled': _('Focus Indicators Enabled'),
            'caption_preference': _('Show Captions for Media'),
            'audio_volume_level': _('Audio Volume Level'),
            'preferred_font_size': _('Preferred Font Size'),
        }
        help_texts = {
            'audio_volume_level': _('Default volume level for media content (0-100)'),
        }
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
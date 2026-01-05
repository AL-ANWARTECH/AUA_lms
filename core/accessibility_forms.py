from django import forms
from .models import AccessibilitySettings

class AccessibilitySettingsForm(forms.ModelForm):
    class Meta:
        model = AccessibilitySettings
        fields = [
            'high_contrast_mode',
            'large_text_mode',
            'preferred_font_size',
            'reduced_motion_mode',
            'screen_reader_optimized',
            'keyboard_navigation_enabled',
            'focus_indicator_enabled',
            'caption_preference',
            'audio_volume_level',
        ]
        
        # User-friendly labels
        labels = {
            'high_contrast_mode': 'Enable High Contrast',
            'large_text_mode': 'Use Large Text',
            'preferred_font_size': 'Font Size Preference',
            'reduced_motion_mode': 'Reduce Animations',
            'screen_reader_optimized': 'Screen Reader Optimization',
            'keyboard_navigation_enabled': 'Enhanced Keyboard Navigation',
            'focus_indicator_enabled': 'Visible Focus Indicators',
            'caption_preference': 'Always Show Captions',
            'audio_volume_level': 'Default Volume Level',
        }

        # Explanatory text for the user
        help_texts = {
            'high_contrast_mode': 'Increases the contrast between text and background for better readability.',
            'large_text_mode': 'Scales up the base text size across the platform.',
            'reduced_motion_mode': 'Minimizes UI animations and transitions.',
            'screen_reader_optimized': 'Adds additional ARIA labels and structural hints for screen readers.',
            'focus_indicator_enabled': 'Adds a thick border around selected elements to make navigation easier.',
            'caption_preference': 'Automatically enables subtitles for video lessons when available.',
        }

        widgets = {
            'high_contrast_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'large_text_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reduced_motion_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'screen_reader_optimized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'keyboard_navigation_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'focus_indicator_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'caption_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Using an HTML5 Range Slider for volume
            'audio_volume_level': forms.NumberInput(attrs={
                'class': 'form-range', 
                'type': 'range', 
                'min': '0', 
                'max': '100',
                'step': '5'
            }),
            
            'preferred_font_size': forms.Select(attrs={'class': 'form-select'}),
        }
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('student', _('Student')),
        ('instructor', _('Instructor')),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label=_('Role'))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
        labels = {
            'username': _('Username'),
            'email': _('Email Address'),
        }
        help_texts = {
            'username': _('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True  # Make email required
        self.fields['password1'].label = _('Password')
        self.fields['password2'].label = _('Password Confirmation')
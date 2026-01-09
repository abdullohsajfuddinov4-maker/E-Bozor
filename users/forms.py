from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name',
            'username',
            'email',
            'password1',
            'password2',
        )


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'tg_username',
            'phone_number',
            'avatar',
        )

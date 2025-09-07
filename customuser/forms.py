# customuser/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Profile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 '
            'border '
            'border-gray-300 '
            'rounded-md shadow-sm '
            'focus:outline-none '
            'focus:ring-indigo-500 '
            'focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )
    username = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 '
            'border '
            'border-gray-300 '
            'rounded-md shadow-sm '
            'focus:outline-none '
            'focus:ring-indigo-500 '
            'focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Username (optional)',
            'autocomplete': 'username',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 '
            'border '
            'border-gray-300 '
            'rounded-md shadow-sm '
            'focus:outline-none '
            'focus:ring-indigo-500 '
            'focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Enter password',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 '
            'border '
            'border-gray-300 '
            'rounded-md shadow-sm '
            'focus:outline-none '
            'focus:ring-indigo-500 '
            'focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        })
    )
    
    # Optional: Terms and conditions checkbox
    agree_to_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 '
        'focus:ring-indigo-500 '
        'border-gray-300 rounded'}),
        label='I agree to the Terms of Service and Privacy Policy'
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip()
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError("This username is already taken.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validate_password(password1)
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        if commit:
            user.save()
        return user
    
class CustomUserLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 '
            'border'
            'border-gray-300'
            'rounded-lg'
            'focus:ring-2'
            'focus:ring-blue-500'
            'focus:border-blue-500',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3'
            'border'
            'border-gray-300'
            'rounded-lg'
            'focus:ring-2'
            'focus:ring-blue-500'
            'focus:border-blue-500',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500'}),
        label='Remember me'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'first_name', 'surname', 'date_of_birth', 
            'contact_number', 'profile_picture', 'bio'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'placeholder': 'First Name'
            }),
            'surname': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg '
                'focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'placeholder': 'Last Name'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg '
                'focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'type': 'date'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg '
                'focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'placeholder': '+27 XX XXX XXXX'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg '
                'focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 '
                'border '
                'border-gray-300 '
                'rounded-lg '
                'focus:ring-2 '
                'focus:ring-blue-500 '
                'focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
        }

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if contact_number:
            # Basic South African number validation
            import re
            # Remove spaces and common separators
            cleaned = re.sub(r'[\s\-\(\)]', '', contact_number)
            
            # Check if it's a valid SA number format
            if not re.match(r'^(\+27|0)[0-9]{9}$', cleaned):
                raise ValidationError(
                    'Please enter a valid South African phone number (e.g., +27 XX XXX XXXX or 0XX XXX XXXX)'
                )
        return contact_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            profile.check_completion()  # Update completion status
            profile.save()
        return profile


# Optional: Password reset form if you want custom styling
class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if not CustomUser.objects.filter(email=email).exists():
                raise ValidationError("No account found with this email address.")
        return email    
from django import forms
from .models import  Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model  = User
        fields = ['username','email','password1', 'password2']
        
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-controls' }),
            'email': forms.TextInput(attrs={'class':'form-controls' }),
            'password1': forms.TextInput(attrs={'class':'form-controls' }),
            'password2': forms.TextInput(attrs={'class':'form-controls' }),
        }
        
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model  = User
        fields = ['username', 'email']
        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = ['first_name', 'surname','profile_pic','phone','bio','address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'style': ' width: 160px;',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }
        



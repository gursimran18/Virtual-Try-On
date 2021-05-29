from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Order, Customer, VitonUploads



class AccountSettings(forms.ModelForm):
    """Form for the image model"""
    class Meta:
        model = Customer
        fields = ['name', 'image']

class CreateUserForm(UserCreationForm):
	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']

class Viton(forms.ModelForm):
    """Form for the image model"""
    class Meta:
        model = VitonUploads
        fields = ['group', 'comments']
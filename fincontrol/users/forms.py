from django import forms
from .models import User

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'gender', 'age', 'position']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }

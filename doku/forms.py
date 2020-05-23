from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput
from .models import Zug


class ZugForm(ModelForm):
    class Meta:
        model = Zug
        fields = '__all__'
        widgets = {
            'Farbe': TextInput(attrs={'type': 'color'}),
        }
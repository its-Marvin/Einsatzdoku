from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput
from .models import Zug, Ort


class ZugForm(ModelForm):
    class Meta:
        model = Zug
        fields = '__all__'
        widgets = {
            'Farbe': TextInput(attrs={'type': 'color'}),
        }


class OrtForm(ModelForm):
    class Meta:
        model = Ort
        fields = '__all__'
        widgets = {
            'Farbe': TextInput(attrs={'type': 'color'}),
        }
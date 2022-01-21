from datetime import datetime

from django import forms

from apps.persona.models import Persona


class Formulario(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Persona.objects.filter(status=True)[0:10], widget=forms.Select(attrs={'class': 'form-control select2'}))
    fecha = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'disabled': True}), initial=datetime.now().date().strftime('%Y-%m-%d'))
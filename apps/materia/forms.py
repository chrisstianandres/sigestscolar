from django import forms
from django.forms import TextInput
from .models import Materia


class Formulario(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['nombre'].widget = TextInput(
                attrs={'placeholder': 'Ingrese el nombre de la materia', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['identificacion'].widget = TextInput(
                attrs={'placeholder': 'Ingrese un codigo unico para la materia', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['alias'].widget = TextInput(
                attrs={'placeholder': 'Ingrese un alias', 'class': 'form-control', 'autocomplete': 'off'})

    class Meta:
        model = Materia
        fields = ['identificacion', 'nombre', 'alias']
        labels = {'identificacion': 'Codigo', 'nombre': 'Nombre', 'alias': 'Alias'}
        widgets = {'nombre': forms.TextInput(), 'alias': forms.TextInput(), 'identificacion': forms.TextInput()}

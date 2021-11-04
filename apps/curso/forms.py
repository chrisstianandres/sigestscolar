from django import forms
from django.forms import TextInput
from .models import Curso


class Formulario(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['nombre'].widget = TextInput(
                attrs={'placeholder': 'Ingrese el nombre del curso', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['descripcion'].widget = TextInput(
                attrs={'placeholder': 'Ingrese una descripcion', 'class': 'form-control', 'autocomplete': 'off'})
        # habilitar, desabilitar, y mas

    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion']
        labels = {'nombre': 'Nombre', 'descripcion': 'Descripcion'}
        widgets = {'nombre': forms.TextInput(), 'descripcion': forms.TextInput()}

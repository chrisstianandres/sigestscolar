from django import forms
from django.forms import TextInput
from .models import Producto


class Formulario(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['nombre'].widget = TextInput(
                attrs={'placeholder': 'Ingrese el nombre del producto', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['descripcion'].widget = TextInput(
                attrs={'placeholder': 'Ingrese un ', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['alias'].widget = TextInput(
                attrs={'placeholder': 'Ingrese un alias', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['codigo'].widget = TextInput(
                attrs={'placeholder': 'Ingrese un codigo unico para el producto', 'class': 'form-control',
                       'autocomplete': 'off'})
            self.fields['codigo'].initial = ''

    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'alias', 'descripcion']
        labels = {'codigo': 'Codigo', 'nombre': 'Nombre', 'alias': 'Alias', 'descripcion': 'Descripcion'}
        widgets = {'nombre': forms.TextInput(), 'alias': forms.TextInput(), 'codigo': forms.TextInput()}

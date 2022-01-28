from django import forms
from django.forms import TextInput

from apps.empresa.models import Empresa


class Formulario(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
    #         self.fields['nombre'].widget = TextInput(
    #             attrs={'placeholder': 'Ingrese el nombre del producto', 'class': 'form-control', 'autocomplete': 'off'})
    #         self.fields['descripcion'].widget = TextInput(
    #             attrs={'placeholder': 'Ingrese un ', 'class': 'form-control', 'autocomplete': 'off'})
    #         self.fields['alias'].widget = TextInput(
    #             attrs={'placeholder': 'Ingrese un alias', 'class': 'form-control', 'autocomplete': 'off'})
    #         self.fields['codigo'].widget = TextInput(
    #             attrs={'placeholder': 'Ingrese un codigo unico para el producto', 'class': 'form-control',
    #                    'autocomplete': 'off'})
    #         self.fields['valor'].widget = TextInput(
    #             attrs={'class': 'form-control', 'min': 1, 'max': 100000000, 'autocomplete': 'off'})
    #         self.fields['codigo'].initial = ''

    class Meta:
        model = Empresa
        fields = ['nombre', 'descripcioncorta', 'direccion', 'mision', 'vision', 'telefono', 'telefono2', 'telefono3',
                  'ruc', 'email', 'iva']
        # labels = {'codigo': 'Codigo', 'nombre': 'Nombre', 'alias': 'Alias',
        #           'descripcion': 'Descripcion', 'talla': 'Talla', 'valor': 'Valor'}
        # widgets = {'nombre': forms.TextInput(), 'alias': forms.TextInput(), 'codigo': forms.TextInput(),
        #            'valor': forms.NumberInput()}


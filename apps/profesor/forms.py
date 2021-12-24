from django import forms
from django.forms import TextInput, Select, ModelChoiceField
from .distributivodocente import MateriaAsignada
from .models import Profesor


class Formulario(forms.ModelForm):
    # constructor
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in self.Meta.fields:
    #         self.fields[field].widget.attrs.update({
    #             'class': 'form-control'
    #         })
    #         self.fields['profesor'].widget = ModelChoiceField()

    class Meta:
        model = MateriaAsignada
        fields = ['profesor']
        labels = {'profesor': 'Docente'}

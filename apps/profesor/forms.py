from django import forms
from django.forms import TextInput, Select, ModelChoiceField
from .distributivodocente import MateriaAsignada
from .models import Profesor
from ..curso.models import CursoMateria
from ..paralelo.models import Paralelo
from ..periodo.models import PeriodoLectivo


class Formulario(forms.Form):
    # # constructor
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in self.Meta.fields:
    #         self.fields[field].widget.attrs.update({'class': 'form-control'})
    #         # self.fields['profesor'].widget = forms.ModelChoiceField(queryset=Profesor.objects.filter(status=True)[0:10])
    #         self.fields['profesor'].attrs = {'class': 'form-control select2'}
    #
    # class Meta:
    #     model = MateriaAsignada
    #     fields = ['profesor']
    #     labels = {'profesor': 'Docente'}
    profesor = forms.ModelChoiceField(queryset=Profesor.objects.filter(status=True)[0:10], widget=forms.Select(attrs={'class': 'form-control select2'}))
    periodo = forms.ModelChoiceField(queryset=PeriodoLectivo.objects.filter(status=True)[0:10], widget=forms.Select(attrs={'class': 'form-control select2'}))
    curso = forms.CharField(widget=forms.Select(attrs={'class': 'form-control select2', 'placeholder': 'Selecciona un curso'}), label='Curso')
    paralelo = forms.CharField(widget=forms.Select(attrs={'class': 'form-control select2', 'placeholder': 'Selecciona un paralelo', 'multiple': 'multiple'}))


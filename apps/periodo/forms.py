from datetime import datetime

from django import forms
from django.db.models import Q
from django.forms import TextInput, Select
from .models import PeriodoLectivo


class Formulario(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['nombre'].widget = TextInput(
                attrs={'placeholder': 'Ingrese el nombre del periodo', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['desde'].widget = TextInput(
                attrs={'placeholder': 'Ingrese la fecha de inicio del periodo', 'class': 'form-control ', 'autocomplete': 'off'})
            self.fields['hasta'].widget = TextInput(
                attrs={'placeholder': 'Ingrese la fecha de fin del periodo', 'class': 'form-control', 'autocomplete': 'off'})
            self.fields['anio'].widget = Select(choices=self.years(),
                attrs={'placeholder': 'Ingrese el al que corresponde el periodo', 'class': 'form-control', 'autocomplete': 'off'})

    class Meta:
        model = PeriodoLectivo
        fields = ['nombre', 'desde', 'hasta', 'anio', 'inicioactividades']
        labels = {'nombre': 'Nombre', 'desde': 'Desde', 'hasta': 'Hasta', 'anio': 'Año', 'inicioactividades': 'Inicio de actividades'}
        widgets = {'nombre': forms.TextInput(), 'desde': forms.TextInput(), 'hasta': forms.TextInput(), 'inicioactividades': forms.TextInput()}

    def clean(self):
        f = super()
        u = f.save(commit=False)
        name = self.cleaned_data['nombre']
        start = self.cleaned_data['desde']
        end = self.cleaned_data['hasta']
        inicioactividades = self.cleaned_data['inicioactividades']
        if u.pk is None:
            if PeriodoLectivo.objects.filter(nombre__iexact=name).exists():
                self.add_error('nombre', 'Ya existe un periodo con ese nombre')
        else:
            if PeriodoLectivo.objects.filter(nombre__iexact=name).exclude(id=u.pk).exists():
                self.add_error('nombre', 'Ya existe un periodo con ese nombre')
        if inicioactividades > end or inicioactividades < start:
            self.add_error('desde', 'No puede ingresar la fecha de inicio de actividades fuera del rango de fechas del periodo')
        if start >= end:
            self.add_error('desde', 'No puede ingresar la fecha de fin menor o igual a la fecha de inicio')
        else:
            total_dias = datetime(end.year, end.month, end.day) - datetime(start.year, start.month, start.day)
            if u.pk is None:
                if PeriodoLectivo.objects.filter(Q(desde__range=[start, end]) | Q(hasta__range=[start, end])).exists():
                    self.add_error('desde', 'Ya existe un periodo en ese rango de fechas')
                elif total_dias.days < 150:
                    self.add_error('hasta', 'Debe elegir un rango mayor a 150 dias')
            else:
                if PeriodoLectivo.objects.filter(Q(desde__range=[start, end]) | Q(hasta__range=[start, end])).exclude(
                        id=u.pk).exists():
                    self.add_error('desde', 'Ya existe un periodo en ese rango de fechas')
                elif total_dias.days < 150:
                    self.add_error('hasta', 'Debe elegir un rango mayor a 150 dias')

    def years(self):
        fecha = datetime.now().year
        anios = []
        for anio in range(0, 6):
            anio_fin = fecha + anio
            anios.append((anio_fin, str(anio_fin),))
        return anios


from django import forms
from django.forms import TextInput, Select
from .models import Curso, CursoParalelo
from ..paralelo.models import Paralelo
from ..periodo.models import PeriodoLectivo


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


class FormularioApertura(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['curso'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['curso'].initial = Curso.objects.filter(status=True)[:10]
            self.fields['paralelo'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['paralelo'].initial = Paralelo.objects.filter(status=True)[:10]
            self.fields['periodo'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['periodo'].initial = PeriodoLectivo.objects.filter(status=True)[:10]

    class Meta:
        model = CursoParalelo
        fields = ['periodo', 'curso', 'paralelo', 'cupo']
        labels = {'curso': 'Curso', 'paralelo': 'Paralelo', 'periodo': 'Periodo'}
        # widgets = {'curso': forms.Select(), 'paralelo': forms.Select(), 'periodo': forms.Select()}

    def clean(self):
        f = super()
        u = f.save(commit=False)
        periodo = self.cleaned_data['periodo']
        curso = self.cleaned_data['curso']
        paralelo = self.cleaned_data['paralelo']
        if u.pk is None:
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso, paralelo_id=paralelo).exists():
                self.add_error('paralelo', 'Ya existe ese paralelo en el curso y periodo seleccionado')
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso).exists():
                self.add_error('curso', 'Ya existe ese curso en el periodo seleccionado')
        else:
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso, paralelo_id=paralelo).exclude(id=u.pk).exists():
                self.add_error('paralelo', 'Ya existe ese paralelo en el curso y periodo seleccionado')
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso).exclude(id=u.pk).exists():
                self.add_error('curso', 'Ya existe ese curso en el periodo seleccionado')

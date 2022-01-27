from django import forms
from django.forms import TextInput, Select
from .models import Curso, CursoParalelo, ConfiguracionValoresCurso, ConfiguracionValoresGeneral, TIPO_PARCIAL, \
    Quimestre, ModeloParcial
from ..materia.models import Materia
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
            self.fields['paralelo'].widget.attrs = {'class': 'form-control select2', 'multiple': 'multiple'}
            # self.fields['paralelo'].initial = Paralelo.objects.filter(status=True)[:10]
            self.fields['periodo'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['periodo'].initial = PeriodoLectivo.objects.filter(status=True)[:10]

    class Meta:
        model = CursoParalelo
        fields = ['periodo', 'curso', 'paralelo', 'cupo', 'cupoindividual', 'quimestres', 'parciales']
        labels = {'curso': 'Curso', 'paralelo': 'Paralelo', 'periodo': 'Periodo',
                  'cupoindividual': 'Cupo Individual para cada paralelo?', 'quimestres': 'N° Quimestres',
                  'parciales': 'N° Parciales por Quimestre'}
        widgets = {'cupoindividual': forms.CheckboxInput(attrs={
                       'data-toggle': 'toggle', 'data-on': 'Si', 'data-off': 'No', 'data-onstyle': 'success',
                       'data-offstyle': 'danger'
                   }),
        'quimestres': forms.NumberInput(attrs={'class': 'form-comtrol', 'max': 5, 'min': 2}),
        'parciales': forms.NumberInput(attrs={'class': 'form-comtrol', 'max': 5, 'min': 3})
        }

    def clean(self):
        f = super()
        u = f.save(commit=False)
        periodo = self.cleaned_data['periodo']
        curso = self.cleaned_data['curso']
        if u.pk is None:
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso).exists():
                self.add_error('curso', 'Ya existe ese curso en el periodo seleccionado')
        else:
            if CursoParalelo.objects.filter(periodo_id=periodo, curso_id=curso).exclude(id=u.pk).exists():
                self.add_error('curso', 'Ya existe ese curso en el periodo seleccionado')
        if self.cleaned_data['quimestres'] < 2:
            self.add_error('quimestres', 'Debe Ingresar un numero de quimestres igual o mayor a 2')
        if self.cleaned_data['parciales'] < 3:
            self.add_error('quimestres', 'Debe Ingresar un numero de parciales por quimestre igual o mayor a 3')


class FormularioConfiguracionValores(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['matricula'].widget.attrs = {'class': 'form-control'}
            self.fields['matricula'].initial = 10.00
            self.fields['pension'].widget.attrs = {'class': 'form-control'}
            self.fields['pension'].initial = 10.00
            self.fields['numeropensiones'].widget.attrs = {'class': 'form-control'}
            self.fields['numeropensiones'].initial = 1
    class Meta:
        model = ConfiguracionValoresGeneral
        fields = ['matricula', 'pension', 'numeropensiones']
        labels = {'matricula': 'Valor de Matricula', 'pension': 'Valor de pension', 'numeropensiones': 'Cantidad de Pensiones'}
        # widgets = {'curso': forms.Select(), 'paralelo': forms.Select(), 'periodo': forms.Select()}


class FormularioNotas(forms.Form):
    periodo = forms.ModelChoiceField(queryset=PeriodoLectivo.objects.none(),  empty_label=None, widget=forms.Select(attrs={'class': 'form-control select2'}))
    curso = forms.ModelChoiceField(queryset=Curso.objects.none(),  empty_label=None, widget=forms.Select(attrs={'class': 'form-control select2'}))
    paralelo = forms.ModelChoiceField(queryset=Paralelo.objects.none(), widget=forms.Select(attrs={'class': 'form-control select2'}))
    materia = forms.ModelChoiceField(queryset=Materia.objects.none(), widget=forms.Select(attrs={'class': 'form-control select2'}))
    quimestre = forms.ModelChoiceField(queryset=Quimestre.objects.none(), widget=forms.Select(attrs={'class': 'form-control select2'}))
    parcial = forms.ModelChoiceField(queryset=ModeloParcial.objects.none(), widget=forms.Select(attrs={'class': 'form-control select2'}))

    def edit(self, info):
        self.fields['periodo'].queryset = PeriodoLectivo.objects.filter(status=True, id=info['periodo'].pk)
        self.fields['curso'].queryset = Curso.objects.filter(status=True, id=info['curso'].pk)
        self.fields['paralelo'].queryset = Paralelo.objects.filter(status=True, id=info['paralelo'].pk)
        self.fields['materia'].queryset = Materia.objects.filter(status=True, id=info['materia'].pk)
        self.fields['quimestre'].queryset = Quimestre.objects.filter(status=True, id=info['quimestre'].pk)
        # self.fields['parcial'].queryset = ModeloParcial.objects.filter(status=True, id=info['parcial'].pk)
        self.fields['periodo'].initial = info['periodo']
        self.fields['curso'].initial = info['curso']
        self.fields['paralelo'].initial = info['paralelo']
        self.fields['materia'].initial = info['materia']
        self.fields['quimestre'].initial = info['quimestre']
        # self.fields['parcial'].initial = info['parcial']

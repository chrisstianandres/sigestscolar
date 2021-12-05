from django import forms
from django.forms import TextInput, Select

from apps.inscripcion.models import Inscripcion


class Formulario(forms.ModelForm):
    # constructor
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            self.fields['alumno'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['curso'].initial = Curso.objects.filter(status=True)[:10]
            self.fields['curso'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['paralelo'].initial = Paralelo.objects.filter(status=True)[:10]
            # self.fields['periodo'].widget.attrs = {'class': 'form-control select2'}
            # self.fields['periodo'].initial = PeriodoLectivo.objects.filter(status=True)[:10]

    class Meta:
        model = Inscripcion
        fields = ['alumno', 'curso', 'fecha', 'paralelo']
        labels = {'curso': 'Curso', 'alumno': 'Alumno', 'fecha': 'fecha', 'paralelo': 'Paralelo'}
        # widgets = {'curso': forms.Select(), 'paralelo': forms.Select(), 'periodo': forms.Select()}

    def clean(self):
        f = super()
        u = f.save(commit=False)
        alumno = self.cleaned_data['alumno']
        curso = self.cleaned_data['curso']
        if u.pk is None:
            if Inscripcion.objects.filter(alumno_id=alumno, curso_id=curso, activo=True).exists():
                self.add_error('alumno', 'Ya existe una inscripcion para este alumno en el periodo seleccionado')
        else:
            if Inscripcion.objects.filter(alumno_id=alumno, curso_id=curso, activo=True).exclude(id=u.pk).exists():
                self.add_error('alumno', 'Ya existe una inscriocion para este alumno en este periodo seleccionado')

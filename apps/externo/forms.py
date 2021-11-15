from django import forms
from django.forms import TextInput
from apps.persona.models import Persona, TipoSangre


class Formulario(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.visible_fields():
            form.field.widget.attrs['class'] = 'form-control'
            form.field.widget.attrs['autocomplete'] = 'off'
            # form.field.widget.attrs['required'] = True
        self.fields['sangre'].initial = TipoSangre.objects.all().first()
        self.fields['ruc'].widget.attrs['required'] = False
        self.fields['telefono_conv'].widget.attrs['required'] = False
        self.fields['libretamilitar'].widget.attrs['required'] = False
        self.fields['libretamilitar'].blank = True
        self.fields['libretamilitar'].null = True

    class Meta:
        model = Persona
        fields = ['nombres', 'apellido1', 'apellido2', 'cedula', 'pasaporte', 'ruc', 'nacimiento', 'genero',
                  'lugarnacimiento', 'lugarecidencia',  'direccion', 'direccion2', 'num_direccion',
                  'referencia', 'telefono', 'telefono_conv',  'email', 'sangre', 'libretamilitar', 'lgtbi']
        widgets = {'nombres': forms.TextInput(attrs={'placeholder': 'Ingrese los nombres',  'autofocus': True}),
                   'apellido1': forms.TextInput(attrs={'placeholder': 'Ingrese el primer apellido'}),
                   'apellido2': forms.TextInput(attrs={'placeholder': 'Ingrese el segundo apellido'}),
                   'cedula': forms.TextInput(attrs={'placeholder': 'Ingrese el numero de cedula'}),
                   'pasaporte': forms.TextInput(attrs={'placeholder': 'Ingrese el numero de pasaporte', 'required': False}),
                   'ruc': forms.TextInput(attrs={'placeholder': 'Ingrese el ruc', 'required': False}),
                   'nacimiento': forms.TextInput(attrs={'placeholder': 'Ingrese la fecha de nacimiento', 'class': 'datetimepicker-input'}),
                   'genero': forms.Select(),
                   'direccion': forms.TextInput(attrs={'placeholder': 'Maximo 200 caracteres'}),
                   'direccion2': forms.TextInput(attrs={'placeholder': 'Maximo 200 caracteres'}),
                   'num_direccion': forms.TextInput(attrs={'placeholder': '#'}),
                   'referencia': forms.Textarea(attrs={'placeholder': 'Maximo 300 caracteres', 'rows': '3', 'cols': '50'}),
                   'telefono': forms.TextInput(attrs={'placeholder': 'Telefono movil'}),
                   'telefono_conv': forms.TextInput(attrs={'placeholder': 'Telefono convencional', 'required': False}),
                   'email': forms.TextInput(attrs={'placeholder': '@ Email personal'}),
                   'libretamilitar': forms.TextInput(attrs={'placeholder': 'Numero de libreta militar', 'required': False}),
                   'lgtbi': forms.CheckboxInput(attrs={
                       'data-toggle': 'toggle', 'data-on': 'Si', 'data-off': 'No', 'data-onstyle': 'success',
                       'data-offstyle': 'danger'
                   }),
                   'sangre': forms.Select()
                   }

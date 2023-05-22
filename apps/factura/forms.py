from datetime import datetime

from django import forms

from apps.factura.models import FORMA_PAGO
from apps.persona.models import Persona


class Formulario(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Persona.objects.filter(status=True)[0:10], widget=forms.Select(attrs={'class': 'form-control select2'}))
    fecha = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'disabled': True}), initial=datetime.now().date().strftime('%Y-%m-%d'))
    referencia_deposito = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'required': False}), required=False)
    referencia_transferencia = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'required': False}), required=False)
    boucher = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'required': False}), required=False)
    formapago = forms.ChoiceField(choices=FORMA_PAGO, initial=1, widget=forms.Select(attrs={'class': 'form-control select2'}), required=False)


class ArchivoFirmado(forms.Form):
    archivo = forms.FileField()
from datetime import datetime

from django.db import models
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce

from apps.extras import ModeloBase



class PeriodoLectivo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    anio = models.IntegerField(default=0, verbose_name=u'Anio', unique=True)
    desde = models.DateField(verbose_name=u"Fecha de incio de periodo")
    hasta = models.DateField(verbose_name=u"Fecha de fin de periodo")
    actual = models.BooleanField(default=True)
    inicioactividades = models.DateField(verbose_name=u"Fecha de incio de actividades academicas", null=True, blank=True)

    def __str__(self):
        # return '{} - Año: {} Dese: {} - Hasta: {}'.format(self.nombre, self.anio, self.desde, self.hasta)
        return 'Periodo: {} - {}'.format(self.desde.year, self.hasta.year)

    def nombre_corto(self):
        return '{} - {}'.format(self.desde.year, self.hasta.year)

    def cobrado_por_mes(self):
        from apps.rubro.models import Pago
        totales = []
        anio = datetime.now().year
        for m in range(1, 13):
            totales.append(Pago.objects.filter(status=True, fecha__year=anio, fecha__month=m, factura__valida=True,
                                               factura__verificada=True).aggregate(
                total=Coalesce(Sum('valortotal', output_field=FloatField()), float(0))).get('total'))
        return totales
    #
    def vencido_por_mes(self):
        from apps.rubro.models import Rubro
        totales = []
        hoy = datetime.now()
        anio = hoy.year
        for m in range(1, 13):
            totales.append(Rubro.objects.filter(status=True, fechavence__year=anio, fechavence__month=m, fechavence__lt=hoy,
                                                cancelado=False).aggregate(
                total=Coalesce(Sum('valortotal', output_field=FloatField()), float(0))).get('total'))
        return totales
    #
    def porcobrar_por_mes(self):
        from apps.rubro.models import Rubro
        totales = []
        hoy = datetime.now()
        anio = hoy.year
        for m in range(1, 13):
            totales.append(Rubro.objects.filter(status=True, fechavence__year=anio, fechavence__month=m, cancelado=False
                                                ).aggregate(
                total=Coalesce(Sum('valortotal', output_field=FloatField()), float(0))).get('total'))
        return totales

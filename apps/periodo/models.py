from django.db import models

from apps.extras import ModeloBase


class PeriodoLectivo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    anio = models.IntegerField(default=0, verbose_name=u'Anio', unique=True)
    desde = models.DateField(verbose_name=u"Fecha de incio de periodo")
    hasta = models.DateField(verbose_name=u"Fecha de fin de periodo")

    def __str__(self):
        return '{} - Año: {} Dese: {} - Hasta: {}'.format(self.nombre, self.anio, self.desde, self.hasta)
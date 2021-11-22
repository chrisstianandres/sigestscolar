from django.db import models

from apps.curso.models import CursoParalelo
from apps.extras import ModeloBase
from apps.persona.models import Persona


class Alumno(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.PROTECT)
    representante = models.ForeignKey(Persona, related_name='+', blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"Representante")
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Alumno"
        verbose_name_plural = u"Alumnos"
        ordering = ['persona']
        unique_together = ('persona',)



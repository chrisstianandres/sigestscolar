from django.db import models

from apps.extras import ModeloBase
from apps.persona.models import Persona


class Administrativo(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.PROTECT)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Administrativo"
        verbose_name_plural = u"Administrativos"
        ordering = ['persona']
        unique_together = ('persona',)
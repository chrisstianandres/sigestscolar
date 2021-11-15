from django.db import models

from apps.extras import ModeloBase
from apps.persona.models import Persona


class Externo(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.PROTECT)

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Externos"
        verbose_name_plural = u"Externos"
        ordering = ['persona']
        unique_together = ('persona',)

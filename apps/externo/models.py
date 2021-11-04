from django.db import models

from apps.extras import ModeloBase
from apps.persona.models import Persona


class Externo(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.PROTECT)
    nombrecomercial = models.CharField(default='', max_length=200, verbose_name=u'Nombre comercial')
    nombrecontacto = models.CharField(default='', max_length=200, verbose_name=u'Nombre contacto')
    telefonocontacto = models.CharField(default='', max_length=50, verbose_name=u"Telefono contacto")
    lugarestudio = models.CharField(default='', max_length=100, verbose_name=u'Lugar de estudio')
    carrera = models.CharField(default='', max_length=100, verbose_name=u'Carrera')
    profesion = models.CharField(default='', max_length=100, verbose_name=u'Profesión')
    institucionlabora = models.CharField(default='', max_length=100, verbose_name=u'Institución Labora')
    cargodesempena = models.CharField(default='', max_length=100, verbose_name=u'Cargo')
    telefonooficina = models.CharField(default='', max_length=100, verbose_name=u'Telefono de oficina')
    jornada = models.CharField(default='', max_length=1, verbose_name=u'Jornada')
    facultad = models.CharField(default='', max_length=100, verbose_name=u'Facultad')
    semestre = models.CharField(default='', max_length=100, verbose_name=u'Semestre')

    def __str__(self):
        return u'%s' % self.nombrecomercial

    class Meta:
        verbose_name = u"Externos"
        verbose_name_plural = u"Externos"
        ordering = ['persona']
        unique_together = ('persona',)

    def save(self, *args, **kwargs):
        self.nombrecomercial = self.nombrecomercial.upper().strip()
        self.nombrecontacto = self.nombrecontacto.upper().strip()
        super(Externo, self).save(*args, **kwargs)

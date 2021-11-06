from django.db import models

from apps.extras import ModeloBase


class Paralelo(ModeloBase):
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripcion del curso')
    # nombreletras = models.CharField(default='', max_length=1, verbose_name=u'Descripcion del curso')

    def __str__(self):
        return '{}'.format(self.nombre)

    class Meta:
        verbose_name = u"Paralelo"
        verbose_name_plural = u"Paralelos"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        # self.nombreletras = self.nombreletras.upper().strip()
        super(Paralelo, self).save(*args, **kwargs)

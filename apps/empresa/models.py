from django.db import models

from apps.extras import ModeloBase


class Iva(ModeloBase):
    ivaporciento = models.FloatField(default=12)

    def __str__(self):
        return '{}'.format(self.ivaporciento)


class Empresa(ModeloBase):
    nombre = models.CharField(max_length=100, null=True, blank=True, verbose_name='Nombre')
    direccion = models.TextField(default='', verbose_name=u"Direccion")
    mision = models.TextField(default='', verbose_name=u"Mision")
    vision = models.TextField(default='', verbose_name=u"Vision")
    telefono = models.CharField(max_length=10, null=True, blank=True, verbose_name='Telefono')
    email = models.TextField(null=True, blank=True, verbose_name='email')
    iva = models.ForeignKey(Iva, null=True, blank=True, verbose_name=u"Iva", on_delete=models.PROTECT)

    def __str__(self):
        return '{}{}'.format(self.nombre, self.direccion)

    class Meta:
        verbose_name = u"Empresa"
        verbose_name_plural = u"Empresas"
        unique_together = ('nombre',)
from django.db import models

from apps.extras import ModeloBase


class Iva(ModeloBase):
    ivaporciento = models.FloatField(default=12)

    def __str__(self):
        return '{}'.format(self.ivaporciento)


class Empresa(ModeloBase):
    nombre = models.CharField(max_length=100, null=True, blank=True, verbose_name='Nombre')
    descripcioncorta = models.CharField(max_length=100, null=True, blank=True, verbose_name='Descripcion corta')
    direccion = models.TextField(default='', verbose_name=u"Direccion")
    mision = models.TextField(default='', verbose_name=u"Mision")
    vision = models.TextField(default='', verbose_name=u"Vision")
    telefono = models.CharField(max_length=10, null=True, blank=True, verbose_name='Telefono')
    telefono2 = models.CharField(max_length=10, null=True, blank=True, verbose_name='Telefono 2')
    telefono3 = models.CharField(max_length=10, null=True, blank=True, verbose_name='Telefono 3')
    ruc = models.CharField(max_length=13, null=True, blank=True, verbose_name='Ruc')
    email = models.EmailField(null=True, blank=True, verbose_name='email')
    iva = models.ForeignKey(Iva, null=True, blank=True, verbose_name=u"Iva", on_delete=models.PROTECT)

    def __str__(self):
        return '{}{}'.format(self.nombre, self.direccion)

    def iva_empresa(self):
        return self.iva.ivaporciento if self.iva else 12

    class Meta:
        verbose_name = u"Empresa"
        verbose_name_plural = u"Empresas"
        unique_together = ('nombre', )
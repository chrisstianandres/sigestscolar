from django.db import models

from apps.extras import ModeloBase


class Producto(ModeloBase):
    codigo = models.IntegerField(default=0)
    descripcion = models.TextField(default='')
    alias = models.CharField(max_length=50, blank=True, null=True)
    codigobarra = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return u'%s' % self.descripcion

    class Meta:
        verbose_name = u'Producto'
        verbose_name_plural = u'Productos'
        unique_together = ('codigo',)
        ordering = ('codigo', )

    def nombre_corto(self):
        return "%s - %s" % (self.codigo, self.descripcion)


class Inventario(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=0)
    fechaingreso = models.DateField()

    def __str__(self):
        return '{}{}'.format(self.producto, self.cantidad)

    class Meta:
        verbose_name = u'Inventario'
        verbose_name_plural = u'Inventarios'
        ordering = ('producto', )

    def nombre_corto(self):
        return "%s - %s" % (self.producto, self.cantidad)
from django.db import models
from django.db.models import Sum

from apps.extras import ModeloBase, PrimaryKeyEncryptor
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Talla(ModeloBase):
    numero = models.IntegerField(default=0)
    talla = models.CharField(max_length=4, default='', blank=True, null=True)

    def __str__(self):
        return '{} - {}'.format(self.numero, self.talla)

    class Meta:
        verbose_name = u'Talla'
        verbose_name_plural = u'Tallas'
        unique_together = ('talla', 'numero', )
        ordering = ('numero', 'talla', )


class Producto(ModeloBase):
    codigo = models.IntegerField(default=0, unique=True)
    descripcion = models.TextField(default='')
    alias = models.CharField(max_length=50, blank=True, null=True)
    codigobarra = models.CharField(max_length=20, blank=True, null=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    talla = models.ForeignKey(Talla, blank=True, null=True, on_delete=models.PROTECT)
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')

    def __str__(self):
        return '{} - {}'.format(self.descripcion, self.talla)

    class Meta:
        verbose_name = u'Producto'
        verbose_name_plural = u'Productos'
        unique_together = ('codigo',)
        ordering = ('codigo', )

    def nombre_corto(self):
        return "%s - %s - Talla: (%s)" % (self.codigo, self.descripcion, self.talla)

    def encoded_id(self):
        return PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).encrypt(self.id)

    def decode_id(self, id):
        return PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(id)

    def stock_producto(self):
        return Inventario.objects.filter(status=True).aggregate(Sum('cantidad')).get('cantidad__sum')

    def valortotal(self):
        return float(self.valor) + float(self.valoriva())

    def saldo_actual(self):
        return self.valortotal()

    def valoriva(self):
        return float(self.valor) * 0.12


class Inventario(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=0)
    fechaingreso = models.DateField()

    def __str__(self):
        return '{} - {}'.format(self.producto, self.cantidad)

    class Meta:
        verbose_name = u'Inventario'
        verbose_name_plural = u'Inventarios'
        ordering = ('producto', )

    def nombre_corto(self):
        return "%s - %s" % (self.producto, self.cantidad)




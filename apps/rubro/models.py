from datetime import datetime
from decimal import Decimal

from django.db import models
from django.db.models import Sum

from apps.empresa.models import Empresa
from apps.extras import ModeloBase, null_to_numeric
from apps.matricula.models import Matricula, Pension
from apps.persona.models import Persona
from apps.producto.models import Inventario


class Rubro(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u'Cliente', on_delete=models.PROTECT)
    pension = models.ForeignKey(Pension, verbose_name=u'Pension', on_delete=models.PROTECT,  blank=True, null=True)
    matricula = models.ForeignKey(Matricula, blank=True, null=True, verbose_name=u'Matricula', on_delete=models.PROTECT)
    producto = models.ForeignKey(Inventario, blank=True, null=True, verbose_name=u'Producto', on_delete=models.PROTECT)
    nombre = models.CharField(max_length=300, verbose_name=u'Nombre', blank=True, null=True)
    fecha = models.DateField(verbose_name=u'Fecha emisión', blank=True, null=True,)
    fechavence = models.DateField(verbose_name=u'Fecha vencimiento', blank=True, null=True,)
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    iva = models.ForeignKey(Empresa, verbose_name=u'IVA', on_delete=models.PROTECT)
    valoriva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor IVA')
    valortotal = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor total')
    valordescuento = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor descuento')
    saldo = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Saldo')
    cancelado = models.BooleanField(default=False, verbose_name=u'Cancelado')
    observacion = models.TextField(default='', max_length=250, blank=True, null=True, verbose_name=u"Observación")
    # capeventoperiodoipec = models.ForeignKey(CapEventoPeriodoIpec, blank=True, null=True, verbose_name=u"curso")
    anulado = models.BooleanField(default=False, verbose_name=u'Anulados')
    bloqueado = models.BooleanField(default=False)

    def fechavence_str(self):
        return str(self.fechavence)

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Rubro de cobro"
        verbose_name_plural = u"Rubros de cobro"

    def esta_liquidado(self):
        return self.pago_set.filter(pagoliquidacion__isnull=False).exists()

    def esta_anulado(self):
        return self.pago_set.filter(factura__valida=False).exists()

    def tiene_pagos(self):
        return self.pago_set.exists()

    def tiene_factura(self):
        try:
            return self.pago_set.all()[0].factura_set.exists()
        except:
            return False

    def factura(self):
        return self.pago_set.all().order_by('-fecha')[0].factura().id

    def valor_total(self):
        if self.iva.iva.ivaporciento:
            return (float(self.valor) - float(self.valordescuento) )+ ((float(self.valor) - float(self.valordescuento)) * float((self.iva.iva.ivaporciento)/100))
        return float(self.valor) - float(self.valordescuento)

    def valor_iva(self):
        if self.iva.iva.ivaporciento:
            return (float(self.valor) - float(self.valordescuento)) * float(self.iva.iva.ivaporciento/100)
        return 0

    def vencido(self):
        return not self.cancelado and self.fechavence < datetime.now().date()

    def puede_eliminarse(self):
        return not self.cancelado and not self.pago_set.exists()

    def tiene_adeuda(self):
        return self.total_pagado() < self.valor

    def valores_anulados(self):
        return null_to_numeric(
            self.pago_set.filter(factura__valida=False, status=True).aggregate(valor=Sum('valortotal'))['valor'], 2)

    def total_pagado(self):
        return self.pago_set.filter(rubro__status=True).exclude(pagoliquidacion__isnull=False).distinct().aggregate(valor=Sum('valortotal'))['valor']

    def adeudado(self):
        return self.valortotal - self.total_pagado()

    def total_liquidado(self):
        return self.pago_set.filter(pagoliquidacion__isnull=False).distinct().aggregate(valor=Sum('valortotal'))['valor']

    def total_adeudado(self):
        sumapagado = self.total_pagado() + self.total_liquidado()
        saldo = (self.valor_total() - sumapagado)
        try:
            if saldo == 0 and self.cancelado == False:
                self.cancelado = True
                self.save()
        except Exception as ex:
            print(ex)
            pass
        return saldo

    def nombre_usuario(self):
        if self.usuario_creacion:
            if not self.usuario_creacion.is_superuser:
                return self.usuario_creacion
        return None

    def total_finanzas(self):
        if Rubro.objects.filter(status=True, persona=self.persona).exists():
            return Rubro.objects.filter(status=True, persona=self.persona).aggregate(Sum('valor')).get('valor__sum')
        return 0.00

    def total_pagado_finanzas(self):
        if Pago.objects.filter(status=True, rubro__persona=self.persona).exists():
            return Pago.objects.filter(status=True, rubro__persona=self.persona).aggregate(Sum('valortotal')).get('valortotal__sum')
        return 0.00

    def total_adeudado_finanzas(self):
        return float(self.total_finanzas()) - float(self.total_pagado_finanzas())

    def total_vencido_finanzas(self):
        if Rubro.objects.filter(status=True, persona=self.persona, fechavence__lt=datetime.now(), cancelado=False).exists():
            return Rubro.objects.filter(status=True, persona=self.persona, fechavence__lt=datetime.now(), cancelado=False).aggregate(Sum('valor')).get('valor__sum')
        return 0.00

    def tiene_rubros(self):
        return Rubro.objects.filter(status=True, persona=self.persona).exists()


    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip() if self.nombre else ''
        self.observacion = self.observacion.upper().strip() if self.observacion else ''
        # self.valortotal = self.valor_total()
        # self.saldo = self.total_adeudado()
        if self.valor > 0:
            self.cancelado = (self.saldo == 0)
        if self.esta_anulado():
            self.anulado = True
        super(Rubro, self).save(*args, **kwargs)


class Pago(ModeloBase):
    rubro = models.ForeignKey(Rubro, verbose_name=u'Rubros', on_delete=models.PROTECT)
    fecha = models.DateField(verbose_name=u'Fecha')
    subtotal0 = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    subtotaliva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    iva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'IVA')
    valordescuento = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor Total')
    valortotal = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor Total')
    efectivo = models.BooleanField(default=True, verbose_name=u'Pago en efectivo')

    def __str__(self):
        return u'Pago $%s' % self.valortotal

    class Meta:
        verbose_name = u"Pago"
        verbose_name_plural = u"Pagos"
        ordering = ['fecha']

    def subtotal(self):
        return self.subtotaliva if self.iva else self.subtotal0

    def total_sinimpuesto(self):
        return Decimal(self.subtotal0 + self.subtotaliva).quantize(Decimal('.01'))

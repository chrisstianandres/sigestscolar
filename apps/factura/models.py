from django.db import models
from django.db.models import Sum

from apps.empresa.models import Iva
from apps.extras import ModeloBase, null_to_decimal
from apps.persona.models import Persona
from apps.rubro.models import Pago

ESTADO_COMPROBANTE = {
    (1, 'CORRECTA'),
    (2, 'INCORRECTA'),
    (3, 'ANULADA'),
}

FORMA_PAGO = {
    (1, 'EFECTIVO'),
    (2, 'TRANSFERENCIA'),
    (3, 'DEPOSITO'),
    (4, 'TARJETA DE CREDITO/DEBITO'),
}


class Factura(ModeloBase):
    numero = models.IntegerField(default=0, verbose_name=u"Numero")
    numerocompleto = models.CharField(default='', max_length=20, verbose_name=u"Numero Completo")
    fecha = models.DateField(verbose_name=u"Fecha")
    observacion = models.TextField(default='', blank=True, null=True, verbose_name=u'Observación')
    valida = models.BooleanField(default=True, verbose_name=u"Valida")
    cliente = models.ForeignKey(Persona, verbose_name=u"Cliente", on_delete=models.PROTECT)
    ivaaplicado = models.ForeignKey(Iva, blank=True, null=True, verbose_name=u"Iva Aplicado", on_delete=models.PROTECT)
    subtotal_base_iva = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    subtotal_base0 = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    total_descuento = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    total_iva = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    impresa = models.BooleanField(default=False, verbose_name=u"Impresa")
    pagos = models.ManyToManyField(Pago, blank=True, verbose_name=u"Pagos")
    identificacion = models.CharField(default='', max_length=20, verbose_name=u"Identificación")
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")
    email = models.CharField(default='', max_length=100, verbose_name=u"Email")
    direccion = models.TextField(default='', verbose_name=u"Dirección")
    telefono = models.CharField(default='', max_length=50, verbose_name=u"Telefono")
    electronica = models.BooleanField(default=False, verbose_name=u"Electrónica")
    pagada = models.BooleanField(default=True, verbose_name=u"Pagada")
    estado = models.IntegerField(choices=ESTADO_COMPROBANTE, default=1, verbose_name=u'Estado Factura')
    formapago = models.IntegerField(choices=FORMA_PAGO, default=1, verbose_name=u'Forma de pago')
    referencia_deposito = models.TextField(default='', verbose_name=u"Referencia deposito", null=True, blank=True)
    referencia_transferencia = models.TextField(default='', verbose_name=u"Referencia deposito", null=True, blank=True)
    boucher = models.TextField(default='', verbose_name=u"Numero de Boucher", null=True, blank=True)
    verificada = models.BooleanField(default=False, verbose_name=u"Verificada")

    def __str__(self):
        return u'Factura No. %s' % self.numero

    class Meta:
        verbose_name = u"Factura"
        verbose_name_plural = u"Facturas"
        ordering = ['numero']
        unique_together = ('numero',)

    # def enletras(self):
    #     return number_to_letter.enletras(self.total)
    #
    # def persona_cajero(self):
    #     return self.sesioncaja.caja.persona
    #
    # def puede_reimprimirse(self):
    #     return self.fecha == datetime.now().date()
    #
    # def total_sin_impuesto_sri(self):
    #     return Decimal(self.subtotal_base0 + self.subtotal_base_iva).quantize(Decimal('.01'))
    #
    # def esta_anulada(self):
    #     # return FacturaCancelada.objects.filter(factura=self).exists()
    #     return self.facturacancelada__set.exists()
    #
    # def datos_anulacion(self):
    #     if self.esta_anulada():
    #         return FacturaCancelada.objects.filter(factura=self)[0]
    #     return None
    #
    # def en_fecha(self):
    #     return datetime.now().date() == self.fecha
    #
    # def tipo_identificacion(self):
    #     from sga.models import TIPOS_IDENTIFICACION
    #     return TIPOS_IDENTIFICACION[self.tipo - 1][1]
    #
    def actualiza_subtotales(self):
        self.subtotal_base0 = null_to_decimal(self.pagos.aggregate(valor=Sum('subtotal0'))['valor'], 2)
        self.subtotal_base_iva = null_to_decimal(self.pagos.aggregate(valor=Sum('subtotaliva'))['valor'], 2)
        self.total_descuento = null_to_decimal(self.pagos.aggregate(valor=Sum('valordescuento'))['valor'], 2)
        self.total_iva = null_to_decimal(self.pagos.aggregate(valor=Sum('iva'))['valor'], 2)
        self.total = null_to_decimal(self.pagos.aggregate(valor=Sum('valortotal'))['valor'], 2)

    def detalle_rubros(self):
        return self.pagos.all()
    #
    # def restaurarrubros(self, observacion):
    #     for pago in self.pagos.all():
    #         rub = Rubro.objects.get(pk=pago.rubro.pk)
    #         rub.anulado = True
    #         rub.save()
    #         totalrub = float(rub.saldo) + float(pago.valortotal)
    #         totalrubsinimpuestos = float(rub.saldo) + float(pago.total_sinimpuesto())
    #         rubro = Rubro(tipo=pago.rubro.tipo,
    #                       persona=pago.rubro.persona,
    #                       nombre=pago.rubro.nombre,
    #                       cuota=pago.rubro.cuota,
    #                       contratorecaudacion=pago.rubro.contratorecaudacion,
    #                       fecha=pago.rubro.fecha,
    #                       fechavence=pago.rubro.fechavence,
    #                       valor=float(pago.total_sinimpuesto()),
    #                       iva=pago.rubro.iva,
    #                       valoriva=float(pago.iva),
    #                       valortotal=float(pago.valortotal),
    #                       saldo=float(pago.valortotal),
    #                       idrubrounemi=pago.rubro.idrubrounemi,
    #                       cancelado=False,
    #                       observacion=observacion,
    #                       capeventoperiodoipec=pago.rubro.capeventoperiodoipec)
    #         rubro.save()
    #
    #         # ANULAR PAGOS SGA
    #         if rubro.idrubrounemi > 0:
    #             cursor = connections['unemi'].cursor()
    #             sql = "UPDATE sagest_rubro SET idrubroepunemi = '%s' WHERE sagest_rubro.status= true and sagest_rubro.id= %s" % (
    #                 rubro.id, rubro.idrubrounemi)
    #             cursor.execute(sql)
    #             # ELIMINAR ID PAGOEPUNEMI_PAGO
    #             # SE BUSCA TODOS LOS PAGOSEPUNEMI_PAGOS REGISTRADOS CON EL IDENTIFICADOR IDPAGOEPUNEMI YA QUE ESTE SE REGISTRA COMO IDENTIFICADOR EN PAGO Y PAGOEPUNEMI
    #             sqlconsultapagos = "SELECT p.id FROM sagest_pagoepunemi_pagos AS p INNER JOIN sagest_pagoepunemi  ep ON p.pagoepunemi_id = ep.id WHERE ep.idpagoepunemi=%s" % (
    #                 pago.id)
    #             cursor.execute(sqlconsultapagos)
    #             rowsconsulta = cursor.fetchall()
    #             for r in rowsconsulta:
    #                 idpagoep_pago = r[0]
    #                 sqlpagoindividual = "DELETE FROM sagest_pagoepunemi_pagos WHERE id = %s" % (idpagoep_pago)
    #                 cursor.execute(sqlpagoindividual)
    #             # ELIMINAR ID PAGO
    #             # SE ELIMINA TODOS LOS REGISTROS DE SAGEST_PAGO FILTRANDO EL MISMO NUMERO IDENTIFICADOR IDPAGOEPUNEMI 2
    #             sqlpago = "DELETE FROM sagest_pago p WHERE p.idpagoepunemi= %s" % (pago.id)
    #             cursor.execute(sqlpago)
    #             # ELIMINAR PAGOEPUNEMI
    #             # SE ELIMINA TODOS LOS REGISTROS DE SAGEST_PAGOEPUNEMI FILTRANDO EL MISMO NUMERO IDENTIFICADOR IDPAGOEPUNEMI 2
    #             delpagoepunemi = "DELETE FROM sagest_pagoepunemi WHERE sagest_pagoepunemi.idpagoepunemi= %s" % (pago.id)
    #             cursor.execute(delpagoepunemi)
    #             cursor.close()
    #
    #         # REVIVIR RUBRO EN SGA
    #         import urllib3
    #         http = urllib3.PoolManager()
    #         data = {'a': 'uprubrounemi', 'irubro': encrypt(rubro.idrubrounemi),
    #                 'tk': '04m76#5&*fg8^6677d8lv0+2t$hkjw=8emvaed(an118!y6a%s' % encrypt(rubro.idrubrounemi)}
    #         # r = http.request('POST', 'http://127.0.0.1:8086/api', data)
    #         r = http.request('POST', 'https://sga.unemi.edu.ec/api_2', data)
    #         resultado = json.loads(r.data.decode('utf-8'))
    #
    # def cancelar(self, motivo, request):
    #     self.restaurarrubros(motivo)
    #     self.valida = False
    #     self.save(request)
    #     facturacancelada = FacturaCancelada(factura=self,
    #                                         motivo=motivo,
    #                                         fecha=datetime.now())
    #     facturacancelada.save(request)
    #
    # def genera_clave_acceso_factura(self):
    #     hoy = self.fecha
    #     numero = self.numero
    #     return self.generar_clave_acceso(hoy, numero, '01')
    #
    # def generar_clave_acceso(self, fecha, numero, codigo):
    #     from sga.models import miinstitucion
    #     institucion = miinstitucion()
    #     hoy = fecha
    #     codigonumerico = str(
    #         Decimal('%02d%02d%04d' % (hoy.day, hoy.month, hoy.year)) + Decimal(institucion.ruc) + Decimal(
    #             '%3s%3s%9s' % (self.puntoventa.establecimiento, self.puntoventa.puntoventa, str(numero).zfill(9))))[:8]
    #     parcial = "%02d%02d%04d%2s%13s%1d%3s%3s%9s%8s%1d" % (hoy.day, hoy.month, hoy.year, codigo, institucion.ruc,
    #                                                          self.tipoambiente, self.puntoventa.establecimiento,
    #                                                          self.puntoventa.puntoventa, str(numero).zfill(9),
    #                                                          codigonumerico, self.tipoemision)
    #     digitoverificador = self.generar_digito_verificador(parcial)
    #     return parcial + str(digitoverificador)
    #
    # def generar_digito_verificador(self, cadena):
    #     basemultiplicador = 7
    #     aux = [0 for i in cadena]
    #     multiplicador = 2
    #     total = 0
    #     verificador = 0
    #     for i in range(len(cadena) - 1, -1, -1):
    #         aux[i] = int(cadena[i]) * multiplicador
    #         multiplicador += 1
    #         if multiplicador > basemultiplicador:
    #             multiplicador = 2
    #         total += aux[i]
    #     if total == 0 or total == 1:
    #         verificador = 0
    #     else:
    #         verificador = 0 if (11 - (total % 11)) == 11 else 11 - (total % 11)
    #     if verificador == 10:
    #         verificador = 1
    #     return verificador
    #
    def numero_secuencial(self):
        return str(self.numero).zfill(9)

    def generar_numero_completo(self):
        self.numerocompleto = str(str('001-001-')+self.numero_secuencial())

    def formapago_span(self):
        span = ''
        if self.formapago == 1:
            span = 'success'
        elif self.formapago == 2:
            span = 'info'
        elif self.formapago == 3:
            span = 'primary'
        else:
            span = 'dark'
        return span
    #
    # def tipo_pago(self):
    #     lista = []
    #     if self.pagos.filter(efectivo=True).exists():
    #         valor = null_to_decimal(self.pagos.filter(efectivo=True).aggregate(valor=Sum('valortotal'))['valor'], 2)
    #         lista.append(['01', valor])
    #     if self.pagos.filter(pagocheque__isnull=False).exists():
    #         if self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=1).exists():
    #             valor = null_to_decimal(
    #                 self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=1).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #         if self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=2).exists():
    #             valor = null_to_decimal(
    #                 self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=2).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #         if self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=3).exists():
    #             valor = null_to_decimal(
    #                 self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=3).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #         if self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=4).exists():
    #             valor = null_to_decimal(
    #                 self.pagos.filter(pagocheque__isnull=False, pagocheque__tipocheque__id=4).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #     if self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                          pagotransferenciadeposito__deposito=False).exists():
    #         if self.pagos.filter(pagotransferenciadeposito__isnull=False, pagotransferenciadeposito__deposito=False,
    #                              pagotransferenciadeposito__tipotransferencia__id=1).exists():
    #             valor = null_to_decimal(self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                                                       pagotransferenciadeposito__deposito=False,
    #                                                       pagotransferenciadeposito__tipotransferencia__id=1).aggregate(
    #                 valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #         if self.pagos.filter(pagotransferenciadeposito__isnull=False, pagotransferenciadeposito__deposito=False,
    #                              pagotransferenciadeposito__tipotransferencia__id=2).exists():
    #             valor = null_to_decimal(self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                                                       pagotransferenciadeposito__deposito=False,
    #                                                       pagotransferenciadeposito__tipotransferencia__id=2).aggregate(
    #                 valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #         if self.pagos.filter(pagotransferenciadeposito__isnull=False, pagotransferenciadeposito__deposito=False,
    #                              pagotransferenciadeposito__tipotransferencia__id=3).exists():
    #             valor = null_to_decimal(self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                                                       pagotransferenciadeposito__deposito=False,
    #                                                       pagotransferenciadeposito__tipotransferencia__id=3).aggregate(
    #                 valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['20', valor])
    #     if self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                          pagotransferenciadeposito__deposito=True).exists():
    #         valor = null_to_decimal(self.pagos.filter(pagotransferenciadeposito__isnull=False,
    #                                                   pagotransferenciadeposito__deposito=True).aggregate(
    #             valor=Sum('valortotal'))['valor'], 2)
    #         lista.append(['20', valor])
    #     if self.pagos.filter(pagodineroelectronico__isnull=False).exists():
    #         valor = null_to_decimal(
    #             self.pagos.filter(pagodineroelectronico__isnull=False).aggregate(valor=Sum('valortotal'))['valor'], 2)
    #         lista.append(['17', valor])
    #     if self.pagos.filter(pagotarjeta__isnull=False).exists():
    #         if self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=1):
    #             if self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=1,
    #                                  pagotarjeta__procedencia__id=1).exists():
    #                 valor = null_to_decimal(self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=1,
    #                                                           pagotarjeta__procedencia__id=1).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #                 lista.append(['19', valor])
    #             if self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=1,
    #                                  pagotarjeta__procedencia__id=2).exists():
    #                 valor = null_to_decimal(self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=1,
    #                                                           pagotarjeta__procedencia__id=2).aggregate(
    #                     valor=Sum('valortotal'))['valor'], 2)
    #                 lista.append(['19', valor])
    #         if self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=2):
    #             valor = null_to_decimal(self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=2).aggregate(
    #                 valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['16', valor])
    #         if self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=3):
    #             valor = null_to_decimal(self.pagos.filter(pagotarjeta__isnull=False, pagotarjeta__tipo__id=3).aggregate(
    #                 valor=Sum('valortotal'))['valor'], 2)
    #             lista.append(['18', valor])
    #     if self.pagos.filter(pagocuentaporcobrar__isnull=False).exists():
    #         valor = null_to_decimal(
    #             self.pagos.filter(pagocuentaporcobrar__isnull=False).aggregate(valor=Sum('valortotal'))['valor'], 2)
    #         lista.append(['20', valor])
    #     if self.pagos.filter(pagonotacredito__isnull=False).exists():
    #         valor = null_to_decimal(
    #             self.pagos.filter(pagonotacredito__isnull=False).aggregate(valor=Sum('valortotal'))['valor'], 2)
    #         lista.append(['20', valor])
    #     return lista
    #
    # def puede_generar_valor_nota(self):
    #     total1 = self.total_nota_credito_manual()
    #     total2 = self.total_nota_credito_auto()
    #     suma = total1 + total2
    #     if suma < self.total:
    #         return True
    #     else:
    #         return False
    #
    # def tiene_nota_credito(self):
    #     if self.notacredito_set.exists():
    #         return True
    #     elif NotaCredito.objects.filter(Q(numerocompletofactura__icontains=self.numero), status=True).exists():
    #         return True
    #     return False
    #
    # def total_nota_credito_manual(self):
    #     if NotaCredito.objects.filter(Q(numerocompletofactura__icontains=self.numero), status=True).exists():
    #         notascreditosuma1 = null_to_decimal(
    #             NotaCredito.objects.filter(Q(numerocompletofactura__icontains=self.numero), status=True).aggregate(
    #                 valor=Sum('total'))['valor'], 2)
    #         return notascreditosuma1
    #     return 0
    #
    # def total_nota_credito_auto(self):
    #     if self.notacredito_set.exists():
    #         notascreditosuma2 = null_to_decimal(
    #             NotaCredito.objects.filter(factura=self, status=True, factura__valida=True).aggregate(
    #                 valor=Sum('total'))['valor'], 2)
    #         return notascreditosuma2
    #     return 0
    #
    # def tiene_cuenta_por_cobrar(self):
    #     return PagoCuentaporCobrar.objects.filter(pagos__factura=self).exists()
    #
    # def cuenta_por_cobrar(self):
    #     if self.tiene_cuenta_por_cobrar():
    #         return PagoCuentaporCobrar.objects.filter(pagos__factura=self)[0]
    #     return None
    #
    def save(self, *args, **kwargs):
        self.numerocompleto = self.numerocompleto.upper().strip()
        self.identificacion = self.identificacion.upper().strip()
        self.nombre = self.nombre.upper().strip()
        self.direccion = self.direccion.upper().strip()
        self.telefono = self.telefono.upper().strip()
        self.observacion = self.observacion.upper().strip() if self.observacion else ""
        if self.id:
            self.actualiza_subtotales()
        super(Factura, self).save(*args, **kwargs)

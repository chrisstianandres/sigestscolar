import base64
import json
import os
import subprocess
import uuid
from datetime import datetime
from unittest import TestCase

from django.conf.global_settings import DATABASES
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.base import View
from xhtml2pdf import pisa
from typing import Text
from zeep import Client

from apps.backEnd import nombre_empresa
from apps.extras import generar_nombre
from apps.factura.forms import Formulario
from apps.factura.models import Factura
from apps.inscripcion.views import crear_rubro
from apps.persona.models import Persona
from apps.producto.models import Producto, Inventario
from apps.rubro.models import Rubro, Pago
from sigestscolar import settings
from sigestscolar.settings import JR_JAVA_COMMAND, PASSSWORD_SIGNCLI, SERVER_URL_SIGNCLI, SERVER_USER_SIGNCLI, \
    SERVER_PASS_SIGNCLI, JR_RUN_SING_SIGNCLI, URL_SERVICIO_ENVIO_SRI_PRUEBAS, URL_SERVICIO_ENVIO_SRI_PRODUCCION, \
    URL_SERVICIO_AUTORIZACION_SRI_PRUEBAS, URL_SERVICIO_AUTORIZACION_SRI_PRODUCCION, TIPO_AMBIENTE_FACTURACION, \
    SITE_STORAGE


class ListviewValores(TemplateView):
    model = Rubro
    template_name = 'valores/list.html'
    template_name_add = 'rubro/form.html'
    form = Formulario

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                form = self.form(request.POST)
                if form.is_valid():
                    form.save()
                else:
                    data['error'] = form.errors
            elif action == 'edit':
                objeto = self.model.objects.get(pk=request.POST['pk'])
                form = self.form(request.POST, instance=objeto)
                if form.is_valid():
                    form.save()
                else:
                    data['error'] = form.errors
            elif action == 'delete':
                objeto = self.model.objects.get(pk=request.POST['pk'])
                objeto.delete()
            else:
                data['error'] = 'No ha seleccionado una opcion'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get(self, request, *args, **kwargs):
        data = {}
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data = self.get_context_data()
                    data['form'] = self.form
                    data['titulo'] = 'Nuevo Curso'
                    data['action_form'] = 'fa fa-user-lock'
                    return render(request, 'curso/form.html', data)
                if action == 'edit':
                    data = model_to_dict(self.model.objects.get(pk=request.GET['pk']))
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    return JsonResponse(data, safe=False)
                if action == 'detalle':
                    data = self.get_context_data()
                    list = self.model.objects.filter(status=True, persona_id=request.GET['id']).order_by('id')
                    data['datos_persona'] = datos_persona = list.first().persona
                    page_number = request.GET.get('page', 1)
                    paginator = Paginator(list, 10)
                    page_range = paginator.get_elided_page_range(number=page_number)
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['page_range'] = page_range
                    return render(request, 'valores/detalle_rubros.html', data)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).distinct('persona')
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(
                            Q(persona__nombre__icontains=search) | Q(persona__apellido1__icontains=search) | Q(
                                persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search)).order_by(
                            'persona__apellido1')
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nueva Factura'
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = 'fas fa-tags'
        data['boton'] = 'Guardar'
        data['titulo'] = 'Consulta de Valores'
        data['titulo_tabla'] = 'Estado de Cuenta'
        data['empresa'] = nombre_empresa()
        data['entidad'] = 'Valores'
        return data


class ListviewFacturacion(TemplateView):
    model = Factura
    template_name = 'valores/facturacionlist.html'
    template_name_add = 'valores/facturacionform.html'
    form = Formulario

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        with transaction.atomic():
            try:
                action = request.POST['action']
                if action == 'add':
                    datos = json.loads(request.POST['factura'])
                    per = Persona.objects.get(id=int(datos['cliente']))
                    efectivo = True if int(datos['tipopago']) == 1 else False
                    aplicaiva = None
                    pagos = []
                    if datos:
                        for rub in datos['rubros_select']:
                            if not rub['producto']:
                                rubro = Rubro.objects.get(id=int(rub['id']))
                                pago = generar_pago(request, rubro, efectivo=efectivo)
                            else:
                                aplicaiva = nombre_empresa().iva
                                prod = Producto.objects.get(id=int(rub['id']))
                                datos_rubro = [{'fechavence': datetime.now(), 'valor': rub['subtotal'],
                                                'observacion': str(prod.nombre_corto()),
                                                'cantidad': int(rub['cantidad'])}]
                                if prod.stock_producto() >= int(rub['cantidad']):
                                    rubrocreado = crear_rubro(persona=per, producto=prod, datos=datos_rubro)
                                else:
                                    transaction.set_rollback(True)
                                    data['error'] = 'Error el producto ' + str(
                                        prod.nombre_corto()) + ' no cuenta con el stock suficiente'
                                    break
                                if rubrocreado:
                                    cant = int(rub['cantidad'])
                                    pago = generar_pago(request, rubrocreado, iva=True, efectivo=efectivo)
                                    stock = Inventario.objects.filter(status=True, stockactual__gt=0)
                                    for st in stock:
                                        if st.stockactual >= cant:
                                            st.stockactual -= cant
                                        else:
                                            cant = cant - st.stockactual
                                            st.stockactual = 0
                                        st.save(request)
                            if pago:
                                pagos.append(pago)
                            else:
                                transaction.set_rollback(True)
                                data['error'] = 'Error al generar los pagos'
                                pagos = []
                                break
                        if len(pagos) > 0:
                            factura = Factura(numero=self.generar_numero(), fecha=datetime.now(),
                                              cliente=per, ivaaplicado=aplicaiva, impresa=True,
                                              identificacion=per.identificacion(), nombre=per.nombre_completo(),
                                              email=per.email, direccion=per.direccion, telefono=per.telefono,
                                              formapago=int(datos['tipopago']))
                            factura.save()
                            for p in pagos:
                                factura.pagos.add(p)
                            factura.actualiza_subtotales()
                            factura.generar_numero_completo()
                            if self.genera_tipo_pago(factura, datos):
                                factura.save(request)
                                data['resp'] = True
                                data['id'] = factura.pk
                            else:
                                transaction.set_rollback(True)
                                data['error'] = 'Error al generar la factura'
                    else:
                        transaction.set_rollback(True)
                        data['error'] = 'Datos Incompletos'

                elif action == 'verificar':
                    try:
                        objeto = self.model.objects.get(pk=request.POST['pk'])
                        objeto.verificada = True
                        objeto.save(request)
                        data['mensaje'] = 'Factura N° '+str(objeto.numerocompleto)+' fue verificada correctamente'
                    except Exception as e:
                        transaction.set_rollback(True)
                        data['error'] = 'Error al verificar la factura'
                elif action == 'anular':
                    try:
                        objeto = self.model.objects.get(pk=request.POST['pk'])
                        objeto.estado = 3
                        objeto.save(request)
                        for pag in objeto.pagos.all():
                            rubro = pag.rubro
                            if not rubro.producto:
                                rubro.saldo += pag.valortotal
                                rubro.cancelado = False
                                pag.status = False
                            else:
                                rubro.status = False
                                cantidad = rubro.cantidad
                                for st in rubro.producto.inventario_set.filter(status=True):
                                    if st.stockactual + cantidad < st.cantidad:
                                        st.stockactual += cantidad
                                    else:
                                        cal = cantidad - st.cantidad
                                        ingreso = cantidad - cal
                                        cantidad = cal
                                        st.stockactual = ingreso
                                    st.save(request)
                                pag.status = False
                            rubro.save(request)
                            pag.save(request)

                        data['mensaje'] = 'Factura N° '+str(objeto.numerocompleto)+' fue anulada correctamente'
                    except Exception as e:
                        transaction.set_rollback(True)
                        data['error'] = 'Error al anular la factura'
                else:
                    data['error'] = 'No ha seleccionado una opcion'
            except Exception as e:
                data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get(self, request, *args, **kwargs):
        data = {}
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data = self.get_context_data()
                    data['form'] = self.form
                    data['titulo'] = 'Nueva Factura'
                    data['titulo_form'] = 'Nueva Factura'
                    data['action_form'] = 'fas fa-wallet'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = model_to_dict(self.model.objects.get(pk=request.GET['pk']))
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    return JsonResponse(data, safe=False)
                if action == 'detalle':
                    data = self.get_context_data()
                    list = self.model.objects.filter(status=True, persona_id=request.GET['id']).order_by('id')
                    data['datos_persona'] = datos_persona = list.first().persona
                    page_number = request.GET.get('page', 1)
                    paginator = Paginator(list, 10)
                    page_range = paginator.get_elided_page_range(number=page_number)
                    page_obj = paginator.get_page(page_number)
                    data['page_obj'] = page_obj
                    data['page_range'] = page_range
                    return render(request, 'valores/detalle_rubros.html', data)
                if action == 'rubros_cliente':
                    data = {}
                    id = request.GET['id']
                    ids = json.loads(request.GET['ids'])
                    persona = Persona.objects.get(id=id)
                    rubros = persona.rubro_set.filter(status=True, cancelado=False).exclude(id__in=ids).order_by(
                        'fechavence')
                    if rubros.exists():
                        elemento = persona.rubro_set.first()
                        template = get_template('valores/rubros_persona.html')
                        data = {'data': template.render({'rubros': rubros}),
                                'totalpagado': elemento.total_pagado_finanzas(),
                                'totaldeuda': elemento.total_adeudado_finanzas(),
                                'totalvencido': elemento.total_vencido_finanzas(),
                                'cedula': persona.documento(), 'tipo_doc': persona.tipo_identificacion(),
                                'telefono': persona.telefono}
                    else:
                        data = {'resp': False, 'mensaje': 'Esta persona no tiene rubros pendientes de pago',
                                'totalpagado': 0, 'totaldeuda': 0, 'totalvencido': 0, 'cedula': persona.documento(),
                                'telefono': persona.telefono, 'tipo_doc': persona.tipo_identificacion()}
                    return JsonResponse(data, safe=False)
                if action == 'lista_productos':
                    data = {}
                    ids = json.loads(request.GET['ids'])
                    productos = Producto.objects.filter(status=True).exclude(id__in=ids)
                    if productos.exists():
                        template = get_template('valores/productos_lista.html')
                        data = {'data': template.render({'productos': productos})}
                    else:
                        data = {'resp': False, 'mensaje': 'No tienes productos para mostrar'}
                    return JsonResponse(data, safe=False)
                if action == 'search_cliente':
                    data = []
                    search = request.GET['term']
                    persona = Persona.objects.filter(Q(status=True),
                                                     Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(
                                                         apellido2__icontains=search) | Q(cedula__icontains=search))
                    for cli in persona:
                        data.append({'id': cli.pk, 'text': cli.nombre_completo()})
                    return JsonResponse(data, safe=False)
                if action == 'search_producto':
                    data = []
                    ids = json.loads(request.GET['ids'])
                    search = request.GET['term']
                    producto = Producto.objects.filter(Q(status=True), Q(nombre__icontains=search) | Q(
                        codigo__icontains=search)).exclude(id__in=ids)
                    for pro in producto[0:10]:
                        if pro.stock_producto() > 0:
                            data.append({'id': pro.pk, 'text': pro.nombre_corto()})
                    return JsonResponse(data, safe=False)
                if action == 'get_producto':
                    data = {}
                    producto = Producto.objects.get(id=request.GET['id'])
                    data = {'id': producto.id, 'nombre': producto.nombre_corto(), 'stock': producto.stock_producto(),
                            'valoru': producto.valor, 'cantidad': 1, 'valor': float(producto.valor),
                            'saldo': float(producto.valortotal()), 'subtotal': float(producto.valor),
                            'iva': float(producto.valoriva()), 'total': float(producto.valortotal()), 'producto': True}
                    return JsonResponse(data, safe=False)
                if action == 'get_productos_lista':
                    productos = []
                    ids = json.loads(request.GET['ids'])
                    query = Producto.objects.filter(id__in=ids)
                    for producto in query:
                        productos.append(
                            {'id': producto.id, 'nombre': producto.nombre_corto(), 'stock': producto.stock_producto(),
                             'valoru': producto.valor, 'cantidad': 1, 'valor': float(producto.valor),
                             'saldo': float(producto.valortotal()), 'subtotal': float(producto.valor),
                             'iva': float(producto.valoriva()), 'total': float(producto.valortotal()),
                             'producto': True})
                    return JsonResponse(productos, safe=False)
                if action == 'get_rubros':
                    rubros = []
                    ids = json.loads(request.GET['ids'])
                    query = Rubro.objects.filter(id__in=ids)
                    for r in query:
                        rubros.append({'id': r.id, 'nombre': r.nombre, 'stock': 0, 'valoru': r.subtotal(),
                                       'cantidad': int(r.cantidad), 'valor': float(r.valortotal),
                                       'saldo': float(r.saldo), 'subtotal': float(r.subtotal()),
                                       'iva': float(r.valoriva), 'total': float(r.valortotal), 'producto': False})
                    return JsonResponse(rubros, safe=False)
                if action == 'rubros_factura':
                    data = {}
                    id = request.GET['id']
                    factura = self.model.objects.get(id=id)
                    template = get_template('valores/rubros_factura.html')
                    data = {'data': template.render({'factura': factura})}
                    return JsonResponse(data, safe=False)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).order_by('-fecha')
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(Q(cliente__nombres__icontains=search) | Q(
                            cliente__apellido1__icontains=search) | Q(
                            cliente__apellido2__icontains=search) | Q(
                            cliente__cedula__icontains=search) | Q(numerocompleto__icontains=search)
                                           ).order_by('-fecha')
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nueva Factura'
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = 'fas fa-wallet'
        data['boton'] = 'Guardar'
        data['titulo'] = 'Listado de Facturacion'
        data['titulo_tabla'] = 'Lista de Facturas'
        data['empresa'] = nombre_empresa()
        data['entidad'] = 'Facturacion'
        return data

    def generar_numero(self):
        return self.model.objects.all().order_by('-id').first().numero + 1 if self.model.objects.all().order_by('-id').first() else 1

    def genera_tipo_pago(self, factura, datos):
        if factura.formapago == 2:
            if 'referencia_transferencia' in datos:
                factura.referencia_transferencia = datos['referencia_transferencia']
                return True
        elif factura.formapago == 3:
            if 'referencia_deposito' in datos:
                factura.referencia_deposito = datos['referencia_deposito']
                return True
        elif factura.formapago == 4:
            if 'boucher' in datos:
                factura.boucher = datos['boucher']
                return True
        else:
            factura.verificada = True
            factura.save()
            return True
        return False


def generar_pago(request, rubro, iva=None, efectivo=None):
    with transaction.atomic():
        try:
            hoy = datetime.now()
            if iva is None:
                pago = Pago(rubro=rubro, fecha=hoy, subtotal0=rubro.valor, valortotal=rubro.valortotal)
            else:
                pago = Pago(rubro=rubro, fecha=hoy, subtotaliva=rubro.valor, iva=rubro.valoriva,
                            valortotal=rubro.valortotal)
            pago.efectivo = efectivo
            pago.save(request)
            rubro.saldo = 0
            rubro.cancelado = True
            rubro.save(request)
            return pago.pk
        except Exception as e:
            transaction.set_rollback(True)
        return None

unicode = str

def crear_representacion_xml_factura(id, proceso_siguiente=False):
    factura = Factura.objects.get(pk=int(id))
    template = get_template("valores/xml/factura.html")
    d = ({'comprobante': factura,
                 'institucion': nombre_empresa()})
    xml_content = template.render(d)
    factura.xml = xml_content
    factura.weburl = uuid.uuid4().hex
    factura.xmlgenerado = True
    factura.save()
    if proceso_siguiente:
        firmar_comprobante_factura(factura.id)


def firmar_comprobante_factura(id):
    factura = Factura.objects.get(pk=int(id))
    token = nombre_empresa().token
    if not token:
        return False

    import os
    runjrcommand = [JR_JAVA_COMMAND, '-jar',
                    os.path.join(JR_RUN_SING_SIGNCLI, 'SignCLI.jar'),
                    token.file.name,
                    PASSSWORD_SIGNCLI,
                    SERVER_URL_SIGNCLI + "/sign_factura/" + factura.weburl]
    if SERVER_USER_SIGNCLI and SERVER_PASS_SIGNCLI:
        runjrcommand.append(SERVER_USER_SIGNCLI)
        runjrcommand.append(SERVER_PASS_SIGNCLI)
    try:
        runjr = subprocess.call(runjrcommand)
    except:
       pass


def envio_comprobante_sri_factura(id, proceso_siguiente=False):
    try:
        factura = Factura.objects.get(pk=int(id))
        xml = factura.xmlfirmado
        test = TestCase
        # d = base64.b64encode(xml.encode('utf-8'))
        if factura.tipoambiente == 1:
            WSDL = URL_SERVICIO_ENVIO_SRI_PRUEBAS #'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
        else:
            WSDL = URL_SERVICIO_ENVIO_SRI_PRODUCCION #'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
        client = Client(WSDL)
        d = base64.b64encode(factura.xmlfirmado.encode('utf-8'))
        respuesta = client.service.validarComprobante(factura.xmlfirmado.encode('utf-8'))
        factura.falloenviodasri = False
        factura.mensajeenvio = ''
        factura.enviadasri = True
        estado = "RECIBIDA"
        yaenviado = False
        if respuesta.comprobantes:
            for m in respuesta.comprobantes.comprobante[0].mensajes.mensaje:
                if m.identificador == '43' or m.identificador == '45':
                    yaenviado = True
                    factura.falloenviodasri = False
                    factura.mensajeenvio = ''
                    factura.enviadasri = True
                else:
                    if unicode(m.mensaje):
                        factura.mensajeenvio = unicode(m.mensaje)
                    try:
                        if unicode(m.informacionAdicional):
                            factura.mensajeenvio += ' ' + unicode(m.informacionAdicional)
                    except Exception as ex:
                        pass
        try:
            estado = unicode(respuesta.estado)
        except Exception as ex:
            pass
        if estado == "RECIBIDA" or yaenviado:
            factura.falloenviodasri = False
            factura.enviadasri = True
            factura.mensajeenvio = ''
            factura.save()
            if proceso_siguiente:
                autorizacion_comprobante_factura(factura.id, proceso_siguiente=proceso_siguiente)
        else:
            factura.falloenviodasri = True
            factura.estado = 2
            factura.save()
    except Exception as ex:
        pass

def autorizacion_comprobante_factura(id, proceso_siguiente=False):
    factura = Factura.objects.get(pk=int(id))
    if not factura.enviadasri:
        return False
    if factura.tipoambiente == 1:
        WSDL = URL_SERVICIO_AUTORIZACION_SRI_PRUEBAS #'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
    else:
        WSDL = URL_SERVICIO_AUTORIZACION_SRI_PRODUCCION #'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
    client = Client(WSDL)
    respuesta = client.service.autorizacionComprobante(factura.claveacceso)
    factura.autorizada = False
    factura.falloautorizacionsri = True
    if int(respuesta.numeroComprobantes) > 0:
        autorizacion = respuesta.autorizaciones.autorizacion[0]
        if autorizacion.estado == 'AUTORIZADO':
            factura.autorizada = True
            factura.falloautorizacionsri = False
            factura.autorizacion = unicode(autorizacion.numeroAutorizacion) if autorizacion.estado == 'AUTORIZADO' else ''
            factura.fechaautorizacion = autorizacion.fechaAutorizacion
            factura.save()
            if proceso_siguiente:
                envio_comprobante_cliente_factura(factura.id)
        elif type(autorizacion.mensajes) != Text:
            factura.falloautorizacionsri = True
            factura.estado = 2
            for mensaje in autorizacion.mensajes.mensaje:
                if unicode(mensaje.mensaje):
                    factura.mensajeautorizacion = unicode(mensaje.mensaje)
                if unicode(mensaje.informacionAdicional):
                    factura.mensajeautorizacion += ' ' + unicode(mensaje.informacionAdicional)
    factura.save()


def envio_comprobante_cliente_factura(id):
    factura = Factura.objects.get(pk=int(id))
    direccion = os.path.join(SITE_STORAGE, 'media', 'comprobantes', 'factura')
    if not factura.xmlarchivo:
        xmlname = generar_nombre('Factura', 'fichero.xml')
        filename_xml = os.path.join(direccion, xmlname)
        f = open(filename_xml, "wb")
        f.write(factura.xmlfirmado.encode('utf-8'))
        f.close()
        factura.xmlarchivo.name = 'comprobantes/factura/%s' % xmlname
    if not factura.pdfarchivo:
        try:
            pdfname = generar_nombre('Factura', 'fichero')
            filename_pdf = os.path.join(direccion, pdfname)
            reporte = Reporte.objects.get(pk=REPORTE_PDF_FACTURA_ID)
            tipo = 'pdf'
            runjrcommand = [JR_JAVA_COMMAND, '-jar',
                            os.path.join(JR_RUN, 'jasperstarter.jar'),
                            'pr', reporte.archivo.file.name,
                            '--jdbc-dir', JR_RUN,
                            '-f', tipo,
                            '-t', 'postgres',
                            '-H', DATABASES['default']['HOST'],
                            '-n', DATABASES['default']['NAME'],
                            '-u', DATABASES['default']['USER'],
                            '-p', DATABASES['default']['PASSWORD'],
                            '-o', filename_pdf]
            mensaje = ''
            for m in runjrcommand:
                mensaje += ' ' + m
            mensaje +=' -P id=' + str(id)
            runjr = subprocess.call(mensaje.encode("latin1"), shell=True)
            sp = os.path.split(reporte.archivo.file.name)
            factura.pdfarchivo.name = 'comprobantes/factura/%s.pdf' % pdfname
        except Exception as ex:
            pass
    if factura.pdfarchivo and factura.xmlarchivo:
        listacorreos = []

        listacorreos.append(factura.email)
        listacorreos.append('tesoreria@unemi.edu.ec')

        send_html_mail("Comprobante Electrónico", "emails/comprobanteelectronico_factura.html", {'sistema': u'Sistema de Gestión Administrativa', 'factura': factura, 't': miinstitucion()}, listacorreos, [], cuenta=CUENTAS_CORREOS[1][1])
        factura.enviadacliente = True
        factura.estado = 2
        factura.save()


def pagaryfacturar(request, caja, extra=None):
    if 'aniofiscalpresupuesto' in request.session:
        anio = request.session['aniofiscalpresupuesto']
    else:
        anio = anio_ejercicio().anioejercicio
    sesion_caja = caja.sesion_caja()
    if extra:
        pagos = extra['pagos']
        idrubros = extra['rubros']
    else:
        pagos = json.loads(request.POST['pagos'])
        idrubros = json.loads(request.POST['rubros'])
    nofactura = False
    for rubro in Rubro.objects.filter(id__in=[int(x['rubro']) for x in idrubros]):
        rubro_seleccionado = rubro
        if rubro.tipo.nofactura:
            nofactura = True
        if not rubro.tipo.partida_saldo(anio):
            return {'result': 'bad', "mensaje": u"El Rubro %s no cuenta con un Saldo de Partida Asociado" % rubro.nombre}

    if extra:
        personacliente = Persona.objects.get(pk=int(extra['id']))
    else:
        personacliente = Persona.objects.get(pk=int(request.POST['id']))

    # SE GENERA FACTURA
    if not nofactura:
        secuencia = secuencia_recaudacion(request, sesion_caja.caja.puntoventa)
        secuencia.factura += 1
        secuencia.save(request)
        if Factura.objects.filter(puntoventa=secuencia.puntoventa, numero=secuencia.factura).exists():
            return {'result': 'bad', "mensaje": u"Numero de factura ya existe."}
        clientefactura = personacliente.cliente_factura(request)
        if not extra:
            clientefactura.nombre = request.POST['nombre']
            clientefactura.identificacion = request.POST['identificacion']
            clientefactura.tipo = int(request.POST['tipoidentificacion'])
            clientefactura.direccion = request.POST['direccion']
            clientefactura.telefono = request.POST['tel']
            clientefactura.email = request.POST['email']
        clientefactura.save(request)

        direccion_factura = "N"
        if clientefactura.direccion:
            if len(clientefactura.direccion.strip()) > 0: direccion_factura = clientefactura.direccion

        factura = Factura(numerocompleto=caja.puntoventa.establecimiento.strip() + "-" + caja.puntoventa.puntoventa.strip() + "-" + str(secuencia.factura).zfill(9),
                          numero=secuencia.factura,
                          puntoventa=caja.puntoventa,
                          fecha=sesion_caja.fecha,
                          valida=True,
                          pagada=True,
                          electronica=True,
                          cliente=personacliente,
                          impresa=False,
                          sesioncaja=sesion_caja,
                          identificacion=clientefactura.identificacion,
                          tipo=clientefactura.tipo,
                          nombre=clientefactura.nombre,
                          # direccion=clientefactura.direccion if clientefactura.direccion,
                          direccion=direccion_factura,
                          telefono=clientefactura.telefono,
                          email=clientefactura.email,
                          tipoambiente=TIPO_AMBIENTE_FACTURACION)
        factura.save(request)
    else:
        # SE GENERA RECIBO DE CAJA
        secuencia = secuencia_recaudacion(request, sesion_caja.caja.puntoventa)
        secuencia.recibocaja += 1
        secuencia.save(request)
        if ReciboCaja.objects.filter(numero=secuencia.recibocaja).exists():
            return {'result': 'bad', "mensaje": u"Numero de recibo caja ya existe."}
        # clienterecibo = persona.cliente_factura(request)
        # if not extra:
        #     clienterecibo.nombre = request.POST['nombre']
        #     clienterecibo.identificacion = request.POST['identificacion']
        #     clienterecibo.tipo = int(request.POST['tipoidentificacion'])
        #     clienterecibo.direccion = request.POST['direccion']
        #     clienterecibo.telefono = request.POST['tel']
        #     clienterecibo.email = request.POST['email']
        #     clienterecibo.save(request)

        if personacliente.cedula:
            tipoidentificacion = 1
            identificacion = personacliente.cedula
        elif personacliente.ruc:
            tipoidentificacion = 2
            identificacion = personacliente.ruc
        else:
            tipoidentificacion = 3
            identificacion = personacliente.pasaporte

        recibocaja = ReciboCaja(numerocompleto=caja.puntoventa.establecimiento.strip() + "-" + caja.puntoventa.puntoventa.strip() + "-" + str(secuencia.recibocaja).zfill(9),
                                numero=secuencia.recibocaja,
                                sesioncaja=sesion_caja,
                                persona=personacliente,
                                partida=rubro_seleccionado.tipo.partida_saldo(anio).partidassaldo,
                                concepto=rubro_seleccionado.tipo.nombre)
        recibocaja.save(request)

    valorpagorecibo = 0

    for pago in pagos:
        tp = None
        fechapago = sesion_caja.fecha
        valorpago = 0
        if int(pago['tipo']) == FORMA_PAGO_EFECTIVO:
            valorpago = Decimal(pago['valor'])
            fechapago = sesion_caja.fecha
        elif int(pago['tipo']) == FORMA_PAGO_CUENTA_PORCOBRAR:
            tp = PagoCuentaporCobrar(fecha=sesion_caja.fecha,
                                     valor=Decimal(pago['valor']))
            tp.save(request)
            fechapago = sesion_caja.fecha
            if not nofactura:
                factura.pagada = False
                factura.save(request)
            valorpago = Decimal(pago['valor'])
        elif int(pago['tipo']) == FORMA_PAGO_CHEQUE:
            tp = PagoCheque(numero=pago['numero'],
                            cuenta=pago['cuenta'],
                            banco_id=int(pago['banco']),
                            tipocheque_id=int(pago['tipocheque']),
                            fecha=sesion_caja.fecha,
                            fechacobro=convertir_fecha(pago['fechacobro']),
                            emite=pago['emite'],
                            valor=Decimal(pago['valor']),
                            protestado=False)
            tp.save(request)
            valorpago = Decimal(pago['valor'])
            fechapago = sesion_caja.fecha
        elif int(pago['tipo']) == FORMA_PAGO_ELECTRONICO:
            tp = PagoDineroElectronico(referencia=pago['referenciaelec'],
                                       fecha=sesion_caja.fecha,
                                       valor=Decimal(pago['valor']))
            tp.save(request)
            fechapago = sesion_caja.fecha
            valorpago = Decimal(pago['valor'])
        elif int(pago['tipo']) == FORMA_PAGO_DEPOSITO:
            tp = PagoTransferenciaDeposito(referencia=pago['referenciadep'],
                                           fecha=convertir_fecha(pago['fechadep']),
                                           cuentabanco_id=int(pago['cuentadep']),
                                           valor=Decimal(pago['valor']),
                                           deposito=True,
                                           recaudacionventanilla=True if extra else False)
            tp.save(request)
            fechapago = convertir_fecha(pago['fechadep'])
            valorpago = Decimal(pago['valor'])
        elif int(pago['tipo']) == FORMA_PAGO_TRANSFERENCIA:
            tp = PagoTransferenciaDeposito(referencia=pago['referenciatrans'],
                                           fecha=convertir_fecha(pago['fechatrans']),
                                           cuentabanco_id=int(pago['cuentatrans']),
                                           tipotransferencia_id=int(pago['tipotran']),
                                           valor=Decimal(pago['valor']),
                                           deposito=False)
            tp.save(request)
            fechapago = convertir_fecha(pago['fechatrans'])
            valorpago = Decimal(pago['valor'])
        elif int(pago['tipo']) == FORMA_PAGO_TARJETA:
            tp = PagoTarjeta(banco_id=int(pago['bancotar']),
                             tipo_id=int(pago['tipotar']),
                             procedencia_id=int(pago['procedencia']),
                             poseedor=pago['poseedor'],
                             valor=Decimal(pago['valor']),
                             procesadorpago_id=int(pago['procesador']),
                             referencia=pago['referenciatarj'],
                             fecha=sesion_caja.fecha)
            tp.save(request)
            fechapago = sesion_caja.fecha
            valorpago = Decimal(pago['valor'])
        # rubro_pagado = []
        valorpagorecibo += valorpago
        for rubro in Rubro.objects.filter(id__in=[int(x['rubro']) for x in idrubros], cancelado=False).order_by('fechavence'):
            # rubro_pagado.append(rubro.id)
            # qs_anterior = list(Rubro.objects.filter(pk=rubro.id).values())
            iva = 0
            if rubro.saldo >= valorpago:
                valorapagar = Decimal(valorpago)
            else:
                valorapagar = Decimal(rubro.saldo)
            if null_to_decimal(valorpago, 2) > 0:
                if rubro.iva.porcientoiva == 0:
                    subtotaliva = 0
                    subtotal0 = valorapagar
                    iva = 0
                else:
                    subtotaliva = Decimal(valorapagar / (rubro.iva.porcientoiva + 1)).quantize(Decimal('.01'))
                    iva = Decimal(valorapagar - subtotaliva).quantize(Decimal('.01'))
                    subtotal0 = 0
                pagorubro = Pago(fecha=fechapago,
                                 subtotal0=subtotal0,
                                 subtotaliva=subtotaliva,
                                 iva=iva,
                                 valordescuento=0,
                                 valortotal=valorapagar,
                                 rubro=rubro,
                                 efectivo=True if not tp else False,
                                 sesion=sesion_caja)
                pagorubro.save(request)
                if pagorubro.rubro.iva.porcientoiva:
                    if not nofactura:
                        factura.ivaaplicado = pagorubro.rubro.iva

                rubro.save(request)
                rubro.bloqueo_matricula_actualizar()
                # GUARDA AUDITORIA RUBRO
                # qs_nuevo = list(Rubro.objects.filter(pk=rubro.id).values())
                # salvaRubros(request, rubro, 'pagaryfacturar', qs_nuevo=qs_nuevo, qs_anterior=qs_anterior)
                # GUARDA AUDITORIA RUBRO

                matricula = rubro.matricula

                if matricula:
                    coordinacion = matricula.inscripcion.carrera.mi_coordinacion2()
                    if coordinacion == 7:
                        if matricula.bloqueo_matricula_pago():
                            matricula.bloqueomatricula=True
                            log(u'%s: %s' % (u'Bloquear matricula ventanilla', matricula), request, "edit")
                        else:
                            matricula.bloqueomatricula = False
                        matricula.save(request)

                BANCO_ACTUALIZA_MATRICULA = variable_valor(
                    'BANCO_ACTUALIZA_MATRICULA')

                if BANCO_ACTUALIZA_MATRICULA:
                    if matricula:
                        matricula.actualiza_matricula()
                        if matricula.inscripcion.coordinacion_id == 9:
                            tipourl = 2
                        else:
                            tipourl = 1
                        for materiaasignada in matricula.mis_materias_sin_retiro():
                            materiaasignada.materia.crear_actualizar_un_estudiante_curso(moodle, tipourl, matricula)
                        if matricula.bloqueo_matricula_pago():
                            matricula.bloqueomatricula = True
                            log(u'%s: %s' % (u'Bloquear matricula Subida Archivo', matricula), request, "edit")

                if not nofactura:
                    factura.pagos.add(pagorubro)

                if tp:
                    tp.pagos.add(pagorubro)
                valorpago -= valorapagar
        # for rubro_p in rubro_pagado:
        #     rubro1 = Rubro.objects.filter(pk=int(rubro_p))[0]
        #     matricula = rubro1.matricula
        #     if matricula:
        #         if Rubro.objects.filter(matricula=matricula, status=True, cancelado=False).exists():
        #             matricula.estado_matricula = 1
        #             matricula.save()
        #         else:
        #             matricula.estado_matricula = 2
        #             matricula.save()
        if not nofactura:
            factura.save(request)
            factura.claveacceso = factura.genera_clave_acceso_factura()
            factura.save(request)
            crear_representacion_xml_factura(factura.id)
        else:
            recibocaja.valor = valorpagorecibo
            recibocaja.save(request)

    if nofactura:
        numero = recibocaja.numerocompleto
        idfactura = recibocaja.id
        tipo = 2
    else:
        numero = factura.numerocompleto
        idfactura = factura.id
        tipo = 1
    log(u'Se facturo para: %s - %s con número factura' % (personacliente.nombre_completo_inverso(), numero), request, "add")
    return {'result': 'ok', 'numerofactura': numero, 'id': idfactura, "tipo": tipo}


class PrintFactura(View):

    def link_callback(self, uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access those
        resources
        """
        result = finders.find(uri)
        if result:
            if not isinstance(result, (list, tuple)):
                result = [result]
            result = list(os.path.realpath(path) for path in result)
            path = result[0]
        else:
            sUrl = settings.STATIC_URL  # Typically /static/
            sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
            mUrl = settings.MEDIA_URL  # Typically /media/
            mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

            if uri.startswith(mUrl):
                path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                path = os.path.join(sRoot, uri.replace(sUrl, ""))
            else:
                return uri

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
        return path

    def get(self, request, *args, **kwargs):
        try:
            tipo = int(request.GET['tipo'])
            factura = Factura.objects.get(pk=self.kwargs['pk'])
            template = get_template('bases/factura.html')
            context = {'title': 'Comprobante de Venta',
                       'factura': factura,
                       'tipo_comprobante': True if tipo == 1 else False,
                       'icon': 'media/logo.png' if not tipo == 1 else 'media/logo_b_n.png',
                       'empresa': nombre_empresa(),
                       }
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Factura_No._'+factura.numerocompleto+'.pdf"'
            pisa_status = pisa.CreatePDF(html, dest=response, link_callback=self.link_callback)
            return response
        except:
            pass
        return HttpResponseRedirect(reverse_lazy('facturacion'))

import json
import os
from datetime import datetime

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

from apps.backEnd import nombre_empresa
from apps.factura.forms import Formulario
from apps.factura.models import Factura
from apps.inscripcion.views import crear_rubro
from apps.persona.models import Persona
from apps.producto.models import Producto, Inventario
from apps.rubro.models import Rubro, Pago
from sigestscolar import settings


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
        try:
            action = request.POST['action']
            if action == 'add':
                with transaction.atomic():
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
                                    data['error'] = 'Error el producto '+str(prod.nombre_corto()) +' no cuenta con el stock suficiente'
                                    break
                                if rubrocreado:
                                    cant = int(rub['cantidad'])
                                    pago = generar_pago(request, rubrocreado, iva=True, efectivo=efectivo)
                                    stock = Inventario.objects.filter(status=True, cantidad__gt=0)
                                    for st in stock:
                                        if st.cantidad >= cant:
                                            st.cantidad -= cant
                                            st.save(request)
                                        else:
                                            st.cantidad = 0
                                            cant = cant-st.cantidad
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
                        data['error'] = 'Datos Incompletos'

            elif action == 'verificar':
                objeto = self.model.objects.get(pk=request.POST['pk'])
                objeto.verificada = True
                objeto.save(request)
                data['mensaje'] = 'Factura N° '+str(objeto.numerocompleto)+' fue verificada correctamente'
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
                        list = list.filter(Q(cliente__persona__nombre__icontains=search) | Q(
                            cliente__persona__apellido1__icontains=search) | Q(
                            cliente__persona__apellido2__icontains=search) | Q(
                            cliente__persona__cedula__icontains=search) | Q(numerocompleto__icontains=search)
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
        return self.model.objects.all().order_by('-id').first().numero + 1

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

import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from apps.backEnd import nombre_empresa
from apps.factura.forms import Formulario
from apps.factura.models import Factura
from apps.persona.models import Persona
from apps.producto.models import Producto
from apps.rubro.models import Rubro


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
                        list = list.filter(Q(persona__nombre__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search)).order_by('persona__apellido1')
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
                form = self.form(request.POST)
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
                    rubros = persona.rubro_set.filter(status=True, cancelado=False).exclude(id__in=ids)
                    if rubros.exists():
                        elemento = persona.rubro_set.first()
                        template = get_template('valores/rubros_persona.html')
                        data = {'data': template.render({'rubros': rubros}), 'totalpagado': elemento.total_pagado_finanzas(),
                                'totaldeuda': elemento.total_adeudado_finanzas(), 'totalvencido': elemento.total_vencido_finanzas()}
                    else:
                        data = {'resp': False, 'mensaje': 'Esta persona no tiene rubros pendientes de pago', 'totalpagado': 0, 'totaldeuda': 0, 'totalvencido': 0}
                    return JsonResponse(data, safe=False)
                if action == 'lista_productos':
                    data = {}
                    ids = json.loads(request.GET['ids'])
                    productos = Producto.objects.filter(status=True).exclude(id__in=ids)
                    if productos.exists():
                        template = get_template('valores/productos_lista.html')
                        data = {'data': template.render({'productos': productos})}
                    else:
                        data = {'resp': False, 'mensaje': 'No tienes productos registrados'}
                    return JsonResponse(data, safe=False)
                if action == 'search_cliente':
                    data = []
                    search = request.GET['term']
                    persona = Persona.objects.filter(Q(status=True), Q(nombres__icontains=search) | Q(apellido1__icontains=search) | Q(apellido2__icontains=search) | Q(cedula__icontains=search) )
                    for cli in persona:
                        data.append({'id': cli.pk, 'text': cli.nombre_completo()})
                    return JsonResponse(data, safe=False)
                if action == 'search_producto':
                    data = []
                    ids = json.loads(request.GET['ids'])
                    search = request.GET['term']
                    producto = Producto.objects.filter(Q(status=True), Q(nombre__icontains=search) | Q(codigo__icontains=search)).exclude(id__in=ids)
                    for pro in producto[0:10]:
                        if pro.stock_producto() > 0:
                            data.append({'id': pro.pk, 'text': pro.nombre_corto()})
                    return JsonResponse(data, safe=False)
                if action == 'get_producto':
                    data = {}
                    producto = Producto.objects.get(id=request.GET['id'])
                    data = {'id': producto.id, 'nombre': producto.nombre_corto(), 'stock': producto.stock_producto(), 'valoru': producto.valor, 'cantidad': 1, 'valor': float(producto.valor), 'saldo': float(producto.valortotal()), 'subtotal': float(producto.valor), 'iva': float(producto.valoriva()), 'total': float(producto.valortotal()), 'producto': True}
                    return JsonResponse(data, safe=False)
                if action == 'get_productos_lista':
                    productos = []
                    ids = json.loads(request.GET['ids'])
                    query = Producto.objects.filter(id__in=ids)
                    for producto in query:
                        productos.append({'id': producto.id, 'nombre': producto.nombre_corto(), 'stock': producto.stock_producto(), 'valoru': producto.valor, 'cantidad': 1, 'valor': float(producto.valor), 'saldo': float(producto.valortotal()), 'subtotal': float(producto.valor), 'iva': float(producto.valoriva()), 'total': float(producto.valortotal()), 'producto': True})
                    return JsonResponse(productos, safe=False)
                if action == 'get_rubros':
                    rubros = []
                    ids = json.loads(request.GET['ids'])
                    query = Rubro.objects.filter(id__in=ids)
                    for r in query:
                        rubros.append({'id': r.id, 'nombre': r.nombre, 'stock': 0, 'valoru': r.subtotal(), 'cantidad': int(r.cantidad), 'valor': float(r.valortotal), 'saldo': float(r.saldo), 'subtotal': float(r.subtotal()), 'iva': float(r.valoriva), 'total': float(r.valortotal), 'producto': False})
                    return JsonResponse(rubros, safe=False)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True)
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(Q(cliente__persona__nombre__icontains=search) | Q(cliente__persona__apellido1__icontains=search) | Q(cliente__persona__apellido2__icontains=search) | Q(cliente__persona__cedula__icontains=search)).order_by('fecha')
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
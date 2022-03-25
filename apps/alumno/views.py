from datetime import datetime

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from apps.backEnd import nombre_empresa, calcular_edad
from apps.externo.forms import Formulario
from apps.extras import PrimaryKeyEncryptor
from apps.persona.models import Persona
from apps.alumno.models import Alumno
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Listview(TemplateView):
    model = Alumno
    template_name = 'alumno/list.html'
    template_name_add = 'externo/form.html'
    icon = 'fas fa-graduations-cap'
    entidad = 'Alumnos'
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
                    edad = calcular_edad(form.cleaned_data['nacimiento'])
                    if edad <= 20 or edad >= 4:
                        persona = form.save()
                        prof = Alumno(persona_id=persona.pk, fechaingreso=datetime.now(), activo=True)
                        prof.save()
                    else:
                        data['error'] = 'Debe ser mayor de edad para ser docente'
                else:
                    data['error'] = form.errors
            elif action == 'edit':
                pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.POST['pk'])
                objeto = Persona.objects.get(pk=pk)
                form = self.form(request.POST, instance=objeto)
                if form.is_valid():
                    edad = calcular_edad(form.cleaned_data['nacimiento'])
                    if edad <= 20 or edad >= 4:
                        form.save()
                    else:
                        data['error'] = 'Debe ser mayor de 4 años'
                else:
                    data['error'] = form.errors
            elif action == 'delete':
                pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.POST['pk'])
                objeto = Persona.objects.get(pk=pk)
                profesor = self.model.objects.get(persona=objeto)
                profesor.delete()
            else:
                data['error'] = 'No ha seleccionado una opcion'
        except Exception as e:
            data['error'] = str(e)
            transaction.set_rollback(True)
        return JsonResponse(data, safe=False)

    def get(self, request, *args, **kwargs):
        data = {}
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data = self.get_context_data()
                    data['action'] = action
                    data['form'] = self.form
                    data['titulo_form'] = 'Nuevo Alumno'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.GET['pk'])
                    instancia = Persona.objects.get(id=pk)
                    data['nacimiento'] = instancia.nacimiento.strftime('%Y-%m-%d')
                    data['form'] = self.form(instance=instancia)
                    data['titulo_form'] = 'Editar alumno'
                    return render(request, self.template_name_add, data)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).order_by('-id')
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(Q(persona__nombres__icontains=search)|Q(persona__apellido1__icontains=search)
                                           |Q(persona__apellido2__icontains=search))
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nuevo Alumno'
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Lista de '+str(self.entidad)
        data['titulo_tabla'] = 'Lista de '+str(self.entidad)
        data['empresa'] = nombre_empresa()
        data['entidad'] = self.entidad
        return data

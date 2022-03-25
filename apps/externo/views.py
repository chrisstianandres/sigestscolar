from datetime import datetime

from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from apps.administrativo.models import Administrativo
from apps.backEnd import nombre_empresa, generar_usuario
from apps.externo.models import Externo
from apps.extras import PrimaryKeyEncryptor
from apps.perfil.models import PerfilUsuario
from apps.persona.models import Persona
from apps.externo.forms import Formulario
from apps.profesor.models import Profesor

from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Listview(TemplateView):
    model = Externo
    model_person = Persona
    second_model = PerfilUsuario
    template_name = 'externo/list.html'
    template_name_add = 'externo/form.html'
    icon = 'fa-fa-user'
    entidad = 'Externos'
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
                    form = self.form(request.POST)
                    if form.is_valid():
                        perfil = self.second_model()
                        perfil.persona = form.save()
                        perfil.externo = True
                        perfil.save()
                        externo = self.model()
                        externo.persona = perfil.persona
                        externo.save()
                    else:
                        data['error'] = form.errors
                elif action == 'edit':
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.POST['pk'])
                    objeto = self.model_person.objects.get(pk=pk)
                    form = self.form(request.POST, instance=objeto)
                    if form.is_valid():
                        form.save()
                    else:
                        data['error'] = form.errors
                elif action == 'delete':
                    objeto = self.model.objects.get(pk=request.POST['pk'])
                    objeto.delete()
                elif action == 'add_administrativo':
                    try:
                        persona = Persona.objects.get(pk=request.POST['id'])
                        if persona.es_administrativo():
                            data['error'] = 'Ya existe un perfil administrativo para esta persona'
                            return JsonResponse(data, safe=False)
                        administrativo = Administrativo(persona=persona, fechaingreso=datetime.now().date())
                        administrativo.save(request)
                        g = Group.objects.get(name='Administrativo')
                        if not persona.usuario:
                            generar_usuario(persona, g.id)
                        g.user_set.add(persona.usuario)
                        g.save()
                        perfil = PerfilUsuario(persona=persona, administrativo=administrativo)
                        perfil.save()
                    except Exception as ex:
                        transaction.set_rollback(True)
                        data['error'] = 'Error en la transaccion.'
                elif action == 'add_docente':
                    try:
                        persona = Persona.objects.get(pk=request.POST['id'])
                        if persona.es_profesor():
                            data['error'] = 'Ya existe un perfil docente para esta persona'
                            return JsonResponse(data, safe=False)
                        profesor = Profesor(persona=persona, fechaingreso=datetime.now().date())
                        profesor.save(request)
                        g = Group.objects.get(name='Profesor')
                        if not persona.usuario:
                            generar_usuario(persona, g.id)
                        g.user_set.add(persona.usuario)
                        g.save()
                        perfil = PerfilUsuario(persona=persona, profesor=profesor)
                        perfil.save()
                    except Exception as ex:
                        transaction.set_rollback(True)
                        data['error'] = 'Error en la transaccion.'
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
                    data['action'] = action
                    data['form'] = self.form
                    data['titulo_form'] = 'Nueva persona Externa'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.GET['pk'])
                    instancia = self.model_person.objects.get(id=pk)
                    data['nacimiento'] = instancia.nacimiento.strftime('%Y-%m-%d')
                    data['form'] = self.form(instance=instancia)
                    data['titulo_form'] = 'Editar persona externa'
                    return render(request, self.template_name_add, data)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).order_by('-id')
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(nombre__icontains=search)
                else:
                    return render(request, self.template_name, data)
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                # if data['modal_form']:
                #     data['form'] = self.form
                #     data['titulo_form'] = 'Nueva '+str(self.entidad)
                #     data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Lista de personas externas'
        data['titulo_tabla'] = 'Lista de personas externas'
        data['empresa'] = nombre_empresa()
        data['entidad'] = self.entidad
        return data

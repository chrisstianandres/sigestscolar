import json
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
from apps.curso.models import MateriaAsignada, Curso, CursoParalelo, CursoMateria
from apps.paralelo.models import Paralelo
from apps.profesor.forms import Formulario
from apps.extras import PrimaryKeyEncryptor
from apps.periodo.models import PeriodoLectivo
from apps.persona.models import Persona
from apps.profesor.models import Profesor
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Listview(TemplateView):
    model = MateriaAsignada
    template_name = 'docente/distributivolist.html'
    template_name_add = 'docente/distributivoform.html'
    icon = 'fas fa-people-arrows'
    entidad = 'Distributivo'
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
                    if calcular_edad(form.cleaned_data['nacimiento']) >= 18:
                        persona = form.save()
                        prof = Profesor(persona_id=persona.pk, fechaingreso=datetime.now(), activo=True)
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
                    if calcular_edad(form.cleaned_data['nacimiento']) >= 18:
                        form.save()
                    else:
                        data['error'] = 'Debe ser mayor de edad para ser docente'
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
                    data['titulo_form'] = 'Agregar distributivo docente'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.GET['pk'])
                    instancia = Persona.objects.get(id=pk)
                    data['nacimiento'] = instancia.nacimiento.strftime('%Y-%m-%d')
                    data['form'] = self.form(initial=model_to_dict(instancia))
                    data['titulo_form'] = 'Editar docente'
                    return render(request, self.template_name_add, data)
                if action == 'filter_periodo':
                    data = []
                    term = request.GET['term']
                    for objeto in PeriodoLectivo.objects.filter(Q(status=True), Q(nombre__icontains=term))[:10]:
                        item = {'id': objeto.pk, 'text': objeto.nombre}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'filter_curso':
                    data = []
                    filtros = Q(status=True)
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '':
                        ids = self.model.objects.values_list('curso_id').filter(Q(periodo_id=request.GET['id']))
                        filtros.add(Q(id__in=ids), Q.AND)
                    query = Curso.objects.filter(filtros, Q(nombre__icontains=term) | Q(descripcion__icontains=term))
                    for objeto in query[:10]:
                        item = {'id': objeto.pk, 'text': objeto.nombre}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'filter_paralelo':
                    data = []
                    filtros = Q(status=True)
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '':
                        filtros.add(Q(periodo_id=request.GET['id']), Q.AND)
                    if 'curso_id' in request.GET and not request.GET['curso_id'] == '':
                        filtros.add(Q(curso_id=request.GET['curso_id']), Q.AND)
                    ids = self.model.objects.values_list('paralelo_id').filter(filtros)
                    f = Q(status=True)
                    if 'id' in request.GET and not request.GET['id'] == '' or 'curso_id' in request.GET and not request.GET['curso_id'] == '':
                        f.add(Q(id__in=ids), Q.AND)
                    for objeto in Paralelo.objects.filter(f, Q(nombre__icontains=term) | Q(descripcion__icontains=term))[:10]:
                            item = {'id': objeto.pk, 'text': objeto.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_curso':
                    data = []
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '':
                        periodo = request.GET['id']
                        excludes = self.model.objects.values_list('materia__curso__curso_id').filter(status=True, materia__curso__periodo_id=periodo)
                        for objeto in Curso.objects.filter(Q(status=True), Q(nombre__icontains=term) | Q(
                                descripcion__icontains=term)).exclude(id__in=excludes)[:10]:
                            item = {'id': objeto.pk, 'text': objeto.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_paralelo':
                    data = []
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '':
                        periodo = request.GET['id']
                        curso = request.GET['curso']
                        if CursoParalelo.objects.filter(curso_id=curso, periodo_id=periodo, status=True).exists():
                            cur = CursoParalelo.objects.get(curso_id=curso, periodo_id=periodo, status=True)
                            for objeto in cur.paralelo.filter(Q(status=True), Q(nombre__icontains=term) | Q(
                                    descripcion__icontains=term))[:10]:
                                item = {'id': objeto.pk, 'text': objeto.nombre}
                                data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_materias':
                    data = []
                    term = request.GET['term']
                    periodo = request.GET['id']
                    curso = request.GET['curso']
                    ids = json.loads(request.GET['ids'])
                    for objeto in CursoMateria.objects.filter(Q(status=True), Q(curso__curso_id=curso), Q(curso__periodo_id=periodo), Q(materia__nombre__icontains=term) | Q(
                            materia__identificacion__icontains=term) | Q(materia__alias__icontains=term)).exclude(id__in=ids)[0:10]:
                        item = {'id': objeto.pk, 'text': str(objeto)}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'get_materia':
                    id = request.GET['id']
                    data = model_to_dict(CursoMateria.objects.get(id=id))
                    return JsonResponse(data, safe=False)
            else:
                data = self.get_context_data()
                filtros = Q(status=True)
                if 'per' in request.GET:
                    filtros = filtros & Q(materia__curso__periodo_id=request.GET['per'])
                elif PeriodoLectivo.objects.filter(status=True, actual=True):
                    periodoactual = PeriodoLectivo.objects.filter(status=True, actual=True).first()
                    data['periodo'] = periodoactual
                    filtros = filtros & Q(materia__curso__periodo_id=periodoactual.pk)
                if 'doc' in request.GET:
                    filtros = filtros & Q(profesor_id=request.GET['doc'])
                if 'cur' in request.GET:
                    filtros = filtros & Q(materia__curso__curso_id=request.GET['cur'])
                if 'mat' in request.GET:
                    filtros = filtros & Q(materia__materia_id=request.GET['mat'])
                objeto = self.model.objects.filter(filtros)
                list = objeto.distinct().values_list('profesor_id', flat=True)
                # list = Profesor.objects.filter(status=True, id__in=ids)
                if 'search' in request.GET:
                    if not request.GET['search'] == '':
                        data['search'] = search = request.GET['search']
                        list = list.filter(nombre__icontains=search)
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nuevo Distributivo'
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

import json

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView

from apps.backEnd import nombre_empresa
from apps.curso.forms import Formulario, FormularioApertura
from apps.curso.models import Curso, CursoParalelo, CursoMateria
from apps.extras import PrimaryKeyEncryptor
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from apps.profesor.models import MateriaAsignada
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Listview(TemplateView):
    model = Curso
    template_name = 'curso/list.html'
    template_name_add = 'curso/form.html'
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
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).order_by('-id')
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
                data['url_add'] = '#'
                data['modal_form'] = True
                if data['modal_form']:
                    data['form'] = self.form
                    data['titulo_form'] = 'Nuevo Curso'
                    data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = 'fa fa-user-lock'
        data['boton'] = 'Guardar'
        data['titulo'] = 'Lista de Cursos'
        data['titulo_tabla'] = 'Lista de Cursos'
        data['empresa'] = nombre_empresa()
        data['entidad'] = 'Cursos'
        return data


class ListviewAperutar(TemplateView):
    model = CursoParalelo
    seccond_model = CursoMateria
    template_name = 'curso/list_apertura.html'
    template_name_add = 'curso/form.html'
    icon = 'far fa-calendar-alt'
    entidad = 'Cursos Aperturados'
    form = FormularioApertura

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                with transaction.atomic():
                    info = json.loads(request.POST['apertura'])
                    form = self.form(info)
                    if form.is_valid():
                        curso = form.save()
                        for materia in info['materias']:
                            CursoMateria(curso=curso, materia_id=materia['id']).save()
                    else:
                        data['error'] = form.errors
            elif action == 'edit':
                with transaction.atomic():
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.POST['pk'])
                    info = json.loads(request.POST['apertura'])
                    objeto = self.model.objects.get(pk=pk)
                    form = self.form(info, instance=objeto)
                    if form.is_valid():
                        form.save()
                        for m in objeto.cursomateria_set.all().exclude(id__in=[id for id in MateriaAsignada.objects.filter(materia_id__in=objeto.cursomateria_set.all().values_list('materia_id'))]):
                            m.delete()
                        for materia in info['materias']:
                            CursoMateria(curso=objeto, materia_id=materia['id']).save()
                    else:
                        data['error'] = form.errors
            elif action == 'delete':
                objeto = self.model.objects.get(pk=request.POST['pk'])
                objeto.cursomateria_set.all().delete()
                objeto.delete()
            elif action == 'detalle':
                data = []
                num = 0
                objeto = self.model.objects.get(pk=request.POST['pk'])
                for materia in objeto.cursomateria_set.all():
                    item = {'nombre': materia.materia.nombre, 'alias': materia.materia.alias,
                            'identificacion': materia.materia.identificacion,
                            'id': num + 1}
                    data.append(item)
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
                    data['titulo_form'] = 'Aperturar nuevo curso'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = request.GET['pk']
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.GET['pk'])
                    instancia = self.model.objects.get(id=pk)
                    data['form'] = self.form(instance=instancia)
                    if instancia.total_materias() > 0:
                        materias = []
                        for m in instancia.cursomateria_set.all():
                            materias.append({'identificacion': m.materia.identificacion, 'nombre': m.materia.nombre, 'alias': m.materia.alias, 'id': m.materia.id})
                        data['materias'] = materias
                    data['titulo_form'] = 'Editar curso aperturado'
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
                        excludes = self.model.objects.values_list('curso_id').filter(status=True, periodo_id=periodo)
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
                        for objeto in Paralelo.objects.filter(Q(status=True), Q(nombre__icontains=term) | Q(
                                descripcion__icontains=term))[:10]:
                            item = {'id': objeto.pk, 'text': objeto.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_materias':
                    data = []
                    term = request.GET['term']
                    ids = json.loads(request.GET['ids'])
                    for objeto in Materia.objects.filter(Q(status=True), Q(nombre__icontains=term) | Q(
                            identificacion__icontains=term) | Q(alias__icontains=term)).exclude(id__in=ids)[:10]:
                        item = {'id': objeto.pk, 'text': str(objeto)}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'get_materia':
                    id = request.GET['id']
                    data = model_to_dict(Materia.objects.get(id=id))
                    return JsonResponse(data, safe=False)
            else:
                data = self.get_context_data()
                list = self.model.objects.filter(status=True).order_by('-id')
                filtros = Q(status=True)
                if 'periodo' in request.GET and not request.GET['periodo'] == '':
                    filtros.add(Q(periodo_id=request.GET['periodo']), Q.AND)
                    data['periodo'] = PeriodoLectivo.objects.get(id=request.GET['periodo'])
                if 'curso' in request.GET and not request.GET['curso'] == '':
                    filtros.add(Q(curso_id=request.GET['curso']), Q.AND)
                    data['curso'] = Curso.objects.get(id=request.GET['curso'])
                if 'paralelo' in request.GET and not request.GET['paralelo'] == '':
                    filtros.add(Q(paralelo_id=request.GET['paralelo']), Q.AND)
                    data['paralelo'] = Paralelo.objects.get(id=request.GET['paralelo'])
                if 'search' in request.GET and not request.GET['search'] == '':
                    filtros.add((Q(curso__nombre__icontains=request.GET['search']) | Q(paralelo__nombre__icontains=request.GET['search'])), Q.AND)
                    # filtros.add(, Q.OR)
                    data['search'] = search = request.GET['search']
                list = list.filter(filtros)
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nueva ' + str(self.entidad)
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Lista de cursos aperturados'
        data['titulo_tabla'] = 'Lista de cursos aperturados'
        data['empresa'] = nombre_empresa()
        data['entidad'] = self.entidad
        return data

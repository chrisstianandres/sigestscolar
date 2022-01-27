import json
import os

from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView
from xhtml2pdf import pisa

from apps.backEnd import nombre_empresa
from apps.curso.forms import Formulario, FormularioApertura, FormularioConfiguracionValores, FormularioNotas
from apps.curso.models import Curso, CursoParalelo, CursoMateria, ConfiguracionValoresCurso, \
    ConfiguracionValoresGeneral, MateriaAsignada, Quimestre, ModeloParcial, CursoQuimestre, NotasAlumno
from apps.extras import PrimaryKeyEncryptor
from apps.inscripcion.models import Inscripcion
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from sigestscolar import settings
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
                            materia = CursoMateria(curso=curso, materia_id=materia['id'])
                            materia.save()
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
                        for m in objeto.cursomateria_set.all().exclude(
                                id__in=objeto.cursomateria_set.all().values_list('materia_id', flat=True)):
                            m.delete()
                        for materia in info['materias']:
                            curso = CursoMateria(curso=objeto, materia_id=materia['id'])
                            curso.save()
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
            elif action == 'configuraciongeneral':
                if ConfiguracionValoresGeneral.objects.exists():
                    confi = ConfiguracionValoresGeneral.objects.first()
                    configuracion = FormularioConfiguracionValores(request.POST, instance=confi)
                else:
                    configuracion = FormularioConfiguracionValores(request.POST)
                if configuracion.is_valid():
                    configuracion.save(request)
            elif action == 'configurarcomogeneral':
                if ConfiguracionValoresGeneral.objects.filter(status=True).exists():
                    configuraciongeneral = ConfiguracionValoresGeneral.objects.first()
                    configuracionindividual = ConfiguracionValoresCurso(curso_id=request.POST['pk'],
                                                                        matricula=configuraciongeneral.matricula,
                                                                        pension=configuraciongeneral.pension,
                                                                        numeropensiones=configuraciongeneral.numeropensiones)
                    configuracionindividual.save(request)
                    data['resp'] = True
                else:
                    data['resp'] = False
                    data['mensaje'] = 'No existe la confguracion General'
                return JsonResponse(data, safe=False)
            elif action == 'configurarindividual':
                configuracion = FormularioConfiguracionValores(request.POST)
                if configuracion.is_valid():
                    configuracionindividual = ConfiguracionValoresCurso(curso_id=request.POST['pk'],
                                                                        matricula=configuracion.cleaned_data[
                                                                            'matricula'],
                                                                        pension=configuracion.cleaned_data['pension'],
                                                                        numeropensiones=configuracion.cleaned_data[
                                                                            'numeropensiones'])
                    configuracionindividual.save(request)
                    data['resp'] = True
                else:
                    data['resp'] = False
                    data['mensaje'] = 'No existe la confguracion General'
                return JsonResponse(data, safe=False)
            elif action == 'configuraparciales':
                with transaction.atomic():
                    try:
                        curso = self.model.objects.get(id=request.POST['id'])
                        if curso.quimestres >= 2 and curso.parciales >= 3:
                            for q in Quimestre.objects.filter(status=True, numero__lte=curso.quimestres).order_by(
                                    'numero'):
                                for p in ModeloParcial.objects.filter(status=True, quimestre=q,
                                                                      numero__lte=curso.parciales + 1):
                                    for m in CursoMateria.objects.filter(status=True, curso=curso):
                                        if not MateriaAsignada.objects.filter(materia=m).exists():
                                            data[
                                                'error'] = 'Este curso aun no tiene todos los docentes asigandos para configurar el modelo de calificacion'
                                            transaction.set_rollback(True)
                                            return JsonResponse(data, safe=False)
                                        for m in MateriaAsignada.objects.filter(materia=m):
                                            configuracionnota = CursoQuimestre(cursoasignado=m, parcial=p)
                                            configuracionnota.save(request)
                        else:
                            data['error'] = 'Numero de Quimestres y/o Parciales Incorrecto'
                    except Exception as e:
                        data['error'] = 'Error en la transaccion: ' + str(e)
                        transaction.set_rollback(True)
                return JsonResponse(data, safe=False)

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
                            materias.append({'identificacion': m.materia.identificacion, 'nombre': m.materia.nombre,
                                             'alias': m.materia.alias, 'id': m.materia.id})
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
                    if 'id' in request.GET and not request.GET['id'] == '' or 'curso_id' in request.GET and not \
                    request.GET['curso_id'] == '':
                        f.add(Q(id__in=ids), Q.AND)
                    for objeto in Paralelo.objects.filter(f,
                                                          Q(nombre__icontains=term) | Q(descripcion__icontains=term))[
                                  :10]:
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
                if 'search' in request.GET and not request.GET['search'] == '':
                    filtros.add((Q(curso__nombre__icontains=request.GET['search']) | Q(
                        paralelo__nombre__icontains=request.GET['search'])), Q.AND)
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
                data['formvaloresindividual'] = FormularioConfiguracionValores()
                if ConfiguracionValoresGeneral.objects.exists():
                    valores = ConfiguracionValoresGeneral.objects.first()
                    data['formvalores'] = FormularioConfiguracionValores(instance=valores)
                else:
                    data['formvalores'] = FormularioConfiguracionValores()
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


class IngresoNotasView(TemplateView):
    model = MateriaAsignada
    seccond_model = CursoMateria
    template_name = 'curso/list_notas.html'
    template_name_add = 'curso/formnotas.html'
    icon = 'fas fa-file-signature'
    entidad = 'Notas'
    form = FormularioNotas

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            with transaction.atomic():
                action = request.POST['action']
                if action == 'add':
                    try:
                        info = json.loads(request.POST['notas'])
                        if 'curso' in info and not info['curso'] == '':
                            for alm in info['alumnos']:
                                if not NotasAlumno.objects.filter(curso_id=int(info['curso']), alumno_id=alm['id'],
                                                                  nota=round(float(alm['nota']))).exists():
                                    notas = NotasAlumno(curso_id=int(info['curso']), alumno_id=alm['id'],
                                                        nota=round(float(alm['nota']), 2))
                                    notas.save(request)
                                    data['id'] = notas.curso.pk
                                    return JsonResponse(data, safe=False)
                                else:
                                    data['error'] = 'Ya existe notas para este alumno'
                        else:
                            data['error'] = 'Debe ingresar una materia, quimestre y parcial valido'
                    except Exception as e:
                        data['error'] = 'Error en la transaccion:' + str(e)
                        transaction.set_rollback(True)
                elif action == 'edit':
                    try:
                        info = json.loads(request.POST['notas'])
                        if 'curso' in info and not info['curso'] == '':
                            for alm in info['alumnos']:
                                notas = NotasAlumno.objects.get(curso_id=int(info['curso']), alumno_id=alm['id'])
                                notas.nota = round(float(alm['nota']), 3)
                                notas.save(request)
                                data['id'] = notas.curso.pk
                                return JsonResponse(data, safe=False)
                            else:
                                data['error'] = 'Ya existe notas para este alumno'
                        else:
                            data['error'] = 'Debe ingresar una materia, quimestre y parcial valido'
                    except Exception as e:
                        data['error'] = 'Error en la transaccion:' + str(e)
                        transaction.set_rollback(True)
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
                elif action == 'configuraciongeneral':
                    if ConfiguracionValoresGeneral.objects.exists():
                        confi = ConfiguracionValoresGeneral.objects.first()
                        configuracion = FormularioConfiguracionValores(request.POST, instance=confi)
                    else:
                        configuracion = FormularioConfiguracionValores(request.POST)
                    if configuracion.is_valid():
                        configuracion.save(request)
                elif action == 'configurarcomogeneral':
                    if ConfiguracionValoresGeneral.objects.filter(status=True).exists():
                        configuraciongeneral = ConfiguracionValoresGeneral.objects.first()
                        configuracionindividual = ConfiguracionValoresCurso(curso_id=request.POST['pk'],
                                                                            matricula=configuraciongeneral.matricula,
                                                                            pension=configuraciongeneral.pension,
                                                                            numeropensiones=configuraciongeneral.numeropensiones)
                        configuracionindividual.save(request)
                        data['resp'] = True
                    else:
                        data['resp'] = False
                        data['mensaje'] = 'No existe la confguracion General'
                    return JsonResponse(data, safe=False)
                elif action == 'configurarindividual':
                    configuracion = FormularioConfiguracionValores(request.POST)
                    if configuracion.is_valid():
                        configuracionindividual = ConfiguracionValoresCurso(curso_id=request.POST['pk'],
                                                                            matricula=configuracion.cleaned_data[
                                                                                'matricula'],
                                                                            pension=configuracion.cleaned_data['pension'],
                                                                            numeropensiones=configuracion.cleaned_data[
                                                                                'numeropensiones'])
                        configuracionindividual.save(request)
                        data['resp'] = True
                    else:
                        data['resp'] = False
                        data['mensaje'] = 'No existe la confguracion General'
                    return JsonResponse(data, safe=False)
                elif action == 'configuraparciales':
                    try:
                        curso = self.model.objects.get(id=request.POST['id'])
                        if curso.quimestres >= 2 and curso.parciales >= 3:
                            for q in Quimestre.objects.filter(status=True, numero__lte=curso.quimestres).order_by(
                                    'numero'):
                                for p in ModeloParcial.objects.filter(status=True, quimestre=q,
                                                                      numero__lte=curso.parciales + 1):
                                    for m in CursoMateria.objects.filter(status=True, curso=curso):
                                        if not MateriaAsignada.objects.filter(materia=m).exists():
                                            data[
                                                'error'] = 'Este curso aun no tiene todos los docentes asigandos para configurar el modelo de calificacion'
                                            transaction.set_rollback(True)
                                            return JsonResponse(data, safe=False)
                                        for m in MateriaAsignada.objects.filter(materia=m):
                                            configuracionnota = CursoQuimestre(cursoasignado=m, parcial=p)
                                            configuracionnota.save(request)
                        else:
                            data['error'] = 'Numero de Quimestres y/o Parciales Incorrecto'
                    except Exception as e:
                        data['error'] = 'Error en la transaccion: ' + str(e)
                        transaction.set_rollback(True)
                    return JsonResponse(data, safe=False)
                elif action == 'cerraracta':
                    try:
                        id = request.POST['acta']
                        nota = CursoQuimestre.objects.get(id=id)
                        nota.actacerrada = True
                        nota.save(request)
                    except Exception as e:
                        data['error'] = 'Error al cerrar el acta' + str(e)
                        transaction.set_rollback(True)
                else:
                    data['error'] = 'No ha seleccionado una opcion'
                    transaction.set_rollback(True)
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
                    data['periodolec'] = PeriodoLectivo.objects.get(id=request.GET['periodo'])
                    data['cursoper'] = Curso.objects.get(id=request.GET['id'])
                    data['action'] = action
                    data['form'] = self.form()
                    data['titulo_form'] = 'Nuevo Ingreso de Notas'
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = pk = request.GET['pk']
                    instancia = CursoQuimestre.objects.get(id=pk)
                    info = {'periodo': instancia.cursoasignado.materia.curso.periodo,
                            'curso': instancia.cursoasignado.materia.curso.curso,
                            'paralelo': instancia.cursoasignado.paralelo,
                            'materia': instancia.cursoasignado.materia.materia,
                            'quimestre': instancia.parcial.quimestre}
                    data['form'] = form = self.form()
                    form.edit(info)
                    data['parcial'] = {'pk': instancia.pk, 'nombre': instancia.parcial.nombre}
                    alumnos = []
                    for a in instancia.notasalumno_set.filter(status=True):
                        alumnos.append({'id': a.alumno.pk, 'nombre': a.alumno.alumno.persona.nombre_completo(),
                                        'identificacion': a.alumno.alumno.persona.identificacion(), 'nota': round(float(a.nota), 3)})
                    data['alumnos'] = alumnos
                    data['titulo_form'] = 'Editar Notas'
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
                    if 'id' in request.GET and not request.GET['id'] == '' or 'curso_id' in request.GET and not \
                    request.GET['curso_id'] == '':
                        f.add(Q(id__in=ids), Q.AND)
                    for objeto in Paralelo.objects.filter(f,
                                                          Q(nombre__icontains=term) | Q(descripcion__icontains=term))[
                                  :10]:
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
                    curso = ''
                    periodo = ''
                    persona = request.session['persona']
                    term = request.GET['term']
                    if 'periodo' in request.GET and not request.GET['periodo'] == '':
                        periodo = request.GET['periodo']
                    else:
                        return JsonResponse(data, safe=False)
                    if 'curso' in request.GET and not request.GET['curso'] == '':
                        curso = request.GET['curso']
                    else:
                        return JsonResponse(data, safe=False)
                    for objeto in MateriaAsignada.objects.filter(Q(status=True), Q(profesor__persona=persona),
                                                                 Q(materia__curso__curso_id=int(curso)),
                                                                 Q(materia__curso__periodo_id=periodo),
                                                                 Q(paralelo__nombre__icontains=term) |
                                                                 Q(paralelo__descripcion__icontains=term)).distinct(
                        'paralelo')[0:10]:
                        item = {'id': objeto.paralelo.pk, 'text': objeto.paralelo.nombre}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_materias':
                    data = []
                    curso = ''
                    periodo = ''
                    paralelo = ''
                    persona = request.session['persona']
                    term = request.GET['term']
                    if 'periodo' in request.GET and not request.GET['periodo'] == '':
                        periodo = request.GET['periodo']
                    else:
                        return JsonResponse(data, safe=False)
                    if 'curso' in request.GET and not request.GET['curso'] == '':
                        curso = request.GET['curso']
                    else:
                        return JsonResponse(data, safe=False)
                    if 'paralelo' in request.GET and not request.GET['paralelo'] == '':
                        paralelo = request.GET['paralelo']
                    else:
                        return JsonResponse(data, safe=False)

                    for objeto in MateriaAsignada.objects.filter(Q(status=True), Q(profesor__persona=persona),
                                                                 Q(materia__curso__curso_id=int(curso)),
                                                                 Q(materia__curso__periodo_id=periodo),
                                                                 Q(paralelo_id=paralelo),
                                                                 Q(materia__materia__nombre__icontains=term) |
                                                                 Q(materia__materia__alias__icontains=term)).distinct(
                        'materia__materia_id')[0:10]:
                        item = {'id': objeto.pk, 'text': objeto.materia.materia.nombre}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_quimestre':
                    materia = ''
                    persona = request.session['persona']
                    term = request.GET['term']
                    if 'materia' in request.GET and not request.GET['materia'] == '':
                        materia = request.GET['materia']
                    else:
                        return JsonResponse(data, safe=False)
                    data = []
                    materiaasignada = MateriaAsignada.objects.get(id=materia, profesor__persona=persona)
                    # for objeto in CursoQuimestre.objects.filter(Q(status=True), cursoasignado_id=materia).distinct('parcial__quimestre'):
                    for objeto in materiaasignada.modelo_eval_quimestres():
                        if not objeto.tiene_notas():
                            item = {'id': objeto.parcial.quimestre.pk, 'text': objeto.parcial.quimestre.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_parcial':
                    quimestre = ''
                    persona = request.session['persona']
                    if 'quimestre' in request.GET and not request.GET['quimestre'] == '':
                        quimestre = request.GET['quimestre']
                    else:
                        return JsonResponse(data, safe=False)
                    if 'materia' in request.GET and not request.GET['materia'] == '':
                        materia = request.GET['materia']
                    else:
                        return JsonResponse(data, safe=False)
                    data = []
                    for objeto in CursoQuimestre.objects.filter(Q(status=True), parcial__quimestre_id=quimestre,
                                                                cursoasignado_id=materia,
                                                                cursoasignado__profesor__persona=persona).distinct(
                        'parcial'):
                        if not NotasAlumno.objects.filter(curso=objeto).exists():
                            item = {'id': objeto.pk, 'text': objeto.parcial.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'get_alumnos':
                    id = request.GET['id']
                    paralelo = request.GET['paralelo']
                    mat = MateriaAsignada.objects.get(id=id)
                    alumnos = Inscripcion.objects.filter(status=True, curso=mat.materia.curso, paralelo_id=paralelo)
                    data = self.lista_alumnos(alumnos)
                    return JsonResponse(data, safe=False)
                if action == 'vernotas':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = pk = request.GET['pk']
                    instancia = CursoQuimestre.objects.get(id=pk)
                    info = {'periodo': instancia.cursoasignado.materia.curso.periodo,
                            'curso': instancia.cursoasignado.materia.curso.curso,
                            'paralelo': instancia.cursoasignado.paralelo,
                            'materia': instancia.cursoasignado.materia.materia,
                            'quimestre': instancia.parcial.quimestre}
                    data['form'] = form = self.form()
                    form.edit(info)
                    data['parcial'] = {'pk': instancia.pk, 'nombre': instancia.parcial.nombre}
                    alumnos = []
                    for a in instancia.notasalumno_set.filter(status=True):
                        alumnos.append({'id': a.alumno.pk, 'nombre': a.alumno.alumno.persona.nombre_completo(),
                                        'identificacion': a.alumno.alumno.persona.identificacion(), 'nota': round(float(a.nota), 3)})
                    data['alumnos'] = alumnos
                    data['titulo_form'] = 'Notas Ingresadas'
                    data['titulo'] = 'Notas Ingresadas'
                    data['pantallaver'] = True
                    return render(request, self.template_name_add, data)
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['pk'] = pk = request.GET['pk']
                    instancia = CursoQuimestre.objects.get(id=pk)
                    data['parcial'] = {'pk': instancia.pk, 'nombre': instancia.parcial.nombre}
                    alumnos = []
                    for a in instancia.notasalumno_set.filter(status=True):
                        alumnos.append({'id': a.alumno.pk, 'nombre': a.alumno.alumno.persona.nombre_completo(),
                                        'identificacion': a.alumno.alumno.persona.identificacion(), 'nota': round(float(a.nota), 3)})
                    data['alumnos'] = alumnos
                    data['titulo_form'] = 'Editar Notas'
                    return render(request, self.template_name_add, data)
            else:
                data = self.get_context_data()
                persona = request.session['persona']
                list = self.model.objects.filter(status=True, profesor__persona=persona)
                filtros = Q(status=True)
                if 'periodo' in request.GET and not request.GET['periodo'] == '':
                    filtros.add(Q(materia__curso__periodo_id=request.GET['periodo']), Q.AND)
                    data['periodo'] = PeriodoLectivo.objects.get(id=request.GET['periodo'])
                else:
                    data['periodo'] = periodo = request.session['periodoactual']
                    filtros.add(Q(materia__curso__periodo=periodo), Q.AND)
                list = list.filter(filtros).order_by('materia__curso__curso_id').distinct('materia__curso__curso')
                page_number = request.GET.get('page', 1)
                paginator = Paginator(list, 10)
                page_range = paginator.get_elided_page_range(number=page_number)
                page_obj = paginator.get_page(page_number)
                data['page_obj'] = page_obj
                data['page_range'] = page_range
                data['url_add'] = '"' + self.request.path + '?action=add' + '"'
                data['modal_form'] = False
                data['form'] = self.form
                data['titulo_form'] = 'Nuevo ' + str(self.entidad)
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def lista_alumnos(self, alumnos):
        try:
            data = []
            for alumno in alumnos:
                data.append({'id': alumno.pk, 'nombre': alumno.alumno.persona.nombre_completo(),
                             'identificacion': alumno.alumno.persona.identificacion(), 'nota': 1})
            return data
        except Exception as e:
            print(e)
            pass

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Ingreso de Notas'
        data['titulo_tabla'] = 'Lista de cursos Asignados'
        data['empresa'] = nombre_empresa()
        data['entidad'] = self.entidad
        return data


class PrintActaNotas(View):

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
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'actaindividual':
                    instancia = CursoQuimestre.objects.get(pk=self.kwargs['pk'])
                    template = get_template('bases/actanotas.html')
                    context = {'title': 'Acta de Notas',
                               'modeloeval': instancia,
                               'icon': 'media/logo.png',
                               'empresa': nombre_empresa()}
                    html = template.render(context)
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="Acta_notas_'+str(instancia.cursoasignado.materia.curso.curso.nombre)+'.pdf"'
                    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=self.link_callback)
                    return response
                elif action == 'actageneral':
                    instancia = MateriaAsignada.objects.get(pk=self.kwargs['pk'])
                    alumnos = Inscripcion.objects.filter(status=True, curso=instancia.materia.curso, paralelo=instancia.paralelo)
                    template = get_template('bases/actageneral.html')
                    context = {'title': 'Acta de Notas',
                               'modeloeval': instancia,
                               'icon': 'media/logo.png',
                               'alumnos': alumnos,
                               'empresa': nombre_empresa()}
                    html = template.render(context)
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="Acta_general_notas_'+str(instancia.materia.curso.curso.nombre)+'.pdf"'
                    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=self.link_callback)
                    return response
        except Exception as e:
            print(e)
            pass
        return HttpResponseRedirect(reverse_lazy('notas'))

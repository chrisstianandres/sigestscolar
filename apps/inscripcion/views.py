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

from apps.alumno.models import Alumno
from apps.backEnd import nombre_empresa
from apps.inscripcion.forms import Formulario
from apps.curso.models import Curso, CursoMateria, CursoParalelo
from apps.extras import PrimaryKeyEncryptor
from apps.inscripcion.models import Inscripcion
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from apps.profesor.models import MateriaAsignada
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Listview(TemplateView):
    model = Inscripcion
    seccond_model = CursoMateria
    template_name = 'inscripcion/list.html'
    template_name_add = 'inscripcion/form.html'
    icon = 'far fa-calendar-alt'
    entidad = 'Inscripciones'
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
                    print(request.POST)
                    alumno_id = request.POST['persona']
                    representante_id = request.POST['representante']
                    paralelo_id = request.POST['paralelo']
                    if not Alumno.objects.filter(persona_id=alumno_id).exists():
                        alumno = Alumno(persona_id=alumno_id, representante_id=representante_id, fechaingreso=datetime.now().date())
                    else:
                        alumno = Alumno.objects.get(persona_id=alumno_id)
                        if not alumno.representante_id == representante_id:
                            alumno.representante_id = representante_id
                    alumno.save()
                    info = {'alumno': alumno, 'curso': paralelo_id, 'fecha': datetime.now().date()}
                    form = self.form(info)
                    if form.is_valid():
                        form.save()
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
                    data['titulo_form'] = 'Inscribir alumno en un curso'
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
                if action == 'search_periodo':
                    data = []
                    term = request.GET['term']
                    for objeto in PeriodoLectivo.objects.filter(Q(status=True), Q(nombre__icontains=term))[:10]:
                        item = {'id': objeto.pk, 'text': objeto.nombre}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_curso':
                    data = []
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '':
                        periodo = request.GET['id']
                        for objeto in CursoParalelo.objects.filter(Q(status=True), Q(curso__nombre__icontains=term), Q(periodo_id=int(periodo)))[:10]:
                            item = {'id': objeto.curso.pk, 'text': objeto.curso.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_paralelo':
                    data = []
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '' and 'idcurso' in request.GET and not request.GET['idcurso'] == '':
                        periodo = request.GET['id']
                        curso = request.GET['idcurso']
                        for objeto in CursoParalelo.objects.filter(status=True, curso_id=curso, periodo_id=periodo, paralelo__nombre__icontains=term)[:10]:
                            item = {'id': objeto.pk, 'text': objeto.paralelo.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_alumno':
                    data = []
                    term = request.GET['term']
                    from apps.persona.models import Persona
                    anio = datetime.now().year - 18
                    for objeto in Persona.objects.filter(Q(status=True), Q(nacimiento__year__gte=anio), Q(nombres__icontains=term) | Q(cedula__icontains=term) | Q(apellido1__icontains=term) | Q(apellido2__icontains=term) )[:10]:
                        item = {'id': objeto.pk, 'text': str(objeto)}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'check_alumno':
                    id = request.GET['id']
                    data = []
                    if Alumno.objects.filter(persona_id=id).exists():
                        alumno = Alumno.objects.get(persona_id=id)
                        if alumno.representante:
                            item = {'id': alumno.representante.pk, 'text': alumno.representante.nombre, 'resp': True}
                            data.append(item)
                    else:
                        item = {'resp': False}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_representante':
                    data = []
                    term = request.GET['term']
                    from apps.persona.models import Persona
                    anio_mayor = datetime.now().year - 18
                    anio_menor = datetime.now().year - 90
                    for objeto in Persona.objects.filter(Q(status=True), Q(nacimiento__year__range=[anio_menor, anio_mayor]), Q(nombres__icontains=term) | Q(cedula__icontains=term) | Q(apellido1__icontains=term) | Q(apellido2__icontains=term))[:10]:
                        item = {'id': objeto.pk, 'text': str(objeto)}
                        data.append(item)
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
                    filtros.add((Q(alumno__persona__nombre__icontains=request.GET['search']) | Q(alumno__persona__apellido1__icontains=request.GET['search']) | Q(alumno__persona__apellido2__icontains=request.GET['search'])), Q.AND)
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
                data['titulo_form'] = 'Nueva Inscripcion'
                data['action_form'] = 'add'
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Lista de Alumnos inscritos'
        data['titulo_tabla'] = 'Lista de Alumnos inscritos'
        data['empresa'] = nombre_empresa()
        data['entidad'] = self.entidad
        return data

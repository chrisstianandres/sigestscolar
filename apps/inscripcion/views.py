import json
from datetime import datetime, timedelta

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
from apps.matricula.models import Matricula, Pension
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from apps.rubro.models import Rubro
from sigestscolar.settings import SECRET_KEY_ENCRIPT
# from dateutil.relativedelta import relativedelta

MESES_EN_LETRAS = ('ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE')

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
                    alumno_id = request.POST['persona']
                    representante_id = request.POST['representante']
                    paralelo_id = request.POST['paralelo']
                    curso_id = request.POST['curso']
                    cursoparalelo = CursoParalelo.objects.get(id=curso_id)
                    cupo = False
                    if cursoparalelo.cupoindividual:
                        if cursoparalelo.cupo_disponible_por_paralelo(paralelo_id):
                            cupo = True
                    else:
                        if cursoparalelo.cupos_disponible():
                            cupo = True
                    if cupo:
                        if not Alumno.objects.filter(persona_id=alumno_id).exists():
                            alumno = Alumno(persona_id=alumno_id, representante_id=representante_id, fechaingreso=datetime.now().date())
                        else:
                            alumno = Alumno.objects.get(persona_id=alumno_id)
                            if not alumno.representante_id == int(representante_id):
                                alumno.representante_id = representante_id
                        alumno.save()
                        info = {'alumno': alumno, 'curso': curso_id, 'paralelo': paralelo_id, 'fecha': datetime.now().date()}
                        form = self.form(info)
                        if form.is_valid():
                            inscripcion = form.save()
                            mat = crear_matricula(inscripcion)
                            if not mat:
                                transaction.set_rollback(True)
                                data['error'] = 'Error al inscribir al alumno'
                        else:
                            data['error'] = form.errors
                    else:
                        data['error'] = 'Cupo no diponible'
            elif action == 'edit':
                with transaction.atomic():
                    instancia = self.model.objects.get(id=request.POST['pk'])
                    alumno_id = request.POST['persona']
                    representante_id = request.POST['representante']
                    paralelo_id = request.POST['paralelo']
                    curso_id = request.POST['curso']
                    alumno = Alumno.objects.get(persona_id=alumno_id)
                    cursoparalelo = CursoParalelo.objects.get(id=curso_id)
                    cupo = False
                    if cursoparalelo.cupoindividual:
                        if cursoparalelo.cupo_disponible_por_paralelo(paralelo_id):
                            cupo = True
                    else:
                        if cursoparalelo.cupos_disponible():
                            cupo = True
                    if cupo:
                        if not alumno.representante_id == int(representante_id):
                            alumno.representante_id = representante_id
                            alumno.save()
                        info = {'alumno': alumno.id, 'curso': curso_id, 'paralelo':paralelo_id, 'fecha': datetime.now().date()}
                        form = self.form(info, instance=instancia)
                        if form.is_valid():
                            form.save()
                        else:
                            data['error'] = form.errors
                    else:
                        data['error'] = 'Cupo no diponible'
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
                    pk = PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).decrypt(request.GET['pk'])
                    instancia = self.model.objects.get(id=pk)
                    data['instancia'] = instancia
                    data['titulo_form'] = 'Editar inscripcion'
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
                        ids = self.model.objects.values_list('curso__curso_id').filter(Q(curso__periodo_id=request.GET['id']))
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
                        filtros.add(Q(curso__periodo_id=request.GET['id']), Q.AND)
                    if 'curso_id' in request.GET and not request.GET['curso_id'] == '':
                        filtros.add(Q(curso__curso_id=request.GET['curso_id']), Q.AND)
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
                            item = {'id': objeto.pk, 'text': objeto.curso.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_paralelo':
                    data = []
                    term = request.GET['term']
                    if 'id' in request.GET and not request.GET['id'] == '' and 'idcurso' in request.GET and not request.GET['idcurso'] == '':
                        periodo = request.GET['id']
                        curso = request.GET['idcurso']
                        query = CursoParalelo.objects.filter(status=True, id=curso, periodo_id=periodo).first()
                        for objeto in query.paralelo.filter(nombre__icontains=term)[:10]:
                            item = {'id': objeto.pk, 'text': objeto.nombre}
                            data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'search_alumno':
                    data = []
                    term = request.GET['term']
                    from apps.persona.models import Persona
                    anio = datetime.now().year - 18
                    for objeto in Persona.objects.filter(Q(status=True), Q(nacimiento__year__gte=anio), Q(nombres__icontains=term) | Q(cedula__icontains=term) | Q(apellido1__icontains=term) | Q(apellido2__icontains=term) ).exclude(usuario__isnull=False)[:10]:
                        item = {'id': objeto.pk, 'text': str(objeto)}
                        data.append(item)
                    return JsonResponse(data, safe=False)
                if action == 'check_inscripcion':
                    if 'alumno' in request.GET and not request.GET['alumno'] == '':
                        data['resp'] = Inscripcion.objects.filter(curso__periodo_id=int(request.GET['id']),
                                                                  alumno__persona_id=int(request.GET['alumno'])).exists()
                    else:
                        data = {'resp': False, 'mensaje': 'Debe seleccionar un alumno!'}
                    return JsonResponse(data, safe=False)
                if action == 'check_alumno':
                    id = request.GET['id']
                    # data = []
                    if Alumno.objects.filter(persona_id=id).exists():
                        alumno = Alumno.objects.get(persona_id=id)
                        if alumno.representante:
                            data = {'id': alumno.representante.pk, 'text': alumno.representante.nombre_completo(), 'resp': True}
                            # data.append(item)
                    else:
                        data = {'resp': False}
                        # data.append(item)
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
                    filtros.add(Q(curso__periodo_id=request.GET['periodo']), Q.AND)
                    data['periodo'] = PeriodoLectivo.objects.get(id=request.GET['periodo'])
                if 'curso' in request.GET and not request.GET['curso'] == '':
                    filtros.add(Q(curso__curso_id=request.GET['curso']), Q.AND)
                    data['curso'] = Curso.objects.get(id=request.GET['curso'])
                if 'paralelo' in request.GET and not request.GET['paralelo'] == '':
                    filtros.add(Q(paralelo_id=request.GET['paralelo']), Q.AND)
                    data['paralelo'] = Paralelo.objects.get(id=request.GET['paralelo'])
                if 'search' in request.GET and not request.GET['search'] == '':
                    filtros.add((Q(alumno__persona__nombres__icontains=request.GET['search']) | Q(alumno__persona__apellido1__icontains=request.GET['search']) | Q(alumno__persona__apellido2__icontains=request.GET['search'])), Q.AND)
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


def crear_matricula(inscripcion):
    try:
        valores = inscripcion.curso.configuracion_valores()
        # fecha maxima de pago 15 dias despues de la inscripcion
        fechamaxima = datetime.now() + timedelta(days=15)
        matricula = Matricula(inscripcion=inscripcion, observaciones='Ninguna', fecha=datetime.now(), fechatope=fechamaxima)
        matricula.save()
        observ = 'MATRICULA DE {} EN EL CURSO {} EN EL PERIODO {}'.format(matricula.inscripcion.alumno.persona, matricula.inscripcion.curso,  matricula.inscripcion.curso.periodo)
        datos = [{'fechavence': fechamaxima, 'valor': valores.matricula, 'iva': 12, 'observacion': observ}]
        rubrocreado = crear_rubro(persona=matricula.inscripcion.alumno.persona, matricula=matricula, datos=datos)
        if rubrocreado:
            # fecha_primera_persion = (inscripcion.curso.periodo.inicioactividades.replace(day=1) + relativedelta(months=1))
            fecha_primera_persion = last_day_of_month(datetime(inscripcion.curso.periodo.inicioactividades.year, inscripcion.curso.periodo.inicioactividades.month, 1))
            # fecha_primera_persion = fecha_primera_persion-timedelta(days=1)
            for cantidad in range(1, valores.numeropensiones+1):
                pension = Pension(fecha=fecha_primera_persion, valor=valores.pension, matricula=matricula)
                pension.save()
                # mes_pension= fecha_primera_persion+timedelta(days=1)
                observ = 'PENSION DE {} EN EL MES DE {} {} EN EL PERIODO {}'.format(matricula.inscripcion.alumno.persona,
                                              MESES_EN_LETRAS[fecha_primera_persion.month-1], fecha_primera_persion.year,
                                              matricula.inscripcion.curso.periodo)
                datos = [{'fechavence': fecha_primera_persion, 'valor': pension.valor, 'iva': 12, 'observacion': observ}]
                rubrocreado = crear_rubro(persona=matricula.inscripcion.alumno.persona, pension=pension, datos=datos)
                if not rubrocreado:
                    break
                month = fecha_primera_persion.month + 1 if fecha_primera_persion.month <= 12 else 1
                year = fecha_primera_persion.year if fecha_primera_persion.month <= 12 else fecha_primera_persion.year+1
                fecha_primera_persion = last_day_of_month(datetime(year, month, 1))
            return True
    except Exception as e:
        return False


def crear_rubro(persona, pension=None, matricula=None, producto=None, datos=None):
    with transaction.atomic():
        try:
            mensaje =''
            rubro = Rubro(persona=persona, fecha=datetime.now(), iva=nombre_empresa())
            if pension:
                rubro.pension = pension
                rubro.iva = nombre_empresa().pk
                mes = pension.fecha+timedelta(days=1)
                mensaje = 'PENSION DEL MES DE {} {}'.format(MESES_EN_LETRAS[mes.month-1], pension.fecha.year)
            if matricula:
                rubro.matricula = matricula
                rubro.iva = nombre_empresa().pk
                mensaje = 'MATRICULA DE {} EN EL PERIODO {}'.format(matricula.inscripcion.alumno.persona, matricula.inscripcion.curso.periodo )
            if producto:
                rubro.producto = producto
                mensaje = str(producto.nombre)
            rubro.save()

            if datos is not None:
                rubro.nombre = mensaje
                rubro.fechavence = datos[0]['fechavence']
                rubro.valor = datos[0]['valor']
                rubro.valoriva = 0 if not rubro.iva else rubro.valor * (rubro.iva.iva.ivaporciento/100)
                rubro.valortotal = float(datos[0]['valor'])+rubro.valoriva
                rubro.saldo = rubro.valortotal
                rubro.observacion = datos[0]['observacion']
                rubro.cantidad = 1 if not  'cantidad' in datos[0] else int(datos[0]['cantidad'])
                rubro.save()
                return rubro
            else:
                transaction.set_rollback(True)
            return False
        except Exception as e:
            transaction.set_rollback(True)
            return False


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


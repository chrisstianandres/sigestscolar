from django.db import models

from apps.extras import ModeloBase


class Materia(ModeloBase):
    identificacion = models.CharField(default='', max_length=30, verbose_name=u'Codigo', unique=True)
    alias = models.CharField(default='', blank=True, null=True, max_length=100, verbose_name=u'Alias')
    nombre = models.CharField(default='', blank=True, null=True, max_length=30, verbose_name=u'Nombre')

    def __str__(self):
        return self.nombre
        # return u'%s - %s - %s' % (
        # self.nombre_completo(), self.profesor_principal() if self.profesor_principal() else '', self.nombre)

    class Meta:
        verbose_name = u"Materia"
        verbose_name_plural = u"Materias"
        unique_together = ('identificacion', 'alias', 'nombre',)

    @staticmethod
    def flexbox_query(q, extra=None):
        return Materia.objects.filter(
            Q(id__contains=q) | Q(asignatura__nombre__contains=q) | Q(identificacion__contains=q)).distinct().order_by(
            '-fin')[:30]

    def flexbox_repr(self):
        return self.nombre_completo() + " - " + self.nivel.paralelo + " (" + self.inicio.strftime(
            '%d-%m-%Y') + " / " + self.fin.strftime('%d-%m-%Y') + ") - " + self.id.__str__()

    def nombre_mostrar(self):
        return self.asignatura.nombre + ((" - " + self.alias) if self.alias else "") + " - [" + (
            self.asignaturamalla.nivelmalla.__str__() if self.asignaturamalla.nivelmalla else "") + "]" + ((
                                                                                                                       ' - ' + self.paralelo) if self.paralelo else '') + " - " + self.asignaturamalla.malla.carrera.alias + (
                   (" - %s" % self.profesor_principal()) if self.profesor_principal() else '')

    def horarioexamen(self):
        if self.horarioexamen_set.filter(status=True).exists():
            return self.horarioexamen_set.filter(status=True)
        return None

    def nombre_mostrar_solo(self):
        return self.asignatura.nombre + " - " + (
            (" - " + self.alias) if self.alias else "") + self.asignaturamalla.malla.carrera.alias + (
                   (' - ' + self.paralelo) if self.paralelo else '') + " - [" + (
                   self.asignaturamalla.nivelmalla.__str__() if self.asignaturamalla.nivelmalla else "") + "]"

    def abreviatura_dedicacion(self):
        # if self.profesor_principal():
        if ProfesorMateria.objects.filter(materia=self, activo=True).exists():
            profemat = ProfesorMateria.objects.filter(materia=self, activo=True)[0]
            distributivo = ProfesorDistributivoHoras.objects.filter(periodo=self.nivel.periodo,
                                                                    profesor=profemat.profesor)
            if distributivo:
                if distributivo[0].dedicacion_id == 1:
                    return "TC"
                elif distributivo[0].dedicacion_id == 2:
                    return "MT"
                elif distributivo[0].dedicacion_id == 3:
                    return "TP"
            else:
                return ''
        else:
            return ''

    def fecha_examen_materia(self, detalle):
        if self.horarioexamen_set.filter(detallemodelo=detalle, status=True).exists():
            return self.horarioexamen_set.filter(detallemodelo=detalle, status=True)[0].fecha
        return ''

    def turno_examen_materia(self, detalle):
        if self.horarioexamen_set.filter(detallemodelo=detalle, status=True).exists():
            return self.horarioexamen_set.filter(detallemodelo=detalle, status=True)[0].turno.id
        return 0

    def puede_cambiar_modelo(self):
        return not EvaluacionGenerica.objects.filter(detallemodeloevaluativo__modelo=self.modeloevaluativo,
                                                     valor__gt=0).exists()

    def documentos(self):
        return self.documentosmateria_set.all().order_by('fecha_creacion')

    def totalpreguntasdocentes(self):
        totalpreguntas = AvPreguntaDocente.objects.values("id").filter(materiaasignada__materia=self, status=True,
                                                                       estadolectura=True).count()
        return totalpreguntas if totalpreguntas else 0

    def tipo_profesormateria(self, profesor):
        if ProfesorMateria.objects.filter(materia=self, profesor=profesor).exists():
            tipoprofesormat = ProfesorMateria.objects.get(materia=self, profesor=profesor)
            return tipoprofesormat.tipoprofesor
        else:
            return ''

    def totalpreguntasalumnos(self):
        totalpreguntas = AvPreguntaDocente.objects.values("id").filter(materiaasignada__materia=self, status=True,
                                                                       estadolecturaalumno=True).count()
        return totalpreguntas if totalpreguntas else 0

    def tipo_profesor(self):
        if ProfesorMateria.objects.filter(materia=self):
            return ProfesorMateria.objects.filter(materia=self)[0].tipoprofesor
        return None

    def tiene_planificacion(self):
        return self.planificacionmateria_set.exists()

    def planificacionxfecha(self, fini, ffin):
        valor = self.planificacionmateria_set.filter(desde__gte=fini, desde__lte=ffin).order_by('tipoplanificacion',
                                                                                                'id')
        return valor

    def tipoevaluaciones(self):
        return TipoEvaluacionEvaluacion.objects.filter(planificacionmateria__materia=self).distinct()

    def finalizo(self):
        return self.fin < datetime.now().date()

    def tiene_proanalitico(self):
        if ContenidoResultadoProgramaAnalitico.objects.filter(
                programaanaliticoasignatura__asignaturamalla=self.asignaturamalla,
                programaanaliticoasignatura__activo=True, programaanaliticoasignatura__status=True).exists():
            return True
        return False

    def tiene_silabo(self):
        if Silabo.objects.filter(materia=self, status=True).exists():
            return True

    def coordinacion_materia(self):
        if self.nivel.nivellibrecoordinacion_set.exists():
            return self.nivel.nivellibrecoordinacion_set.all()[0].coordinacion
        return None

    def horas_restantes_horario(self):
        return null_to_numeric(
            Turno.objects.filter(clase__materia=self, clase__activo=True).aggregate(horas=Sum('horas'))['horas'])

    def max_capacidad_aula(self):
        return null_to_numeric(Aula.objects.filter(clase__materia=self, clase__activo=True).distinct().aggregate(
            capacidad=Min('capacidad'))['capacidad'])

    def tiene_capacidad(self):
        if CUPO_POR_MATERIA:
            return self.materiaasignada_set.values("id").exclude(retiramateria=True).count() < self.cupo
        return self.materiaasignada_set.values("id").exclude(retiramateria=True).count() < self.max_capacidad_aula()

    def aulas(self):
        return Aula.objects.filter(clase__materia=self, clase__activo=True).distinct().order_by('capacidad')

    def capacidad_sobrepasada(self):
        if CUPO_POR_MATERIA:
            if self.materiaasignada_set.values("id").exclude(retiramateria=True).count() > self.cupo:
                return self.materiaasignada_set.values("id").exclude(retiramateria=True).count() - self.cupo
        else:
            if self.materiaasignada_set.values("id").exclude(retiramateria=True).count() > self.max_capacidad_aula():
                return self.materiaasignada_set.values("id").exclude(
                    retiramateria=True).count() - self.max_capacidad_aula()
        return 0

    def capcidad_total(self):
        if CUPO_POR_MATERIA:
            return self.cupo
        return self.max_capacidad_aula()

    def capacidad_disponible(self):
        if CUPO_POR_MATERIA:
            if self.materiaasignada_set.values("id").exclude(retiramateria=True).count() < self.cupo:
                return self.cupo - self.materiaasignada_set.values("id").exclude(retiramateria=True).count()
        else:
            if self.materiaasignada_set.values("id").exclude(retiramateria=True).count() < self.max_capacidad_aula():
                return self.max_capacidad_aula() - self.materiaasignada_set.values("id").exclude(
                    retiramateria=True).count()
        return 0

    def cerrar_disponible(self):
        return not self.materiaasignada_set.filter(Q(cerrado=False) | Q(cerrado=None)).exists()

    def tiene_clases(self):
        return self.lecciones().count() > 0

    def cantidad_clases(self):
        return self.clase_set.values("id").filter(activo=True).count()

    def profesores_materia(self):
        return self.profesormateria_set.filter(activo=True).order_by('id')

    def profesores_materia_dia(self, fecha):
        if self.profesormateria_set.filter(desde__lte=fecha, hasta__gte=fecha, principal=True).exists():
            return self.profesormateria_set.filter(desde__lte=fecha, hasta__gte=fecha, principal=True)[0]
        return None

    def profesores(self):
        return ", ".join([x.profesor.persona.nombre_completo_inverso() for x in self.profesores_materia()])

    def horario(self):
        if self.clase_set.filter(activo=True).exists():
            return self.clase_set.filter(activo=True).order_by('dia')
        return None

    def horario_asignado(self):
        if self.clase_set.filter(activo=True).exists():
            return self.clase_set.filter(activo=True)[0]
        return None

    def horarios_asignados(self):
        if self.clase_set.filter(activo=True).exists():
            return self.clase_set.filter(activo=True).distinct('turno')
        return None

    def clases_informacion(self):
        return ["%s - %s a %s - (%s al %s) - %s" % (
        x.dia_semana(), x.turno.comienza.strftime('%H:%M %p'), x.turno.termina.strftime('%H:%M %p'),
        x.inicio.strftime('%d-%m-%Y'), x.fin.strftime('%d-%m-%Y'), x.aula.nombre) for x in
                self.clase_set.filter(activo=True).order_by('dia', 'turno__comienza')]

    def dias_programados(self):
        dias_lista = []
        for dia in self.clase_set.filter(activo=True).order_by('dia', 'turno__comienza'):
            dia_nombre = dia.dia_semana()[0:3].__str__()
            if dia_nombre not in dias_lista:
                dias_lista.append(dia_nombre)
        diassemana = ",".join(dias_lista)
        return "[" + diassemana + "]"

    def profesor_principal(self):
        if self.profesormateria_set.filter(principal=True, activo=True).exists():
            return self.profesormateria_set.filter(principal=True, activo=True)[0].profesor
        return None

    def profesor_materia_principal(self):
        if self.profesormateria_set.filter(principal=True, activo=True).exists():
            return self.profesormateria_set.filter(principal=True, activo=True)[0]
        return None

    def profesor_actual(self):
        hoy = datetime.now().date()
        if self.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy).exists():
            return self.profesormateria_set.filter(desde__lte=hoy, hasta__gte=hoy)[0]
        return self.profesormateria_set.all()[0]

    def nombre_completo(self):
        return self.asignatura.nombre + (" - " + self.alias if self.alias else "") + " - [" + (
            self.identificacion if self.identificacion else "###") + "]" + (
                   ' - ' + self.paralelo if self.paralelo else '') + " - " + self.asignaturamalla.malla.carrera.alias

    def nombre_completo_materia(self):
        return self.asignatura.nombre + (
            ' - ' + self.paralelo if self.paralelo else '') + " - " + self.asignaturamalla.malla.carrera.nombre + ' ' + self.asignaturamalla.malla.carrera.mencion

    def nombre_horario(self):
        return self.asignatura.nombre + (" - " + self.alias if self.alias else "") + " - [" + (
            self.identificacion if self.identificacion else "###") + "] " + (
                   ' - ' + self.paralelo if self.paralelo else '') + " (" + self.inicio.strftime(
            '%d-%m-%Y') + " al " + self.fin.strftime('%d-%m-%Y') + ")"

    def asignados_a_esta_materia(self):
        return self.materiaasignada_set.filter(matricula__estado_matricula=2).order_by(
            'matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2',
            'matricula__inscripcion__persona__nombres')

    def asignados_a_esta_materia_por_id(self):
        return self.materiaasignada_set.filter(matricula__estado_matricula=2).order_by('id')

    def asignados_a_esta_materia_sinretirados(self):
        return self.materiaasignada_set.filter(materiaasignadaretiro__isnull=True,
                                               matricula__estado_matricula=2).distinct().order_by(
            'matricula__inscripcion__persona__apellido1')

    def cantidad_asignados_a_esta_materia_sinretirados(self):
        return self.materiaasignada_set.values("id").filter(materiaasignadaretiro__isnull=True,
                                                            matricula__estado_matricula=2,
                                                            status=True).distinct().count()

    def cantidad_asignados_a_esta_materia_sinretirados_inscritos(self):
        return self.materiaasignada_set.values("id").filter(materiaasignadaretiro__isnull=True,
                                                            matricula__estado_matricula=1,
                                                            status=True).distinct().count()

    def cantidad_matriculas_materia(self):
        return self.materiaasignada_set.values("id").filter(matricula__estado_matricula=2).count()

    def tiene_matriculas(self):
        return self.materiaasignada_set.values("id").filter(matricula__estado_matricula=2).exists()

    def lecciones(self):
        return LeccionGrupo.objects.filter(lecciones__clase__materia=self, status=True).order_by('fecha', 'horaentrada')

    def lecciones_individuales(self):
        lecciones = Leccion.objects.filter(clase__materia=self).order_by('lecciongrupo__fecha',
                                                                         'lecciongrupo__horaentrada')
        for leccion in lecciones:
            if not leccion.leccion_grupo():
                leccion.delete()
        return Leccion.objects.filter(clase__materia=self).order_by('lecciongrupo__fecha', 'lecciongrupo__horaentrada')

    def mis_lecciones(self, profesor):
        return LeccionGrupo.objects.filter(lecciones__clase__materia=self, profesor=profesor).order_by('fecha',
                                                                                                       'horaentrada')

    def syllabus_malla(self):
        asignaturamallas = []
        if MATRICULACION_LIBRE:
            asignaturamallas.append(self.asignaturamalla)
        else:
            for malla in self.nivel.carrera.malla_set.all():
                if malla.asignaturamalla_set.filter(asignatura=self.asignatura).exists():
                    asignaturamalla = malla.asignaturamalla_set.filter(asignatura=self.asignatura)[0]
                    if asignaturamalla not in asignaturamallas:
                        asignaturamallas.append(asignaturamalla)
        return asignaturamallas

    def micro(self, profesor):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_MICRO, profesor=profesor).exists():
            return Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_MICRO, profesor=profesor)[0]
        return None

    def syllabus(self, profesor):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, profesor=profesor).exists():
            return \
            Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, profesor=profesor).order_by('-id')[0]
        return None

    def syllabuspdf(self):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, archivo__contains='.pdf').exists():
            return \
            Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, archivo__contains='.pdf').order_by(
                '-id')[0]
        return None

    def syllabusword(self):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, archivo__contains='.doc').exists():
            return \
            Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, archivo__contains='.doc').order_by(
                '-id')[0]
        return None

    def syllabusaux(self, profesor, ext):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, profesor=profesor,
                                  archivo__contains=ext).exists():
            return Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_SYLLABUS, profesor=profesor,
                                          archivo__contains=ext)[0]
        return None

    def deber(self):
        if Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_DEBERES).exists():
            return Archivo.objects.filter(materia=self, tipo_id=ARCHIVO_TIPO_DEBERES).distinct('lecciongrupo')
        return None

    def en_fecha(self):
        return self.inicio <= datetime.now().date() <= self.fin

    def pasada_fecha(self):
        return datetime.now().date() > self.fin

    def tiene_calificaciones(self):
        return self.materiaasignada_set.filter(notafinal__gt=0).exists()

    def cerrar(self):
        for ma in self.materiaasignada_set.all():
            ma.cerrado = True
            ma.save(True)
            ma.actualiza_estado()
        self.cerrado = True
        self.fechacierre = datetime.now().date()
        self.save()

    def tiene_horario(self):
        return self.clase_set.exists()

    def horarios(self):
        return self.clase_set.filter(activo=True).order_by('inicio', 'dia', 'turno__comienza')

    def horarios_del_profesor(self, profesor):
        clase = Clase.objects.filter(activo=True, materia=self, materia__nivel__periodo=self.nivel.periodo,
                                     materia__profesormateria__profesor=profesor)
        if clase:
            tipoprofesor = ProfesorMateria.objects.filter(materia=self, status=True, profesor=profesor)[0].tipoprofesor
            return clase.filter(tipoprofesor=tipoprofesor).order_by('inicio', 'dia', 'turno__comienza')
        return None

    def profesor_materia(self, profesor):
        profesor_materia = ProfesorMateria.objects.filter(materia=self, status=True, profesor=profesor)
        if profesor_materia:
            return profesor_materia[0]
        return None

    def carrera(self):
        if self.nivel.carrera:
            return self.nivel.carrera
        elif self.asignaturamalla:
            return self.asignaturamalla.malla.carrera
        return None

    def recalcularmateria(self):
        for materiaasignada in self.materiaasignada_set.all():
            modeloevaluativomateria = materiaasignada.materia.modeloevaluativo
            d = locals()
            exec(modeloevaluativomateria.logicamodelo, globals(), d)
            d['calculo_modelo_evaluativo'](materiaasignada)
            materiaasignada.notafinal = round(materiaasignada.notafinal, modeloevaluativomateria.notafinaldecimales)
            if materiaasignada.notafinal > modeloevaluativomateria.notamaxima:
                materiaasignada.notafinal = modeloevaluativomateria.notamaxima
            materiaasignada.save()
            encurso = True
            for campomodelo in modeloevaluativomateria.campos().filter(actualizaestado=True):
                if materiaasignada.valor_nombre_campo(campomodelo.nombre) > 0:
                    encurso = False
            if not encurso:
                materiaasignada.actualiza_estado()
            else:
                materiaasignada.estado_id = NOTA_ESTADO_EN_CURSO
                materiaasignada.save()

    def recalcularnota(self):
        if PlanificacionMateria.objects.filter(materia=self, paraevaluacion=True).exists():
            for tipoevaluacion in self.modeloevaluativo.detallemodeloevaluativo_set.filter(dependiente=False,
                                                                                           nombre__contains='N'):
                if PlanificacionMateria.objects.filter(materia=self, paraevaluacion=True,
                                                       tipoevaluacion=tipoevaluacion).exists():
                    for ma in self.asignados_a_esta_materia():
                        valor = self.promedio_calificacion_deberes(ma, tipoevaluacion)
                        actualizar_nota_planificacion(ma.id, tipoevaluacion.nombre, valor)
        else:
            self.arreglarecalcularnota()

    def arreglarecalcularnota(self):
        for ma in self.asignados_a_esta_materia():
            ma.actualiza_notafinal()

    def promedio_calificacion_deberes(self, materiaasignada, tipoevaluacion):
        nota = MateriaAsignadaPlanificacion.objects.filter(materiaasignada=materiaasignada, planificacion__materia=self,
                                                           planificacion__paraevaluacion=True,
                                                           planificacion__tipoevaluacion=tipoevaluacion).aggregate(
            valor=Round0(Avg('calificacion')))['valor']
        return nota

    def actualizar_promedio_deberes(self, tipoevaluacion, bandera=False):
        if PlanificacionMateria.objects.filter(materia=self, paraevaluacion=True,
                                               tipoevaluacion=tipoevaluacion).exists():
            for ma in self.asignados_a_esta_materia():
                valor = self.promedio_calificacion_deberes(ma, tipoevaluacion)
                actualizar_nota_planificacion(ma.id, tipoevaluacion.nombre, valor)
        elif bandera:
            self.vaciarnota(tipoevaluacion)
            self.arreglarecalcularnota()

    def vaciarnota(self, detallemodeloevaluativo):
        for materiaasignada in MateriaAsignada.objects.filter(materia=self, status=True):
            EvaluacionGenerica.objects.filter(materiaasignada=materiaasignada, status=True,
                                              detallemodeloevaluativo=detallemodeloevaluativo).update(valor=0)

    def cronogramacalificaciones(self):
        if self.usaperiodocalificaciones:
            if self.cronogramaevaluacionmodelo_set.exists():
                return self.cronogramaevaluacionmodelo_set.all()[0]
            elif CronogramaEvaluacionModelo.objects.filter(periodo=self.nivel.periodo, modelo=self.modeloevaluativo,
                                                           materias__isnull=True).order_by('id').exists():
                return \
                CronogramaEvaluacionModelo.objects.filter(periodo=self.nivel.periodo, modelo=self.modeloevaluativo,
                                                          materias__isnull=True).order_by('id')[0]
        return None

    def cantidad_estudiantes_encuestados_docencia(self, periodo, profesor):
        return self.respuestaevaluacionacreditacion_set.values("id").filter(tipoinstrumento=1, proceso__periodo=periodo,
                                                                            profesor=profesor,
                                                                            materiaasignada__isnull=False).count()

    def resultado_evaluacion_estudiantes_docencia(self, periodo, profesor):
        return round(null_to_numeric(
            self.respuestaevaluacionacreditacion_set.filter(tipoinstrumento=1, proceso__periodo=periodo,
                                                            profesor=profesor, materiaasignada__isnull=False).aggregate(
                promedio=Avg('valortotaldocencia'))['promedio']), 1)

    def promedio_nota_general(self):
        return round(
            null_to_numeric(self.asignados_a_esta_materia_sinretirados().aggregate(prom=Avg('notafinal'))['prom']), 2)

    def promedio_asistencia_general(self):
        return round(null_to_numeric(
            self.asignados_a_esta_materia_sinretirados().aggregate(prom=Avg('asistenciafinal'))['prom']), 2)

    def promedio_nota_primer_parcial_con_cero(self):
        return round(
            null_to_numeric(self.asignados_a_esta_materia_sinretirados().aggregate(prom=Avg('notafinal'))['prom']), 2)

    def cantidad_practicas_profesor(self, profesor):
        return self.practicapreprofesional_set.values("id").filter(profesor=profesor).count()

    def cantidad_practicas(self):
        return self.practicapreprofesional_set.values("id").count()

    def total_asistencias(self, fecha):
        asistencia = AsistenciaLeccion.objects.values("id").filter(materiaasignada__materia=self,
                                                                   leccion__fecha__lte=fecha).count()
        return asistencia if asistencia else 0

    def materias_cupo(self, matricula, asignatura):
        if MateriaCupo.objects.filter(materia=self, matricula_id=matricula).exists():
            materiaid = MateriaCupo.objects.get(materia=self, matricula_id=matricula)
            return materiaid.materia.id
        else:
            if MateriaCupo.objects.filter(materia__asignatura__id=asignatura, matricula_id=matricula).exists():
                return 1
            else:
                return 0

    def profesormateria(self, profesor):
        return ProfesorMateria.objects.get(status=True, materia=self, profesor=profesor)

    def materias_nomcompleto(self):
        return u'%s - %s - %s - [%s]' % (
        self.nombre_completo(), self.profesor_principal() if self.profesor_principal() else '', self.nivel.paralelo,
        self.id)

    def tiene_silabo_digital(self):
        return True if self.silabo_set.all().exists() else False

    # def tiene_silabo_semanal(self):
    #     return True if self.silabo_set.get().silabosemanal_set.all().exists() else False

    def tiene_silabo_semanal(self):
        if self.silabo_set.filter(status=True).exists():
            for silabo in self.silabo_set.filter(status=True):
                if silabo.silabosemanal_set.all().exists():
                    return True
        return False

    def estado_silabo_digital(self):
        if self.silabo_set.filter(status=True, programaanaliticoasignatura__activo=True).exists():
            return self.silabo_set.filter(status=True, programaanaliticoasignatura__activo=True)[
                0].estado_semanas_llenas()

    def silabo_actual(self):
        if self.silabo_set.filter(status=True).exists():
            return self.silabo_set.filter(status=True)[0]
        return None

    def totalcomunicacionmasiva(self):
        return self.avcomunicacion_set.values("id").order_by("-fecha_creacion")[:4].count()

    def laboratorio_uso(self):
        return True if self.laboratorio.gpguiapracticasemanal_set.all().exists() else False

    def tiene_silabo_archivo(self):
        return True if Archivo.objects.filter(materia=self, status=True).exists() else False

    def libros_silabo(self):
        return DetalleSilaboSemanalBibliografiaDocente.objects.filter(silabosemanal__silabo__materia=self).distinct(
            'librokohaprogramaanaliticoasignatura')

    def libros_programaanalitico(self):
        return BibliografiaProgramaAnaliticoAsignatura.objects.filter(
            programaanaliticoasignatura__asignaturamalla=self.asignaturamalla).distinct(
            'librokohaprogramaanaliticoasignatura')

    def detallemodeloevaluativo(self):
        if self.modeloevaluativo.detallemodeloevaluativo_set.filter(status=True, alternativa__id=20,
                                                                    modelo__status=True).exists():
            return self.modeloevaluativo.detallemodeloevaluativo_set.filter(status=True, alternativa__id=20,
                                                                            modelo__status=True)
        return None

    def save(self, *args, **kwargs):
        self.identificacion = self.identificacion.upper().strip()
        self.alias = self.alias.upper().strip() if self.alias else ''
        self.nombre = self.nombre.upper().strip() if self.nombre else ''
        # if self.inicio < self.nivel.inicio:
        #     self.inicio = self.nivel.inicio
        # if not self.id:
        #     self.fechafinasistencias = self.fin
        super(Materia, self).save(*args, **kwargs)

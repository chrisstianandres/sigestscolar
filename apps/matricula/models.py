from datetime import datetime, timedelta

from django.db import models
from django.db.models import Q

from apps.extras import ModeloBase
from apps.inscripcion.models import Inscripcion





class Matricula(ModeloBase):
    inscripcion = models.ForeignKey(Inscripcion, verbose_name=u"Inscripción", on_delete=models.PROTECT)
    pago = models.BooleanField(default=False, verbose_name=u"Pago")
    becado = models.BooleanField(default=False, verbose_name=u"Becado")
    porcientobeca = models.FloatField(default=0, verbose_name=u"% de Beca")
    observaciones = models.TextField(default='', max_length=1000, verbose_name=u"Observaciones")
    fecha = models.DateField(null=True, blank=True, verbose_name=u"Fecha")
    fechatope = models.DateField(null=True, blank=True, verbose_name=u"Fecha límite de cancelación")
    cerrada = models.BooleanField(default=False, verbose_name=u"Cerrada")

    def __str__(self):
        return '{}{}{}'.format(self.inscripcion.alumno, self.observaciones, self.fecha)

    class Meta:
        verbose_name = u"Matricula"
        verbose_name_plural = u"Matriculas"
        unique_together = ('inscripcion',)

    @staticmethod
    def flexbox_query(q, extra=None):
        if ' ' in q:
            s = q.split(" ")
            return Matricula.objects.filter(Q(inscripcion__alumno__persona__apellido1__contains=s[0]) & Q(inscripcion__persona__apellido2__contains=s[1])).distinct()[:25]
        return Matricula.objects.filter(Q(inscripcion__alumno__persona__nombres__contains=q) | Q(inscripcion__persona__apellido1__contains=q) | Q(inscripcion__persona__apellido2__contains=q) | Q(inscripcion__persona__cedula__contains=q)).distinct()[:25]


    def clases_horario(self, dia, turno, periodo):
        return Clase.objects.filter(dia=dia, activo=True, turno=turno, materia__nivel__periodo=periodo, materia__materiaasignada__matricula=self)

    def permiso_evaluacion_docente(self, materia):
        if self.materiaasignada_set.filter(materia=materia).exists():
            materiaasignada = self.materiaasignada_set.filter(materia=materia)[0]
            if materiaasignada.evaluar:
                return datetime.now() <= materiaasignada.fechaevaluar + timedelta(hours=HORAS_AUTORIZADO_EVALUACION_DOCENTE)
        return False

    def confirmar_matricula(self):
        if ConfirmarMatricula.objects.filter(matricula=self, status=True).exists():
            confirmarmatricula = ConfirmarMatricula.objects.filter(matricula=self, status=True)
        else:
            confirmarmatricula = ConfirmarMatricula(matricula=self, estado=True)
            confirmarmatricula.save()
        return confirmarmatricula

    def en_fecha(self):
        return self.nivel.periodo.fin >= datetime.now().date() >= self.nivel.periodo.inicio

    def periodo_name(self):
        return "%s" % self.nivel.periodo

    def retirado(self):
        return self.retiradomatricula

    def materias_profesor(self, profesor):
        return ProfesorMateria.objects.filter(profesor=profesor, activo=True, principal=True, materia__in=[x.materia for x in self.materiaasignada_set.all()])

    def nivel_cerrado(self):
        return self.nivel.cerrado

    def cantidad_materias(self):
        return self.materiaasignada_set.values("id").count()

    def materias(self):
        return self.materiaasignada_set.all()

    def promedio_asistencia_alumno(self, anterior, minasistencia, minpromedio):
        materias = MateriaAsignada.objects.filter(status=True,
                                                  matricula__inscripcion=self.inscripcion,
                                                  matricula__nivel__periodo__id=anterior,
                                                  materiaasignadaretiro__isnull=True)
        verificacion = 0
        lista = []
        suma = 0
        promedio = 0
        sumasis = 0
        asistencia = 0
        total = materias.count()
        for m in materias:
            suma += m.notafinal
            sumasis += m.asistenciafinal
            if m.estado.id != 1:
                verificacion = 1
                break
        if suma > 0 and verificacion == 0:
            promedio = round(suma / total, 2)
            asistencia = round(sumasis / total, 2)
            if verificacion == 0 and promedio >= minpromedio and asistencia >= minasistencia:
                lista.append([promedio, asistencia])
                return lista
            else:
                return None

    def promedio_asistencia_alumno_sin(self, anterior):
        materias = MateriaAsignada.objects.filter(status=True,
                                                  matricula__inscripcion=self.inscripcion,
                                                  matricula__nivel__periodo__id=anterior,
                                                  materiaasignadaretiro__isnull=True)
        # materias = MateriaAsignada.objects.filter(status=True,
        #                                           matricula__inscripcion__id=29159,
        #                                           matricula__nivel__periodo__id=7,
        #                                           materiaasignadaretiro__isnull=True)
        verifica = 0
        lista = []
        suma = 0
        promedio = 0
        sumasis = 0
        asistencia = 0
        total = materias.count()
        for m in materias:
            suma += m.notafinal
            sumasis += m.asistenciafinal
            if m.estado.id != 1:
                verifica = 1
                break
        if suma > 0 and verifica == 0:
            promedio = round(suma / total, 2)
            asistencia = round(sumasis / total, 2)
            lista.append([promedio, asistencia])
            return lista
        else:
            return None

    def materias_periodo(self):
        return Materia.objects.filter(materiaasignada__matricula=self).distinct()

    def materiasxalumno(self, idper, idinsc):
        materias = Materia.objects.filter(materiaasignada__matricula__inscripcion__id=idinsc, nivel__periodo__id=idper).distinct()
        return materias

    def calificacionesxalumno(self, idper, idinsc):
        calificaciones = MateriaAsignada.objects.filter(matricula__inscripcion__id=idinsc,
                                                        matricula__nivel__periodo__id=idper).distinct()
        return calificaciones

    def retiro_academico(self, motivo):
        retiro = RetiroMatricula(matricula=self,
                                 fecha=datetime.now().date(),
                                 motivo=motivo)
        retiro.save()
        for materia in self.materiaasignada_set.all():
            if not materia.retiramateria:
                retiromateria = MateriaAsignadaRetiro(materiaasignada=materia,
                                                      motivo='RETIRO DE MATRICULA',
                                                      valida=False,
                                                      fecha=retiro.fecha)
                retiromateria.save()
                materia.retiramateria = True
                materia.save()
        self.retiradomatricula = True
        self.save()

    def calculos_finanzas(self, request, cobro):
        # costo de matricula carlos loyola 03-03-2017
        from sagest.models import TipoOtroRubro, Rubro
        persona = self.inscripcion.persona
        periodo = self.nivel.periodo
        valorgrupoeconomico = self.inscripcion.persona.fichasocioeconomicainec_set.all()[
            0].grupoeconomico.periodogruposocioeconomico_set.filter(periodo=periodo, status=True)[0].valor
        porcentaje_gratuidad = periodo.porcentaje_gratuidad
        valor_maximo = periodo.valor_maximo
        costo_materia_total = 0
        tiporubroarancel = TipoOtroRubro.objects.filter(pk=RUBRO_ARANCEL)[0]
        tiporubromatricula = TipoOtroRubro.objects.filter(pk=RUBRO_MATRICULA)[0]
        if cobro > 0:
            for materiaasignada in self.materiaasignada_set.filter(status=True):
                costo_materia = 0
                if cobro == 1:
                    costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                        Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                else:
                    if cobro == 2:
                        if materiaasignada.matriculas > 1:
                            costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                                Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                    else:
                        costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                            Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                costo_materia_total += costo_materia

        if costo_materia_total > 0:
            # self.estado_matricula = 2
            # self.save(request)
            valor_porcentaje = Decimal((costo_materia_total * porcentaje_gratuidad) / 100).quantize(Decimal('.01'))
            rubro = Rubro(tipo=tiporubroarancel,
                          persona=persona,
                          relacionados=None,
                          matricula=self,
                          # contratorecaudacion = None,
                          nombre=tiporubroarancel.nombre + ' - ' + periodo.nombre,
                          cuota=1,
                          fecha=datetime.now().date(),
                          fechavence=datetime.now().date() + timedelta(days=1),
                          valor=costo_materia_total,
                          iva_id=1,
                          valoriva=0,
                          valortotal=costo_materia_total,
                          saldo=costo_materia_total,
                          cancelado=False)
            rubro.save(request)

            valor = valor_porcentaje
            if valor_porcentaje > valor_maximo:
                valor = valor_maximo
            rubro1 = Rubro(tipo=tiporubromatricula,
                           persona=persona,
                           relacionados=rubro,
                           matricula=self,
                           # contratorecaudacion = None,
                           nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                           cuota=1,
                           fecha=datetime.now().date(),
                           fechavence=datetime.now().date() + timedelta(days=1),
                           valor=valor,
                           iva_id=1,
                           valoriva=0,
                           valortotal=valor,
                           saldo=valor,
                           cancelado=False)
            rubro1.save(request)

            # valor multa por no se ordinaria
            if self.tipomatricula.id != 1:
                valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                rubro1 = Rubro(tipo=tiporubromatricula,
                               persona=persona,
                               relacionados=None,
                               matricula=self,
                               # contratorecaudacion = None,
                               nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                               cuota=1,
                               fecha=datetime.now().date(),
                               fechavence=datetime.now().date() + timedelta(days=1),
                               valor=valor,
                               iva_id=1,
                               valoriva=0,
                               valortotal=valor,
                               saldo=valor,
                               cancelado=False)
                rubro1.save(request)

        else:
            if self.tipomatricula.id == 1:
                self.estado_matricula = 2
                self.save(request)
            else:
                valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                rubro1 = Rubro(tipo=tiporubromatricula,
                               persona=persona,
                               relacionados=None,
                               matricula=self,
                               # contratorecaudacion = None,
                               nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                               cuota=1,
                               fecha=datetime.now().date(),
                               fechavence=datetime.now().date() + timedelta(days=1),
                               valor=valor,
                               iva_id=1,
                               valoriva=0,
                               valortotal=valor,
                               saldo=valor,
                               cancelado=False)
                rubro1.save(request)
                # costo de matricula carlos loyola 03-03-2017

    def calculos_finanzas_adicional(self, request, materiaasignada, cobro):
        # costo de matricula carlos loyola 03-03-2017
        from sagest.models import TipoOtroRubro, Rubro
        persona = self.inscripcion.persona
        periodo = self.nivel.periodo
        valorgrupoeconomico = self.inscripcion.persona.fichasocioeconomicainec_set.all()[
            0].grupoeconomico.periodogruposocioeconomico_set.filter(periodo=periodo, status=True)[0].valor
        porcentaje_gratuidad = periodo.porcentaje_gratuidad
        valor_maximo = periodo.valor_maximo
        rubro_anterior_matricula = None
        if Rubro.objects.filter(matricula=materiaasignada.matricula, relacionados__isnull=True, status=True).exists():
            rubro_anterior_matricula = \
            Rubro.objects.filter(matricula=materiaasignada.matricula, relacionados__isnull=True, status=True)[0]

        costo_materia_total = 0
        tiporubroarancel = TipoOtroRubro.objects.filter(pk=RUBRO_ARANCEL)[0]
        tiporubromatricula = TipoOtroRubro.objects.filter(pk=RUBRO_MATRICULA)[0]

        if cobro > 0:
            for materiaasignada in self.materiaasignada_set.filter(status=True):
                costo_materia = 0
                if cobro == 1:
                    costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                        Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                else:
                    if cobro == 2:
                        if materiaasignada.matriculas > 1:
                            costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                                Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                    else:
                        costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                            Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                costo_materia_total += costo_materia

        valor_pagado_arancel = 0
        if Rubro.objects.filter(matricula=self, status=True, tipo=tiporubroarancel, cancelado=True).exists():
            valor_pagado_arancel = \
            Rubro.objects.filter(matricula=self, status=True, tipo=tiporubroarancel, cancelado=True).aggregate(
                suma=Sum('valor'))['suma']
            costo_materia_total = costo_materia_total - valor_pagado_arancel

        if costo_materia_total > 0:
            self.estado_matricula = 1
            self.save(request)
            valor_porcentaje = Decimal((costo_materia_total * porcentaje_gratuidad) / 100).quantize(Decimal('.01'))
            rubro = Rubro(tipo=tiporubroarancel,
                          persona=persona,
                          relacionados=rubro_anterior_matricula,
                          matricula=self,
                          # contratorecaudacion = None,
                          nombre=tiporubroarancel.nombre + ' - ' + periodo.nombre,
                          cuota=1,
                          fecha=datetime.now().date(),
                          fechavence=datetime.now().date() + timedelta(days=1),
                          valor=costo_materia_total,
                          iva_id=1,
                          valoriva=0,
                          valortotal=costo_materia_total,
                          saldo=costo_materia_total,
                          cancelado=False)
            rubro.save(request)

            valor = valor_porcentaje

            valor_pagado_matricula = 0
            if Rubro.objects.filter(matricula=self, status=True, tipo=tiporubromatricula).exists():
                valor_pagado_matricula = Rubro.objects.filter(matricula=self, status=True, tipo=tiporubromatricula)[
                    0].valor
            if (valor + valor_pagado_matricula) > valor_maximo:
                valor = valor_maximo - valor_pagado_matricula

            if valor > 0:
                rubro1 = Rubro(tipo=tiporubromatricula,
                               persona=persona,
                               relacionados=rubro_anterior_matricula,
                               matricula=self,
                               # contratorecaudacion = None,
                               nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                               cuota=1,
                               fecha=datetime.now().date(),
                               fechavence=datetime.now().date() + timedelta(days=1),
                               valor=valor,
                               iva_id=1,
                               valoriva=0,
                               valortotal=valor,
                               saldo=valor,
                               cancelado=False)
                rubro1.save(request)

                # # valor multa por no se ordinaria
                # if self.tipomatricula.id != 1:
                #     valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                #     rubro1 = Rubro(tipo=tiporubromatricula,
                #                    persona=persona,
                #                    relacionados=None,
                #                    matricula=self,
                #                    # contratorecaudacion = None,
                #                    nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                #                    cuota=1,
                #                    fecha=datetime.now().date(),
                #                    fechavence=datetime.now().date() + timedelta(days=1),
                #                    valor=valor,
                #                    iva_id=1,
                #                    valoriva=0,
                #                    valortotal=valor,
                #                    saldo=valor,
                #                    cancelado=False)
                #     rubro1.save(request)
        else:
            if self.tipomatricula.id == 1:
                self.estado_matricula = 2
                self.save(request)
                # else:
                #     valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                #     rubro1 = Rubro(tipo=tiporubromatricula,
                #                    persona=persona,
                #                    relacionados=None,
                #                    matricula=self,
                #                    # contratorecaudacion = None,
                #                    nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                #                    cuota=1,
                #                    fecha=datetime.now().date(),
                #                    fechavence=datetime.now().date() + timedelta(days=1),
                #                    valor=valor,
                #                    iva_id=1,
                #                    valoriva=0,
                #                    valortotal=valor,
                #                    saldo=valor,
                #                    cancelado=False)
                #     rubro1.save(request)
                #     # costo de matricula carlos loyola 03-03-2017

    def calculos_finanzas_adicional_aux(self, request, cobro):
        # costo de matricula carlos loyola 03-03-2017
        from sagest.models import TipoOtroRubro, Rubro
        persona = self.inscripcion.persona
        periodo = self.nivel.periodo
        valorgrupoeconomico = self.inscripcion.persona.fichasocioeconomicainec_set.all()[
            0].grupoeconomico.periodogruposocioeconomico_set.filter(periodo=periodo, status=True)[0].valor
        porcentaje_gratuidad = periodo.porcentaje_gratuidad
        valor_maximo = periodo.valor_maximo
        rubro_anterior_matricula = None
        if Rubro.objects.filter(matricula=self, relacionados__isnull=True, status=True).exists():
            rubro_anterior_matricula = Rubro.objects.filter(matricula=self, relacionados__isnull=True, status=True)[0]

        costo_materia_total = 0
        tiporubroarancel = TipoOtroRubro.objects.filter(pk=RUBRO_ARANCEL)[0]
        tiporubromatricula = TipoOtroRubro.objects.filter(pk=RUBRO_MATRICULA)[0]

        if cobro > 0:
            for materiaasignada in self.materiaasignada_set.filter(status=True):
                costo_materia = 0
                if cobro == 1:
                    costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                        Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                else:
                    if cobro == 2:
                        if materiaasignada.matriculas > 1:
                            costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                                Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                    else:
                        costo_materia = Decimal(Decimal(materiaasignada.materia.creditos).quantize(
                            Decimal('.01')) * valorgrupoeconomico).quantize(Decimal('.01'))
                costo_materia_total += costo_materia

        valor_pagado_arancel = 0
        if Rubro.objects.filter(matricula=self, status=True, tipo=tiporubroarancel, cancelado=True).exists():
            valor_pagado_arancel = \
            Rubro.objects.filter(matricula=self, status=True, tipo=tiporubroarancel, cancelado=True).aggregate(
                suma=Sum('valor'))['suma']
            costo_materia_total = costo_materia_total - valor_pagado_arancel

        if costo_materia_total > 0:
            self.estado_matricula = 1
            self.save(request)
            valor_porcentaje = Decimal((costo_materia_total * porcentaje_gratuidad) / 100).quantize(Decimal('.01'))
            rubro = Rubro(tipo=tiporubroarancel,
                          persona=persona,
                          relacionados=rubro_anterior_matricula,
                          matricula=self,
                          # contratorecaudacion = None,
                          nombre=tiporubroarancel.nombre + ' - ' + periodo.nombre,
                          cuota=1,
                          fecha=datetime.now().date(),
                          fechavence=datetime.now().date() + timedelta(days=1),
                          valor=costo_materia_total,
                          iva_id=1,
                          valoriva=0,
                          valortotal=costo_materia_total,
                          saldo=costo_materia_total,
                          cancelado=False)
            rubro.save(request)

            valor = valor_porcentaje

            valor_pagado_matricula = 0
            if Rubro.objects.filter(matricula=self, status=True, tipo=tiporubromatricula).exists():
                valor_pagado_matricula = Rubro.objects.filter(matricula=self, status=True, tipo=tiporubromatricula)[
                    0].valor

            if valor_pagado_matricula < valor:
                valor = valor - valor_pagado_matricula
                if (valor + valor_pagado_matricula) > valor_maximo:
                    valor = valor_maximo - valor_pagado_matricula
            else:
                valor = 0

            if valor > 0:
                rubro1 = Rubro(tipo=tiporubromatricula,
                               persona=persona,
                               relacionados=rubro_anterior_matricula,
                               matricula=self,
                               # contratorecaudacion = None,
                               nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                               cuota=1,
                               fecha=datetime.now().date(),
                               fechavence=datetime.now().date() + timedelta(days=1),
                               valor=valor,
                               iva_id=1,
                               valoriva=0,
                               valortotal=valor,
                               saldo=valor,
                               cancelado=False)
                rubro1.save(request)

            # valor multa por no se ordinaria
            if self.tipomatricula.id != 1:
                valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                rubro1 = Rubro(tipo=tiporubromatricula,
                               persona=persona,
                               relacionados=None,
                               matricula=self,
                               # contratorecaudacion = None,
                               nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                               cuota=1,
                               fecha=datetime.now().date(),
                               fechavence=datetime.now().date() + timedelta(days=1),
                               valor=valor,
                               iva_id=1,
                               valoriva=0,
                               valortotal=valor,
                               saldo=valor,
                               cancelado=False)
                rubro1.save(request)
        else:
            if self.tipomatricula.id == 1:
                self.estado_matricula = 2
                self.save(request)
                # else:
                #     valor = Decimal((valor_maximo * PORCENTAJE_MULTA) / 100).quantize(Decimal('.01'))
                #     rubro1 = Rubro(tipo=tiporubromatricula,
                #                    persona=persona,
                #                    relacionados=None,
                #                    matricula=self,
                #                    # contratorecaudacion = None,
                #                    nombre=tiporubromatricula.nombre + ' - ' + periodo.nombre,
                #                    cuota=1,
                #                    fecha=datetime.now().date(),
                #                    fechavence=datetime.now().date() + timedelta(days=1),
                #                    valor=valor,
                #                    iva_id=1,
                #                    valoriva=0,
                #                    valortotal=valor,
                #                    saldo=valor,
                #                    cancelado=False)
                #     rubro1.save(request)
                #     # costo de matricula carlos loyola 03-03-2017

    def calcular_rubros_matricula(self, request, cobro):
        # esto valida para que no le genere rubros a los de POSTGRADO
        if not Periodo.objects.filter(id=self.nivel.periodo.id, tipo__id__in=[1, 3]).exists():
            self.calculos_finanzas(request, cobro)
        else:
            self.estado_matricula = 2
            self.save()

    # def agregacion(self,request, materiaasignada):
    #     if self.inscripcion.coordinacion_id <> 9 and self.inscripcion.coordinacion_id <> 7:
    #         cursor = connection.cursor()
    #         sql = "select am.nivelmalla_id, count(am.nivelmalla_id) as cantidad_materias_seleccionadas " \
    #               " from sga_materiaasignada ma, sga_materia m, sga_asignaturamalla am where ma.status=true and ma.matricula_id=" + str(self.id) + " and m.status=true and m.id=ma.materia_id and am.status=true and am.id=m.asignaturamalla_id GROUP by am.nivelmalla_id, am.malla_id order by count(am.nivelmalla_id) desc, am.nivelmalla_id desc limit 1;"
    #         cursor.execute(sql)
    #         results = cursor.fetchall()
    #         nivel = 0
    #         for per in results:
    #             nivel = per[0]
    #             cantidad_seleccionadas = per[1]
    #         cantidad_nivel = 0
    #
    #         asignaturamalla1 = self.inscripcion.mi_malla().asignaturamalla_set.filter(status=True)
    #
    #         if RecordAcademico.objects.filter(aprobada=False, inscripcion=self.inscripcion, asignaturamalla_id__in=asignaturamalla1).exists():
    #             for asignaturamalla in AsignaturaMalla.objects.filter(nivelmalla__id=nivel, status=True, malla=self.inscripcion.mi_malla()):
    #                 if Materia.objects.filter(nivel__periodo=self.nivel.periodo, asignaturamalla=asignaturamalla).exists():
    #                     cantidad_nivel += 1
    #         else:
    #             for asignaturamalla in AsignaturaMalla.objects.filter(nivelmalla__id=nivel, status=True, malla=self.inscripcion.mi_malla()):
    #                 if Materia.objects.filter(nivel__periodo=self.nivel.periodo, asignaturamalla=asignaturamalla).exists():
    #                     if self.inscripcion.puede_tomar_materia(asignaturamalla.asignatura):
    #                         if self.inscripcion.estado_asignatura(asignaturamalla.asignatura) != 1:
    #                             cantidad_nivel += 1
    #         porcentaje_seleccionadas = int(round(Decimal((float(cantidad_nivel) * float(PORCIENTO_PERDIDA_PARCIAL_GRATUIDAD)) / 100).quantize(Decimal('.00')),0))
    #         cobro = 0
    #         if self.inscripcion.estado_gratuidad == 1 or self.inscripcion.estado_gratuidad == 2:
    #             if (cantidad_seleccionadas < porcentaje_seleccionadas):
    #                 cobro = 1
    #             else:
    #                 # if self.inscripcion.estado_gratuidad == 2:
    #                 cobro = 2
    #         else:
    #             if self.inscripcion.estado_gratuidad == 2:
    #                 cobro = 2
    #             else:
    #                 cobro = 3
    #
    #         if self.inscripcion.persona.tiene_otro_titulo():
    #             cobro = 3
    #
    #         if self.tiene_pagos_matricula():
    #             # cuando tiene pagos de los rubros de la matricula, se le generara un rubro aparta por el valor de la matricula, y el valor adicional de los 10$ pero que no se pase de los 10$
    #             self.elimina_rubro_matricula_adicional()
    #             self.calculos_finanzas_adicional(request, materiaasignada,cobro)
    #         else:
    #             self.elimina_rubro_matricula()
    #             self.calculos_finanzas(request, cobro)
    #     self.actualiza_matricula()

    def agregacion_aux(self, request):
        if self.inscripcion.coordinacion_id != 9 and self.inscripcion.coordinacion_id != 7:
            cursor = connection.cursor()
            sql = "select am.nivelmalla_id, count(am.nivelmalla_id) as cantidad_materias_seleccionadas " \
                  " from sga_materiaasignada ma, sga_materia m, sga_asignaturamalla am where ma.status=true and ma.matricula_id=" + str(
                self.id) + " and m.status=true and m.id=ma.materia_id and am.status=true and am.id=m.asignaturamalla_id GROUP by am.nivelmalla_id, am.malla_id order by count(am.nivelmalla_id) desc, am.nivelmalla_id desc limit 1;"
            cursor.execute(sql)
            results = cursor.fetchall()
            nivel = 0
            for per in results:
                nivel = per[0]
                cantidad_seleccionadas = per[1]
            cantidad_nivel = 0

            # asignaturamalla1 = self.inscripcion.mi_malla().asignaturamalla_set.filter(status=True)

            # if RecordAcademico.objects.filter(aprobada=False, inscripcion=self.inscripcion, asignaturamalla_id__in = asignaturamalla1).exists():
            #     for asignaturamalla in AsignaturaMalla.objects.filter(nivelmalla__id=nivel, status=True, malla=self.inscripcion.mi_malla()):
            #         if Materia.objects.filter(nivel__periodo=self.nivel.periodo, asignaturamalla=asignaturamalla).exists():
            #             cantidad_nivel += 1
            # else:
            #     for asignaturamalla in AsignaturaMalla.objects.filter(nivelmalla__id=nivel, status=True, malla=self.inscripcion.mi_malla()):
            #         if Materia.objects.filter(nivel__periodo=self.nivel.periodo, asignaturamalla=asignaturamalla).exists():
            #             if self.inscripcion.puede_tomar_materia(asignaturamalla.asignatura):
            #                 if self.inscripcion.estado_asignatura(asignaturamalla.asignatura) != 1:
            #                     cantidad_nivel += 1

            for asignaturamalla in AsignaturaMalla.objects.filter(nivelmalla__id=nivel, status=True,
                                                                  malla=self.inscripcion.mi_malla()):
                if Materia.objects.filter(nivel__periodo=self.nivel.periodo, asignaturamalla=asignaturamalla).exists():
                    if self.inscripcion.estado_asignatura(asignaturamalla.asignatura) != 1:
                        cantidad_nivel += 1

            porcentaje_seleccionadas = int(round(
                Decimal((float(cantidad_nivel) * float(PORCIENTO_PERDIDA_PARCIAL_GRATUIDAD)) / 100).quantize(
                    Decimal('.00')), 0))
            cobro = 0
            if self.inscripcion.estado_gratuidad == 1 or self.inscripcion.estado_gratuidad == 2:
                if (cantidad_seleccionadas < porcentaje_seleccionadas):
                    cobro = 1
                else:
                    # if self.inscripcion.estado_gratuidad == 2:
                    cobro = 2
            else:
                if self.inscripcion.estado_gratuidad == 2:
                    cobro = 2
                else:
                    cobro = 3

            if self.inscripcion.persona.tiene_otro_titulo():
                cobro = 3

            if self.tiene_pagos_matricula():
                # cuando tiene pagos de los rubros de la matricula, se le generara un rubro aparta por el valor de la matricula, y el valor adicional de los 10$ pero que no se pase de los 10$
                self.elimina_rubro_matricula_adicional()
                self.calculos_finanzas_adicional_aux(request, cobro)
            else:
                self.elimina_rubro_matricula()
                self.calculos_finanzas(request, cobro)
                # self.actualiza_matricula()

    def elimina_rubro_matricula(self):
        from sagest.models import Rubro
        Rubro.objects.filter(matricula=self).delete()

    def elimina_rubro_matricula_adicional(self):
        from sagest.models import Rubro, Pago
        Rubro.objects.filter(matricula=self).update(relacionados=None)
        for r in Rubro.objects.filter(matricula=self, relacionados__isnull=True):
            if not Pago.objects.filter(rubro=r).exists():
                r.delete()

    def actualizabecario(self):
        if not self.inscripcion.inscripcionbecario_set.exists():
            becario = InscripcionBecario(inscripcion=self.inscripcion,
                                         tipobeca=self.tipobeca,
                                         porciento=self.porcientobeca,
                                         motivo=self.observaciones,
                                         fecha=self.nivel.inicio)
            becario.save()

    def eliminar_materia(self, materiaasignada, request):
        registro = AgregacionEliminacionMaterias(matricula=self,
                                                 agregacion=False,
                                                 asignatura=materiaasignada.materia.asignatura,
                                                 responsable=request.session['persona'],
                                                 fecha=datetime.now().date(),
                                                 creditos=materiaasignada.materia.creditos,
                                                 nivelmalla=materiaasignada.materia.nivel.nivelmalla if materiaasignada.materia.nivel.nivelmalla else None,
                                                 matriculas=materiaasignada.matriculas)
        registro.save()
        materiaasignada.delete()
        self.save()

    def costo_materia(self, materiaasignada):
        return 0

    def actualizar_horas_creditos(self):
        if self.materiaasignada_set.exists():
            self.promedioasistencias = round(
                null_to_numeric(self.materiaasignada_set.aggregate(prom=Avg('asistenciafinal'))['prom']), 0)
            self.promedionotas = round(
                null_to_numeric(self.materiaasignada_set.aggregate(prom=Avg('notafinal'))['prom']), 2)
            self.totalhoras = round(
                null_to_numeric(self.materiaasignada_set.aggregate(horas=Sum('materia__horas'))['horas']), 0)
            self.totalcreditos = round(null_to_numeric(
                self.materiaasignada_set.aggregate(creditos=Sum('materia__asignaturamalla__creditos'))['creditos']), 2)
        else:
            self.promedioasistencias = 0
            self.promedionotas = 0
            self.totalhoras = 0
            self.totalcreditos = 0
        self.save()

    def verificar_matricula_materia(self):
        from sagest.models import Rubro
        if not self.materiaasignada_set.exists():
            rubro = Rubro.objects.filter(matricula=self, status=True)
            if rubro:
                if not rubro[0].tiene_pagos():
                    self.delete()
                    return True
        return False

    def cantidad_evaluacionestudiantes_realizada_periodo(self, periodo):
        return RespuestaEvaluacion.objects.values("id").filter(instrumento__matriz__proceso__periodo=periodo,
                                                               instrumento__tipo__id=SUBTIPO_COMPONENTE_HETEROEVALUACION_ID,
                                                               evaluador=self.inscripcion.persona).distinct().count()

    def cantidad_evaluacionestudiantes_total_periodo(self, periodo):
        return ProfesorMateria.objects.values("id").filter(
            materia__detalleinstrumentoevaluacionintegral__instrumento__matriz__proceso__periodo=periodo,
            materia__detalleinstrumentoevaluacionintegral__instrumento__tipo__id=SUBTIPO_COMPONENTE_HETEROEVALUACION_ID,
            materia__id__in=[x.materia.id for x in self.materiaasignada_set.filter(materiaasignadaretiro__isnull=True)],
            principal=True).distinct().count()

    def promedio_nota(self):
        return null_to_numeric(
            self.materiaasignada_set.exclude(materiaasignadaretiro__valida=False).aggregate(prom=Avg('notafinal'))[
                'prom'])

    def promedio_nota_sin_modulo(self):
        return null_to_numeric(self.materiaasignada_set.exclude(materiaasignadaretiro__valida=False).exclude(
            materia__asignatura__modulo=True).aggregate(prom=Avg('notafinal'))['prom'])

    def promedio_asistencias(self):
        return null_to_numeric(self.materiaasignada_set.exclude(materiaasignadaretiro__valida=False).aggregate(
            prom=Avg('asistenciafinal'))['prom'])

    def promedio_asistencias_sin_modulo(self):
        return null_to_numeric(self.materiaasignada_set.exclude(materiaasignadaretiro__valida=False).exclude(
            materia__asignatura__modulo=True).aggregate(prom=Avg('asistenciafinal'))['prom'])

    def cantidad_evaluacionestudiantes_total_acreditacion(self):
        listadoc = []
        docentesdirectores = ActividadDetalleDistributivoCarrera.objects.values_list(
            'actividaddetalle__criterio__distributivo__profesor_id', flat=True).filter(
            actividaddetalle__criterio__distributivo__periodo=self.nivel.periodo,
            actividaddetalle__criterio__criteriogestionperiodo__isnull=False,
            actividaddetalle__criterio__hetero=True,
            actividaddetalle__criterio__status=True,
            carrera=self.inscripcion.carrera,
            status=True).distinct()
        for listadirectores in docentesdirectores:
            profe = Profesor.objects.get(pk=listadirectores)
            if profe.mis_rubricas_heterodirectivos(self.nivel.periodo.id):
                listadoc.append(profe.id)
        # return ProfesorMateria.objects.filter(tipoprofesor__id=TIPO_DOCENTE_TEORIA, materia__materiaasignada__matricula=self, materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().count() + ProfesorMateria.objects.filter(tipoprofesor__id=TIPO_DOCENTE_PRACTICA, alumnospracticamateria__materiaasignada__matricula=self, materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().count() + len(listadoc)
        return ProfesorMateria.objects.values("id").filter(tipoprofesor__id__in=[1, 5, 6],
                                                           materia__materiaasignada__matricula=self,
                                                           materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().count() + ProfesorMateria.objects.values(
            "id").filter(tipoprofesor__id=TIPO_DOCENTE_PRACTICA,
                         alumnospracticamateria__materiaasignada__matricula=self,
                         materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().count() + len(
            listadoc)

    def cantidad_evaluacionestudiantes_realizada_acreditacion(self, periodo):
        # total = 0
        # profemateria = ProfesorMateria.objects.filter(materia_id__in=RespuestaEvaluacionAcreditacion.objects.values_list('materia_id').filter(proceso__periodo=periodo, tipoinstrumento=1, evaluador=self.inscripcion.persona,materiaasignada__materiaasignadaretiro__isnull=True))
        return RespuestaEvaluacionAcreditacion.objects.values("id").filter(proceso__periodo=periodo, tipoinstrumento=1,
                                                                           evaluador=self.inscripcion.persona).count()
        # lista = RespuestaEvaluacionAcreditacion.objects.filter(proceso__periodo=periodo, tipoinstrumento=1, evaluador=self.inscripcion.persona,materiaasignada__materiaasignadaretiro__isnull=True)
        # for listados in lista:
        #     if ProfesorMateria.objects.filter(profesor=listados.profesor,materia=listados.materia,tipoprofesor_id__in=[1,2,5,6]):
        #         total = total + 1
        # return total + lista.filter(materia__isnull=True).count()
        # return total + lista.filter(materia__isnull=True).count()

    def materias_evaluacionestudiantes_no_realizada_acreditacion(self):
        periodo = self.nivel.periodo
        carrera = self.inscripcion.carrera
        # return self.materiaasignada_set.exclude(respuestaevaluacionacreditacion__isnull=False, respuestaevaluacionacreditacion__proceso__periodo=periodo, respuestaevaluacionacreditacion__tipoinstrumento=1).distinct()
        return self.materiaasignada_set.exclude(respuestaevaluacionacreditacion__isnull=False,
                                                respuestaevaluacionacreditacion__proceso__periodo=periodo,
                                                respuestaevaluacionacreditacion__tipoinstrumento=1,
                                                matricula__inscripcion__carrera=carrera).distinct()

    def cantidad_evaluacionestudiantes_restantes_acreditacion(self):
        periodo = self.nivel.periodo
        return self.cantidad_evaluacionestudiantes_total_acreditacion() - self.cantidad_evaluacionestudiantes_realizada_acreditacion(
            periodo)

    def mis_profesores_acreditacion(self):
        # return ProfesorMateria.objects.filter(Q(tipoprofesor__id=TIPO_DOCENTE_TEORIA, materia__materiaasignada__matricula=self) | Q(tipoprofesor__id=TIPO_DOCENTE_AYUDANTIA, materia__materiaasignada__matricula=self) | Q(tipoprofesor__id=TIPO_DOCENTE_PRACTICA, alumnospracticamateria__materiaasignada__matricula=self), materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().order_by('-tipoprofesor', 'profesor')
        return ProfesorMateria.objects.filter(
            Q(tipoprofesor__id=TIPO_DOCENTE_TEORIA, materia__materiaasignada__matricula=self) | Q(
                tipoprofesor__id=TIPO_DOCENTE_AYUDANTIA, materia__materiaasignada__matricula=self) | Q(
                tipoprofesor__id=6, materia__materiaasignada__matricula=self) | Q(
                tipoprofesor__id=TIPO_DOCENTE_PRACTICA, alumnospracticamateria__materiaasignada__matricula=self),
            materia__materiaasignada__materiaasignadaretiro__isnull=True).distinct().order_by('-tipoprofesor',
                                                                                              'profesor')

    def total_rubros(self):
        from sagest.models import Rubro
        valor = null_to_decimal(
            Rubro.objects.filter(matricula=self, status=True).aggregate(valor=Sum('valortotal'))['valor'], 2)
        return valor

    def total_rubrossinanular(self):
        from sagest.models import Pago, Rubro
        # rubros = Rubro.objects.values_list('id', flat=True).filter(matricula=self, status=True)
        # rubrospagos = Pago.objects.values_list('rubro_id', flat=True).filter(rubro__in=rubros, factura__valida=False)
        # valor = null_to_decimal(Rubro.objects.filter(matricula=self, status=True).exclude(pk__in=rubrospagos).aggregate(valor=Sum('valortotal'))['valor'], 2)
        valor = null_to_decimal(
            Rubro.objects.filter(matricula=self, status=True).aggregate(valor=Sum('valortotal'))['valor'],
            2) - null_to_decimal(
            Pago.objects.filter(rubro__matricula=self, rubro__status=True, factura__valida=False, status=True,
                                factura__status=True).aggregate(valor=Sum('valortotal'))['valor'], 2)
        return valor

    def total_saldo_rubro(self):
        from sagest.models import Rubro
        valor = null_to_decimal(
            Rubro.objects.filter(matricula=self, status=True).aggregate(valor=Sum('saldo'))['valor'], 2)
        return valor

    def total_saldo_rubrosinanular(self):
        from sagest.models import Pago, Rubro
        # rubros = Rubro.objects.values_list('id', flat=True).filter(matricula=self, status=True)
        # rubrospagos = Pago.objects.values_list('rubro_id', flat=True).filter(rubro__in=rubros, factura__valida=False)
        # valor = null_to_decimal(Rubro.objects.filter(matricula=self, status=True).exclude(pk__in=rubrospagos).aggregate(valor=Sum('saldo'))['valor'], 2)
        valor = null_to_decimal(
            Rubro.objects.filter(matricula=self, status=True).aggregate(valor=Sum('saldo'))['valor'], 2)
        return valor

    def total_pagado_rubro(self):
        valor = null_to_decimal((self.total_rubros() - self.total_saldo_rubro()), 2)
        return valor

    def total_pagado_rubrosinanular(self):
        valor = null_to_decimal((self.total_rubrossinanular() - self.total_saldo_rubrosinanular()), 2)
        return valor

    def vencido_a_la_fechamatricula(self):
        from sagest.models import Pago, Rubro
        rubros = Rubro.objects.filter(matricula=self, cancelado=False, fechavence__lt=datetime.now().date(),
                                      status=True).distinct()
        valor_rubros = null_to_numeric(rubros.aggregate(valor=Sum('valortotal'))['valor'])
        valor_pagos = null_to_numeric(
            Pago.objects.filter(rubro__in=rubros, status=True).distinct().aggregate(valor=Sum('valortotal'))['valor'])
        return valor_rubros - valor_pagos

    def tiene_pagos_matricula(self):
        from sagest.models import Pago
        return Pago.objects.filter(rubro__matricula=self, status=True).exists()

    def total_vencidos(self):
        from sagest.models import Rubro
        valor = null_to_decimal(
            Rubro.objects.filter(matricula=self, fechavence__lt=datetime.now().date(), cancelado=False,
                                 status=True).aggregate(valor=Sum('valortotal'))['valor'], 2)
        return valor

    def grupo_socio_economico(self, tipo_id):
        if self.matriculagruposocioeconomico_set.exists():
            gruposocioecnomico = self.matriculagruposocioeconomico_set.all()[0]
            gruposocioecnomico.tipomatricula = tipo_id
            gruposocioecnomico.puntajetotal = self.inscripcion.persona.fichasocioeconomicainec_set.all()[0].puntajetotal
            gruposocioecnomico.estado_gratuidad = self.inscripcion.estado_gratuidad
            gruposocioecnomico.save()

        else:
            if not self.inscripcion.persona.fichasocioeconomicainec_set.all().exists():
                self.inscripcion.persona.mi_ficha()
            gruposocioecnomico = MatriculaGrupoSocioEconomico(matricula=self,
                                                              gruposocioeconomico=
                                                              self.inscripcion.persona.fichasocioeconomicainec_set.all()[
                                                                  0].grupoeconomico,
                                                              tipomatricula=tipo_id,
                                                              puntajetotal=
                                                              self.inscripcion.persona.fichasocioeconomicainec_set.all()[
                                                                  0].puntajetotal,
                                                              estado_gratuidad=self.inscripcion.estado_gratuidad)
            gruposocioecnomico.save()
        return gruposocioecnomico

    def estadogratuidad(self):
        if self.matriculagruposocioeconomico_set.filter(status=True).exists():
            return ESTADO_GRATUIDAD[self.matriculagruposocioeconomico_set.filter(status=True)[0].estado_gratuidad - 1][
                1]
        return "NINGUNO"

    def matriculagruposocioeconomico(self):
        if self.matriculagruposocioeconomico_set.filter(status=True).exists():
            return self.matriculagruposocioeconomico_set.filter(status=True)[0].gruposocioeconomico
        return None

    def tienenovedades(self):
        return self.matriculanovedad_set.filter(status=True).exists()

    def novedadesmatricula(self):
        return self.matriculanovedad_set.filter(status=True)

    def calcula_nivel(self):
        cursor = connection.cursor()
        sql = "select am.nivelmalla_id, count(am.nivelmalla_id) as cantidad_materias_seleccionadas " \
              " from sga_materiaasignada ma, sga_materia m, sga_asignaturamalla am " \
              " where ma.status=true and ma.matricula_id=" + str(
            self.id) + " and m.status=true and m.id=ma.materia_id and am.status=true " \
                       " and am.id=m.asignaturamalla_id GROUP by am.nivelmalla_id, am.malla_id order by count(am.nivelmalla_id) desc, am.nivelmalla_id desc limit 1"
        cursor.execute(sql)
        results = cursor.fetchall()
        nivel = 1
        for per in results:
            nivel = per[0]
        self.nivelmalla_id = nivel
        self.save()

    def carrera_es_admision(self):
        return Coordinacion.objects.filter(pk=9, carrera=self.inscripcion.carrera).exists()

    def save(self, *args, **kwargs):
        self.observaciones = self.observaciones.upper().strip()
        if not self.id:
            self.nivelmalla = self.inscripcion.mi_nivel().nivel
        # if self.tipomatricula:
        #     if self.tipomatricula.id>1:
        #         if self.fecha <= self.nivel.fechatopematricula:
        #             self.tipomatricula_id = MATRICULA_REGULAR_ID
        #         elif self.nivel.fechatopematricula < self.fecha <= self.nivel.fechatopematriculaex:
        #             self.tipomatricula_id = MATRICULA_EXTRAORDINARIA_ID
        #         elif self.nivel.fechatopematriculaex < self.fecha <= self.nivel.fechatopematriculaes:
        #             self.tipomatricula_id = MATRICULA_ESPECIAL_ID
        #         else:
        #             self.tipomatricula_id = MATRICULA_OTRAS_ID
        # else:
        #     if self.fecha <= self.nivel.fechatopematricula:
        #         self.tipomatricula_id = MATRICULA_REGULAR_ID
        #     elif self.nivel.fechatopematricula < self.fecha <= self.nivel.fechatopematriculaex:
        #         self.tipomatricula_id = MATRICULA_EXTRAORDINARIA_ID
        #     elif self.nivel.fechatopematriculaex < self.fecha <= self.nivel.fechatopematriculaes:
        #         self.tipomatricula_id = MATRICULA_ESPECIAL_ID
        #     else:
        #         self.tipomatricula_id = MATRICULA_OTRAS_ID
        if not self.tipomatricula:
            if self.fecha <= self.nivel.fechatopematricula:
                tipomatricula = TipoMatricula.objects.get(pk=MATRICULA_REGULAR_ID)
            elif self.nivel.fechatopematricula < self.fecha <= self.nivel.fechatopematriculaex:
                tipomatricula = TipoMatricula.objects.get(pk=MATRICULA_EXTRAORDINARIA_ID)
            elif self.nivel.fechatopematriculaex < self.fecha <= self.nivel.fechatopematriculaes:
                tipomatricula = TipoMatricula.objects.get(pk=MATRICULA_ESPECIAL_ID)
            else:
                tipomatricula = TipoMatricula.objects.get(pk=MATRICULA_OTRAS_ID)
            self.tipomatricula = tipomatricula
        # self.inscripcion.actualiza_estado_matricula()
        super(Matricula, self).save(*args, **kwargs)
        # self.grupo_socio_economico(self.tipomatricula_id)


class Pension(ModeloBase):
    fecha = models.DateField(verbose_name='Fecha pension')
    valor = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor')
    cancelado = models.BooleanField(default=False, verbose_name='Cancelado')
    fecha_pago = models.DateField(verbose_name='Fecha de pago')
    matricula = models.ForeignKey(Matricula, verbose_name=u"Matricula", on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return '{}{}{}'.format(self.fecha, self.valor, self.cancelado)

    class Meta:
        verbose_name = u"Pension"
        verbose_name_plural = u"Pensiones"



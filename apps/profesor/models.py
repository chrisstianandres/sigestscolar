from datetime import datetime

from django.db import models

from apps.extras import ModeloBase
from apps.persona.models import Persona


class Profesor(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.PROTECT)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    contrato = models.CharField(default='', max_length=50, null=True, blank=True, verbose_name=u"Contrato")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Profesor"
        verbose_name_plural = u"Profesores"
        ordering = ['persona']
        unique_together = ('persona',)

    def habilitado_ingreso_calificaciones(self):
        if variable_valor('UTILIZA_VALIDACION_CALIFICACIONES'):
            datos = self.datos_habilitacion()
            if datos.habilitado and datos.fecha == datetime.now().date():
                return True
            return False
        return True

    def generar_clave_notas(self):
        clave = ''
        for i in range(4):
            clave += random.choice('0123456789ABCDEF')
        return clave

    def cantidad_materias(self, periodo):
        return ProfesorMateria.objects.values("id").filter(profesor=self, materia__nivel__periodo=periodo, activo=True, principal=True).count()

    def cantidad_materiastodas(self, periodo):
        return ProfesorMateria.objects.values("id").filter(profesor=self, materia__nivel__periodo=periodo, activo=True).count()

    def mis_materias(self, periodo):
        return ProfesorMateria.objects.filter(profesor=self, materia__nivel__periodo=periodo, activo=True, principal=True)

    def mis_materiastodas(self, periodo):
        return ProfesorMateria.objects.filter(profesor=self, materia__nivel__periodo=periodo, activo=True)

    def materias_imparte_activas(self):
        return Materia.objects.filter(cerrado=False, profesormateria__profesor=self,
                                      profesormateria__principal=True).distinct()

    def materias_imparte_periodo(self, periodo):
        # return Materia.objects.filter(nivel__periodo=periodo, profesormateria__profesor=self, profesormateria__principal=True).distinct()
        return Materia.objects.filter(nivel__periodo=periodo, profesormateria__tipoprofesor__in=[1, 2, 5],
                                      profesormateria__profesor=self).distinct()

    def materias_imparte_periodo_aux(self, periodo, tipoprofesor):
        # return Materia.objects.filter(nivel__periodo=periodo, profesormateria__profesor=self, profesormateria__principal=True).distinct()
        return Materia.objects.filter(nivel__periodo=periodo, profesormateria__tipoprofesor__in=[1, 2, 5],
                                      profesormateria__tipoprofesor=tipoprofesor,
                                      profesormateria__profesor=self).distinct()

    def asignaturas_imparte_periodo(self, periodo):
        return Asignatura.objects.filter(materia__nivel__periodo=periodo, materia__profesormateria__profesor=self,
                                         materia__profesormateria__principal=True).distinct()

    def cursos_imparte(self, periodo):
        return self.materiaasignada_set.filter(status=True, materia__curso__periodo_id=periodo).distinct('paralelo')

    def cursos_imparte_total(self, periodo):
        return self.materiaasignada_set.filter(status=True, materia__curso__periodo_id=periodo)

    def materias_imparte(self, curso, paralelo):
        return self.materiaasignada_set.filter(status=True, materia__curso__curso_id=curso, paralelo_id=paralelo).distinct('materia')

    def materias_imparte_total(self, periodo):
        return self.materiaasignada_set.filter(status=True, materia__curso__periodo=periodo).distinct('materia').count()


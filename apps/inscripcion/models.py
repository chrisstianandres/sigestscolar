from django.db import models

from apps.alumno.models import Alumno
from apps.curso.models import CursoParalelo
from apps.extras import ModeloBase
from apps.persona.models import Persona


class Inscripcion(ModeloBase):
    alumno = models.ForeignKey(Alumno, verbose_name=u'Persona', on_delete=models.PROTECT)
    curso = models.ForeignKey(CursoParalelo, verbose_name=u'Curso', on_delete=models.PROTECT)
    fecha = models.DateField(verbose_name=u'Fecha de inscripción')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.alumno

    class Meta:
        verbose_name = u"Inscripción de alumno"
        verbose_name_plural = u"Inscripciones de alumnos"
        ordering = ["alumno", '-fecha', 'curso']
        unique_together = ('alumno', 'curso')

    def perfil_usuario(self):
        return self.perfilusuario_set.all()[0]

    def adeuda_a_la_fecha(self):
        return sum([x.adeudado() for x in self.alumno.persona.rubro_set.filter(cancelado=False, status=True) if x.vencido()])


    def matriculado(self):
        return self.matricula_set.filter(cerrada=False).exists()

    def matriculado_periodo(self, periodo):
        return self.matricula_set.filter(nivel__periodo=periodo).exists()

    def becado_periodo(self, periodo):
        return self.matricula_set.filter(nivel__periodo=periodo, becado=True).exists()

    def matricula(self):
        if self.matriculado():
            return self.matricula_set.filter(cerrada=False)[0]
        return None

    def save(self, *args, **kwargs):
        self.colegio = self.colegio.upper().strip()
        self.identificador = self.identificador.upper().strip()
        self.coordinacion = self.mi_coordinacion()
        super(Inscripcion, self).save(*args, **kwargs)


# class CursoInscripcion(ModeloBase):
#     curso = models.ForeignKey(CursoParalelo, on_delete=models.PROTECT)
#     alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT)

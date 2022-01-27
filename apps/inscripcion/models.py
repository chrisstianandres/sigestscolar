from datetime import datetime

from django.db import models

from apps.alumno.models import Alumno
from apps.curso.models import CursoParalelo
from apps.extras import ModeloBase, PrimaryKeyEncryptor
from apps.paralelo.models import Paralelo
from apps.persona.models import Persona
from sigestscolar.settings import SECRET_KEY_ENCRIPT


class Inscripcion(ModeloBase):
    alumno = models.ForeignKey(Alumno, verbose_name=u'Persona', on_delete=models.PROTECT)
    curso = models.ForeignKey(CursoParalelo, verbose_name=u'Curso', on_delete=models.PROTECT)
    paralelo = models.ForeignKey(Paralelo, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField(verbose_name=u'Fecha de inscripción')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.alumno

    class Meta:
        verbose_name = u"Inscripción de alumno"
        verbose_name_plural = u"Inscripciones de alumnos"
        ordering = ["alumno", '-fecha', 'curso']
        unique_together = ('alumno', 'curso')

    def encoded_id(self):
        return PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).encrypt(self.id)

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

    def notas_generales(self, materiaasignada):
        notas = []
        promedio1 = 0.00
        promedio2 = 0.00
        for a in materiaasignada.cursoquimestre_set.filter(status=True).distinct('parcial'):
            if a.notasalumno_set.filter(status=True, alumno=self).exists():
                notas.append(float(a.notasalumno_set.filter(status=True, alumno=self).first().nota))
                promedio1 += float(a.notasalumno_set.filter(status=True, alumno=self).first().nota)
                if a.parcial.nombre == 'Examen':
                    promedio1 = float(promedio1) / (float(materiaasignada.modelo_eval_parcial_total())*float(materiaasignada.modelo_eval_quimestres().count()))
                    promedio2 += promedio1
                    notas.append(round(promedio1, 2))
            else:
                notas.append(float(0.00))
                promedio1 += 0.00
                if a.parcial.nombre == 'Examen':
                    promedio1 = float(promedio1) / (float(materiaasignada.modelo_eval_parcial_total())*float(materiaasignada.modelo_eval_quimestres().count()))
                    promedio2 += promedio1
                    notas.append(round(promedio1, 2))
        notas.append(round(promedio2/float(materiaasignada.modelo_eval_quimestres().count()), 2))
        return notas

    def save(self, *args, **kwargs):
        self.fecha = datetime.now()
        super(Inscripcion, self).save(*args, **kwargs)


# class CursoInscripcion(ModeloBase):
#     curso = models.ForeignKey(CursoParalelo, on_delete=models.PROTECT)
#     alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT)

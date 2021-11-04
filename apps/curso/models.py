from django.db import models

from apps.extras import ModeloBase
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo


class Curso(ModeloBase):
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripcion del curso')

    def __str__(self):
        return '{}'.format(self.nombre)

    class Meta:
        verbose_name = u"Curso"
        verbose_name_plural = u"Cursos"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super(Curso, self).save(*args, **kwargs)


class CursoParalelo(ModeloBase):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    paralelo = models.ForeignKey(Paralelo, on_delete=models.PROTECT)
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.PROTECT)


class CursoMateria(ModeloBase):
    curso = models.ForeignKey(CursoParalelo, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)


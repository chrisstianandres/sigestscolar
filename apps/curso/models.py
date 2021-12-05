from django.db import models
from django.forms import model_to_dict

from apps.extras import ModeloBase, PrimaryKeyEncryptor
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from sigestscolar.settings import SECRET_KEY_ENCRIPT


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

    def to_JSON(self):
        item = model_to_dict(self)
        return item

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super(Curso, self).save(*args, **kwargs)


class CursoParalelo(ModeloBase):
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT)
    paralelo = models.ManyToManyField(Paralelo)
    periodo = models.ForeignKey(PeriodoLectivo, on_delete=models.PROTECT)
    cupo = models.IntegerField(default=5)
    cupoindividual = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {}  {}'.format(self.periodo.nombre, self.curso.nombre, self.paralelo.nombre)

    def to_JSON(self):
        item = model_to_dict(self)
        item['curso'] = self.curso.to_JSON()
        return item

    def tiene_inscripciones(self):
        return self.inscripcion_set.all().exists()

    def total_inscritos(self):
        return self.inscripcion_set.all().count()

    def total_materias(self):
        return self.cursomateria_set.all().count()

    def encoded_id(self):
        return PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).encrypt(self.id)

    def cupos_disponible(self):
        return self.total_inscritos() < self.cupo_total()

    def configuracion_valores(self):
        if self.configuracionvalorescurso_set.exists():
            return self.configuracionvalorescurso_set.first()
        return False

    def cupo_total(self):
        if self.cupoindividual:
            return self.cupo * self.paralelo.all().count()
        return self.cupo

    def cupo_individual(self):
        if self.cupoindividual:
            return self.cupo

    def cupo_disponible_por_paralelo(self, paralelo):
        if self.cupoindividual:
            return self.cupo_individual() > self.inscripcion_set.filter(paralelo_id=paralelo).count()


    class Meta:
        verbose_name = u"Curso Paralelo"
        verbose_name_plural = u"Cursos Paralelos"
        ordering = ['periodo']


class CursoMateria(ModeloBase):
    curso = models.ForeignKey(CursoParalelo, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)

    def __str__(self):
        return '{} - {} '.format(self.curso.curso.nombre, self.materia.nombre)

    def to_JSON(self):
        item = model_to_dict(self)
        item['curso'] = self.curso.to_JSON()
        item['materia'] = model_to_dict(self.materia)
        return item

    class Meta:
        verbose_name = u"Curso Materia"
        verbose_name_plural = u"Cursos Materias"
        ordering = ['materia']


class ConfiguracionValoresCurso(ModeloBase):
    curso = models.ForeignKey(CursoParalelo, on_delete=models.PROTECT)
    matricula = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pension = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    numeropensiones = models.IntegerField(default=1)


class ConfiguracionValoresGeneral(ModeloBase):
    matricula = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pension = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    numeropensiones = models.IntegerField(default=1)


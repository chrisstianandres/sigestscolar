from django.db import models
from django.db.models import Avg
from django.forms import model_to_dict

from apps.extras import ModeloBase, PrimaryKeyEncryptor
from apps.materia.models import Materia
from apps.paralelo.models import Paralelo
from apps.periodo.models import PeriodoLectivo
from apps.profesor.models import Profesor
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
    quimestres = models.IntegerField(default=0, verbose_name='Numero de Quimestres')
    parciales = models.IntegerField(default=0, verbose_name='Numero de Parciales')

    def __str__(self):
        return '{} - {}'.format(self.periodo.nombre, self.curso.nombre)

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

    def materias_asignadas_curso(self, id=None):
        data = []
        keys = []
        for m in self.cursomateria_set.filter(status=True):
            if id is not None:
                if m.id == id:
                    data.append({'id': m.id, 'materia': m.materia.nombre, 'select': 'true'})
                else:
                    data.append({'id': m.id, 'materia': m.materia.nombre, 'select': 'false'})
            # elif m == self.cursomateria_set.filter(status=True)[0]:
            #     data.append({'id': m.id, 'materia': m.materia.nombre, 'select': True})
            else:
                for p in m.curso.paralelo.filter(status=True):
                    if not MateriaAsignada.objects.filter(materia=m, paralelo=p).exists():
                        if m.materia.id not in keys:
                            keys.append(m.materia.id)
                            data.append({'id': m.id, 'materia': m.materia.nombre, 'select': len(keys) == 1})
        return data

    def get_paralelos(self, id=None):
        data = []
        keys = []
        for p in self.paralelo.filter(status=True):
            if id is not None:
                if p.id == id:
                    data.append({'id': p.id, 'paralelo': p.nombre, 'select': 'true'})
                else:
                    data.append({'id': p.id, 'paralelo': p.nombre, 'select': 'false'})
            # elif p == self.paralelo.filter(status=True)[0]:
            #     data.append({'id': p.id, 'paralelo': p.nombre, 'select': True})
            else:
                for c in CursoMateria.objects.filter(curso__periodo=self.periodo, curso=self):
                    if not MateriaAsignada.objects.filter(materia=c, paralelo=p).exists():
                        if p.id not in keys:
                            keys.append(p.id)
                            data.append({'id': p.id, 'paralelo': p.nombre, 'select': len(keys) == 1})
        return data

    def encoded_id(self):
        return PrimaryKeyEncryptor(SECRET_KEY_ENCRIPT).encrypt(self.id)

    def cupos_disponible(self):
        return self.total_inscritos() < self.cupo_total()

    def configuracion_valores(self):
        if self.configuracionvalorescurso_set.exists():
            return self.configuracionvalorescurso_set.first()
        return False

    def configuro_quimestres(self):
        if CursoQuimestre.objects.filter(status=True, cursoasignado__materia__curso=self).exists():
            return CursoQuimestre.objects.filter(status=True, cursoasignado__materia__curso=self).count() == (
                        self.quimestres * (self.parciales + 1)) * (
                       self.paralelo.count()) * self.cursomateria_set.count()
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

    def docentes(self):
        self.materiaasignada_set.filter(status=True)

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


class MateriaAsignada(ModeloBase):
    profesor = models.ForeignKey(Profesor, on_delete=models.PROTECT)
    materia = models.ForeignKey(CursoMateria, on_delete=models.PROTECT)
    paralelo = models.ForeignKey(Paralelo, on_delete=models.PROTECT)

    def __str__(self):
        return '{} {}'.format(self.profesor.persona.nombre_completo(), self.materia.materia.nombre)

    def modelo_eval_quimestres(self):
        return self.cursoquimestre_set.filter(status=True).distinct('parcial__quimestre')

    def modelo_eval_parcial(self):
        return self.cursoquimestre_set.filter(status=True).distinct('parcial')

    def modelo_eval_parcial_total(self):
        return int(self.cursoquimestre_set.filter(status=True).distinct(
            'parcial').count() / self.modelo_eval_quimestres().count())

    def modelo_eval_parcial_totalacta(self):
        return int(self.cursoquimestre_set.filter(status=True).distinct(
            'parcial').count() / self.modelo_eval_quimestres().count()) + 1

    def puede_exportar_acta(self):
        return self.cursoquimestre_set.filter(status=True).first().tiene_notas()


class Quimestre(ModeloBase):
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre')
    numero = models.IntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.nombre)


TIPO_PARCIAL = (
    (0, 'PARCIAL'),
    (1, 'EXAMEN')
)


class ModeloParcial(ModeloBase):
    quimestre = models.ForeignKey(Quimestre, on_delete=models.PROTECT)
    nombre = models.CharField(default='', max_length=200, verbose_name=u'Nombre')
    tipo = models.IntegerField(choices=TIPO_PARCIAL, default=0, verbose_name=u'Nombre')
    numero = models.IntegerField(default=1)

    def __str__(self):
        return '{} {} {} {}'.format(self.numero, self.quimestre, self.nombre, self.get_tipo_display())


class CursoQuimestre(ModeloBase):
    cursoasignado = models.ForeignKey(MateriaAsignada, on_delete=models.PROTECT, verbose_name='Curso y Materia')
    parcial = models.ForeignKey(ModeloParcial, on_delete=models.PROTECT, verbose_name='Quimestre y Parcial', null=True,
                                blank=True)
    actacerrada = models.BooleanField(default=False)

    def __str__(self):
        return '{} {}'.format(self.cursoasignado.materia.curso, self.cursoasignado.materia)

    def tiene_notas(self):
        return self.notasalumno_set.filter(status=True).exists()

    def alumnos_notas(self):
        return self.notasalumno_set.filter(status=True)


class NotasAlumno(ModeloBase):
    curso = models.ForeignKey(CursoQuimestre, on_delete=models.PROTECT, verbose_name='Curso Quimestre parcial')
    alumno = models.ForeignKey('inscripcion.Inscripcion', on_delete=models.PROTECT,
                               verbose_name='Inscripcion de Alumno')
    nota = models.DecimalField(decimal_places=2, max_digits=5, default=0, verbose_name='Nota')

    def __str__(self):
        return '{} {}'.format(self.curso, self.alumno, self.nota)

    # def promedio_parciales(self, quimestre, materia):
    #     promedio = NotasAlumno.objects.filter(curso__parcial__quimestre=quimestre,
    #                                           curso__cursoasignado=materia, alumno=self).aggregate(promedio=Avg('nota'))
    #     return promedio

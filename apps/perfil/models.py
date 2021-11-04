from django.db import models

from apps.administrativo.models import Administrativo
from apps.externo.models import Externo
from apps.extras import ModeloBase
from apps.inscripcion.models import Inscripcion
from apps.persona.models import Persona
from apps.profesor.models import Profesor


class PerfilUsuario(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)
    administrativo = models.ForeignKey(Administrativo, blank=True, null=True, verbose_name=u'Administrativo', on_delete=models.PROTECT)
    profesor = models.ForeignKey(Profesor, blank=True, null=True, verbose_name=u'Profesor', on_delete=models.PROTECT)
    externo = models.ForeignKey(Externo, blank=True, null=True, verbose_name=u'Cliente externo', on_delete=models.PROTECT)
    inscripcion = models.ForeignKey(Inscripcion, blank=True, null=True, verbose_name=u'Inscripción', on_delete=models.PROTECT)
    inscripcionprincipal = models.BooleanField(default=False, verbose_name=u'Inscripción principal')

    def __str__(self):
        if self.es_estudiante():
            return u'%s' % "ESTUDIANTE"
        elif self.es_profesor():
            return u'%s' % "PROFESOR"
        elif self.es_administrativo():
            return u'%s' % "ADMINISTRATIVO"
        elif self.es_externo():
            return u'%s' % "EXTERNO"
        else:
            return u'%s' % "OTRO PERFIL"

    class Meta:
        ordering = ['persona', 'inscripcion', 'administrativo', 'profesor', 'externo']
        unique_together = ('persona', 'inscripcion', 'administrativo', 'profesor', 'externo')

    def es_estudiante(self):
        return null_to_numeric(self.inscripcion_id) > 0

    def establecer_estudiante_principal(self):
        if self.es_estudiante() and not self.inscripcionprincipal:
            PerfilUsuario.objects.filter(persona=self.persona, inscripcion__isnull=False).update(
                inscripcionprincipal=False)
            self.inscripcionprincipal = True
            self.save()

    def es_profesor(self):
        return null_to_numeric(self.profesor_id) > 0

    def es_administrativo(self):
        return null_to_numeric(self.administrativo_id) > 0

    def es_externo(self):
        return null_to_numeric(self.externo_id) > 0

    def activo(self):
        if self.es_estudiante():
            return self.inscripcion.activo
        elif self.es_profesor():
            return self.profesor.activo
        elif self.es_administrativo():
            return self.administrativo.activo
        return False

    def tipo(self):
        if self.es_estudiante():
            return self.inscripcion.carrera.alias
        elif self.es_administrativo():
            return "ADMINISTRATIVO"
        elif self.es_profesor():
            return "PROFESOR"
        elif self.es_externo():
            return "EXTERNO"
        else:
            return "NO DEFINIDO"

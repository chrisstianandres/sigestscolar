from datetime import datetime

from django.db import models

from sigestscolar.settings import ADMINISTRADOR_ID


class ModeloBase(models.Model):
    """ Modelo base para todos los modelos del proyecto """
    from django.contrib.auth.models import User
    status = models.BooleanField(default=True)
    usuario_creacion = models.ForeignKey(User, related_name='+', blank=True, null=True, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    usuario_modificacion = models.ForeignKey(User, related_name='+', blank=True, null=True, on_delete=models.PROTECT)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        usuario = None
        if len(args):
            usuario = args[0].user.id
        if self.id:
            self.usuario_modificacion_id = usuario if usuario else ADMINISTRADOR_ID
            self.fecha_modificacion = datetime.now()
        else:
            self.usuario_creacion_id = usuario if usuario else ADMINISTRADOR_ID
            self.fecha_creacion = datetime.now()
        models.Model.save(self)

    class Meta:
        abstract = True


def null_to_numeric(valor, decimales=None):
    if decimales:
        return round((valor if valor else 0), decimales)
    return valor if valor else 0

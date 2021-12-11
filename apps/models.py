from django.db import models

from apps.extras import ModeloBase


class Modulo(ModeloBase):
    url = models.CharField(max_length=50)
    nombre = models.CharField(max_length=50)
    icono = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return '{} {}'.format(self.nombre, self.url)

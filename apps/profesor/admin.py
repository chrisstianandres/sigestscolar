from django.contrib import admin
from .models import *
from ..curso.models import MateriaAsignada

admin.site.register(Profesor)
admin.site.register(MateriaAsignada)
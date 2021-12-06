from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.alumno.views import *

app_name = 'alumno'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='alumnos'),

]

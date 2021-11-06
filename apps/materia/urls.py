from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.materia.views import *

app_name = 'materia'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='materias'),

]

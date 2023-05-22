from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.curso.views import *

app_name = 'curso'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='cursos'),
    path('/', login_required(ListviewAperutar.as_view()), name='aperturar'),

]

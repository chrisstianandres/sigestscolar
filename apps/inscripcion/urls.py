from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.inscripcion.views import *

app_name = 'Inscripcion'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='inscripcion'),

]

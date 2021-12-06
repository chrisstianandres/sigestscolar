from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.profesor.views import *

app_name = 'docente'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='docentes'),

]

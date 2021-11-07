from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.periodo.views import *

app_name = 'periodo'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='periodos'),

]

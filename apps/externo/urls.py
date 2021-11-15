from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.externo.views import *

app_name = 'externo'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='externos'),

]

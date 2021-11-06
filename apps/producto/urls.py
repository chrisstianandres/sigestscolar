from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.producto.views import *

app_name = 'producto'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='producto'),

]

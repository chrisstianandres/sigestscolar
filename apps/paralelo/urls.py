from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.paralelo.views import *

app_name = 'paralelo'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='paralelos'),

]

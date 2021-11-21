from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.administrativo.views import *

app_name = 'administrativo'

urlpatterns = [
    path('', login_required(Listview.as_view()), name='administrativos'),

]

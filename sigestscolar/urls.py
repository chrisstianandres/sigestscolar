"""sigestscolar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include

from apps import backEnd, curso

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashborad/', login_required(backEnd.DashboardView.as_view()), name='dashborad'),
    path('change_profile/<int:pk>', login_required(backEnd.UserChangeGroup.as_view()), name='changeprofile'),
    path('cursos/', include('apps.curso.urls', namespace='cursos')),
    path('paralelos/', include('apps.paralelo.urls', namespace='paralelos')),
    path('materias/', include('apps.materia.urls', namespace='materias')),
    path('productos/', include('apps.producto.urls', namespace='productos')),
    path('periodos/', include('apps.periodo.urls', namespace='periodos')),
    path('externos/', include('apps.externo.urls', namespace='externos')),
    path('administrativos/', include('apps.administrativo.urls', namespace='administrativos')),
    path('inscripciones/', include('apps.inscripcion.urls', namespace='inscripciones')),
]

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
from django.conf.urls.static import static
from django.conf import settings

from apps import backEnd
from apps.curso.views import IngresoNotasView, PrintActaNotas
from apps.empresa.views import EmpresaView
from apps.profesor.distributivodocente import Listview
from apps.rubro.views import ListviewValores, ListviewFacturacion, PrintFactura

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('login/', backEnd.LoginFormView.as_view(), name='login'),
                  path('', backEnd.LoginFormView.as_view(), name='index'),
                  path('accounts/login', backEnd.LoginFormView.as_view(), name='login_next'),
                  path('logout/', backEnd.disconnect, name='logout'),
                  path('dashborad/', login_required(backEnd.DashboardView.as_view()), name='dashborad'),
                  path('empresa/', login_required(EmpresaView.as_view()), name='empresa'),
                  path('change_profile/<int:pk>', login_required(backEnd.UserChangeGroup.as_view()), name='changeprofile'),
                  path('cursos/', include('apps.curso.urls', namespace='cursos')),
                  path('paralelos/', include('apps.paralelo.urls', namespace='paralelos')),
                  path('materias/', include('apps.materia.urls', namespace='materias')),
                  path('productos/', include('apps.producto.urls', namespace='productos')),
                  path('periodos/', include('apps.periodo.urls', namespace='periodos')),
                  path('externos/', include('apps.externo.urls', namespace='externos')),
                  path('administrativos/', include('apps.administrativo.urls', namespace='administrativos')),
                  path('docentes/', include('apps.profesor.urls', namespace='profesor')),
                  path('alumnos/', include('apps.alumno.urls', namespace='alumnos')),
                  path('inscripciones/', include('apps.inscripcion.urls', namespace='inscripciones')),
                  path('distributivo/', login_required(Listview.as_view()), name='distributivo'),
                  path('valores', login_required(ListviewValores.as_view()), name='valores'),
                  path('facturacion', login_required(ListviewFacturacion.as_view()), name='facturacion'),
                  path('exportcomprobante/<int:pk>', login_required(PrintFactura.as_view()), name='imprimirfactura'),
                  path('notas', login_required(IngresoNotasView.as_view()), name='notas'),
                  path('generaractaindividual/<int:pk>', login_required(PrintActaNotas.as_view()), name='generaractanotas'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

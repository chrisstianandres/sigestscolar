import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from crum import get_current_request

from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count, FloatField, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib.auth import *
from django.http import HttpResponse
from django.http import *
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
import json
from django.views.decorators.csrf import csrf_exempt

# -----------------------------------------------PAGINA PRINCIPAL-----------------------------------------------------#
# from apps.user.forms import UserForm, UserForm_online, ResetPasswordForm, ChangePasswordForm
# from apps.user.models import User
from django.views.generic.base import View

from apps.curso.models import MateriaAsignada, CursoParalelo
from apps.empresa.models import Empresa
from apps.inscripcion.models import Inscripcion
from apps.models import Modulo
from apps.perfil.models import PerfilUsuario
from apps.periodo.models import PeriodoLectivo
from apps.persona.models import Persona
from apps.rubro.models import Pago, Rubro


def nombre_empresa():
    if Empresa.objects.all().exists():
        empresa = Empresa.objects.first()
    else:
        empresa = {'nombre': 'Sin nombre'}
    return empresa


def calcular_edad(fecha):
    hoy = datetime.now().date()
    try:
        nac = fecha
        if hoy.year > nac.year:
            edad = hoy.year - nac.year
            if hoy.month <= nac.month:
                if hoy.month == nac.month:
                    if hoy.day < nac.day:
                        edad -= 1
                else:
                    edad -= 1
            return edad
        else:
            raise NameError('Error')
    except Exception as ex:
        return 0

PERFIL_ACTUAL = (
    (0, 'EXTERNO'),
    (1, 'ADMINISTRATIVO'),
    (2, 'PROFESOR'),
    (3, 'ALUMNO'),
    (4, 'SUPERUSUARIO'),
)
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['anioactual'] = anio = datetime.now().year
        persona = self.request.session['persona']
        perfilactual = self.request.session['perfilactual']
        data['titulo'] = 'Menu Principal'
        data['empresa'] = nombre_empresa()
        data['icono'] = 'fas fa-tachometer-alt'
        data['entidad'] = 'Menu Principal'
        if persona.es_administrativo() and perfilactual == 'ADMINISTRATIVO' or persona.usuario.is_superuser:
            data['periodoactual'] = periodoactual = PeriodoLectivo.objects.filter(status=True, actual=True).first()
            data['recaudado'] = Pago.objects.filter(status=True, fecha__year=anio, factura__valida=True, factura__verificada=True).aggregate(recaudado=Sum('valortotal')).get('recaudado')
            data['inscritos'] = Inscripcion.objects.filter(status=True, curso__periodo=periodoactual).count()
            data['docentes'] = MateriaAsignada.objects.filter(status=True, materia__curso__periodo=periodoactual).distinct('profesor').count()
            data['cursos'] = CursoParalelo.objects.filter(status=True, periodo=periodoactual).count()
            data['personas'] = self.personas_recientes()
            # data['vencidomes'] = self.vencido_por_mes()
            # data['cabrarmes'] = self.porcobrar_por_mes()

        return data

    def personas_recientes(self):
        hoy = datetime.now()
        return Persona.objects.filter(status=True, fecha_creacion__lte=hoy-timedelta(days=30))

    # def vencido_por_mes(self):
    #     totales = []
    #     hoy = datetime.now()
    #     anio = hoy.year
    #     for m in range(1, 13):
    #         totales.append(Rubro.objects.filter(status=True, fecha__year=anio, fecha__month=m, fechavence__lt=hoy, cancelado=False).aggregate(
    #             total=Coalesce(Sum('valortotal', output_field=FloatField()), float(0))).get('total'))
    #     return totales
    #
    # def porcobrar_por_mes(self):
    #     totales = []
    #     hoy = datetime.now()
    #     anio = hoy.year
    #     for m in range(1, 13):
    #         totales.append(Rubro.objects.filter(status=True, fecha__year=anio, fecha__month=m, fechavence__gte=hoy, cancelado=False).aggregate(
    #             total=Coalesce(Sum('valortotal', output_field=FloatField()), float(0))).get('total'))
    #     return totales


def generar_usuario(persona, g):
    usuario = User(username=persona.cedula)
    usuario.set_password(persona.cedula)
    usuario.save()
    persona.usuario = usuario
    persona.save()
    return usuario


def crear_perfil_usuario(persona, administrativo=None, inscripcion=None, profesor=None):
    if inscripcion:
        perfil = PerfilUsuario(persona=persona, inscripcion=inscripcion)
        perfil.save()
    elif administrativo:
        perfil = PerfilUsuario(persona=persona, administrativo=administrativo)
        perfil.save()
    elif profesor:
        perfil = PerfilUsuario(persona=persona, profesor=profesor)
        perfil.save()


class LoginFormView(LoginView):
    template_name = 'login.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                self.get_group_session()
                self.get_persona_session()
                data['resp'] = True
            else:
                data['error'] = '<strong>Usuario Inactivo </strong>'
        else:
            data['error'] = '<strong>Usuario no valido </strong><br> Verifica las credenciales de acceso y vuelve a intentarlo.'
        return JsonResponse(data)

    def get_group_session(self):
        try:
            request = get_current_request()
            persona = request.user.persona_set.first()
            if persona is not None:
                perfiles = persona.perfilusuario_set.filter(status=True)
                if perfiles.exists():
                    keyperfil = 0
                    if 'perfiles' not in request.session:
                        request.session['perfiles'] = perfiles[0]
                    if 'perfilactualkey' not in request.session:
                        for key in range(0, 4):
                            if PERFIL_ACTUAL[key][1] == str(perfiles[0]):
                                request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[key][0]
                    if 'perfilactual' not in request.session:
                        request.session['perfilactual'] = PERFIL_ACTUAL[keyperfil][1]
                    self.get_modulos()
                elif request.user.is_superuser:
                    if 'perfilactualkey' not in request.session:
                        request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[4][0]
                    if 'perfilactual' not in request.session:
                        request.session['perfilactual'] = PERFIL_ACTUAL[4][1]
                    self.get_modulos()
            elif request.user.is_superuser:
                if 'perfilactualkey' not in request.session:
                    request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[4][0]
                if 'perfilactual' not in request.session:
                    request.session['perfilactual'] = PERFIL_ACTUAL[4][1]
                self.get_modulos()
        except Exception as e:
            pass

    def get_modulos(self):
        try:
            request = get_current_request()
            perfilactual = request.session['perfilactual']
            grupo = Group.objects.filter(name__icontains=perfilactual)
            if grupo.exists():
                modulos = grupo.first().grupomodulo_set.all()
                if modulos.exists():
                    request.session['modulos'] = modulos.first().modulos.all()
            elif request.user.is_superuser:
                request.session['modulos'] = Modulo.objects.filter(status=True).exclude(id=13).order_by('nombre')
            else:
                request.session['modulos'] = []
            if PeriodoLectivo.objects.filter(status=True, actual=True):
                request.session['periodoactual'] = PeriodoLectivo.objects.filter(status=True, actual=True).first()
        except Exception as e:
            disconnect(self.request)
            pass

    def get_persona_session(self):
        request = get_current_request()
        if not 'persona' in request.session:
            request.session['persona'] = request.user.persona_set.first()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['title'] = 'Inicio de Sesion'
        data['empresa'] = nombre_empresa()
        return data



# class ResetPasswordView(FormView):
#     form_class = ResetPasswordForm
#     template_name = 'front-end/user/forgot-password.html'
#     success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)
#
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     def send_email_reset_pwd(self, user):
#         data = {}
#         try:
#             URL = settings.DOMAIN if not settings.DEBUG else self.request.META['HTTP_HOST']
#             user.token = uuid.uuid4()
#             user.save()
#             mailServer = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
#             mailServer.starttls()
#             mailServer.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
#             email_to = user.email
#             mensaje = MIMEMultipart()
#             mensaje['From'] = settings.EMAIL_HOST_USER
#             mensaje['To'] = email_to
#             mensaje['Subject'] = 'Reseteo de contraseña'
#             empresa = nombre_empresa()
#             content = render_to_string('front-end/user/send_email.html', {
#                 'user': user,
#                 'link_resetpwd': 'http://{}/change_pass/{}/'.format(URL, str(user.token)),
#                 'empresa': empresa
#             })
#             mensaje.attach(MIMEText(content, 'html'))
#             mailServer.sendmail(settings.EMAIL_HOST_USER, email_to, mensaje.as_string())
#             data['email'] = user.email
#         except Exception as e:
#             data['error'] = str(e)
#         return data
#
#     def post(self, request, *args, **kwargs):
#         data = {}
#         try:
#             form = ResetPasswordForm(request.POST)  # self.get_form()
#             if form.is_valid():
#                 user = form.get_user()
#                 data = self.send_email_reset_pwd(user)
#             else:
#                 data['error'] = form.errors
#         except Exception as e:
#             data['error'] = str(e)
#         return JsonResponse(data, safe=False)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Reseteo de Contraseña'
#         context['nomb'] = nombre_empresa()
#         return context
#
#
# class ChangePasswordView(FormView):
#     form_class = ChangePasswordForm
#     template_name = 'front-end/user/change_password.html'
#     success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)
#
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         token = self.kwargs['token']
#         if User.objects.filter(token=token).exists():
#             return super().get(request, *args, **kwargs)
#         return HttpResponseRedirect('/')
#
#     def post(self, request, *args, **kwargs):
#         data = {}
#         try:
#             form = ChangePasswordForm(request.POST)
#             if form.is_valid():
#                 user = User.objects.get(token=self.kwargs['token'])
#                 user.set_password(request.POST['password'])
#                 user.token = uuid.uuid4()
#                 user.save()
#             else:
#                 data['error'] = form.errors
#         except Exception as e:
#             data['error'] = str(e)
#         return JsonResponse(data, safe=False)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Cambio de Contraseña'
#         context['login_url'] = settings.LOGIN_URL
#         context['nomb'] = nombre_empresa()
#         return context
#
#
# class SingUpView(FormView):
#     form_class = UserForm_online
#     template_name = 'front-end/user/singup.html'
#     success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)
#
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)
#
#     def post(self, request, *args, **kwargs):
#         data = {}
#         try:
#             form = self.form_class(request.POST)  # self.get_form()
#             if form.is_valid():
#                 form.save()
#             else:
#                 data['error'] = form.errors
#         except Exception as e:
#             data['error'] = str(e)
#         return JsonResponse(data, safe=False)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Crear una cuenta'
#         context['nomb'] = nombre_empresa()
#         return context

class UserChangeGroup(View):

    def get(self, request, *args, **kwargs):
        try:
            # request.session['group'] = Group.objects.get(pk=self.kwargs['pk'])
            request.session['perfilactual'] = PERFIL_ACTUAL[self.kwargs['pk']][1]
            request.session['perfilactualkey'] = int(self.kwargs['pk'])
            self.get_group_session()
            self.get_persona_session()
        except:
            pass
        return HttpResponseRedirect(reverse_lazy('dashborad'))

    def get_group_session(self):
        try:
            request = get_current_request()
            persona = request.user.persona_set.first()
            if persona is not None:
                perfiles = persona.perfilusuario_set.filter(status=True)
                if perfiles.exists():
                    keyperfil = 0
                    if 'perfiles' not in request.session:
                        request.session['perfiles'] = perfiles[0]
                    if 'perfilactualkey' not in request.session:
                        for key in range(0, 4):
                            if PERFIL_ACTUAL[key][1] == str(perfiles[0]):
                                request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[key][0]
                    if 'perfilactual' not in request.session:
                        request.session['perfilactual'] = PERFIL_ACTUAL[keyperfil][1]
                    self.get_modulos()
                elif request.user.is_superuser:
                    if 'perfilactualkey' not in request.session:
                        request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[4][0]
                    if 'perfilactual' not in request.session:
                        request.session['perfilactual'] = PERFIL_ACTUAL[4][1]
                    self.get_modulos()
            elif request.user.is_superuser:
                if 'perfilactualkey' not in request.session:
                    request.session['perfilactualkey'] = keyperfil = PERFIL_ACTUAL[4][0]
                if 'perfilactual' not in request.session:
                    request.session['perfilactual'] = PERFIL_ACTUAL[4][1]
                self.get_modulos()
        except Exception as e:
            pass

    def get_modulos(self):
        try:
            request = get_current_request()
            perfilactual = request.session['perfilactual']
            grupo = Group.objects.filter(name__icontains=perfilactual)
            if grupo.exists():
                modulos = grupo.first().grupomodulo_set.all()
                if modulos.exists():
                    request.session['modulos'] = modulos.first().modulos.all()
            elif request.user.is_superuser:
                request.session['modulos'] = Modulo.objects.filter(status=True).exclude(id=13).order_by('nombre')
            else:
                request.session['modulos'] = []
        except Exception as e:
            disconnect(self.request)
            pass

    def get_persona_session(self):
        request = get_current_request()
        if not 'persona' in request.session:
            request.session['persona'] = request.user.persona_set.first()


def disconnect(request):
    logout(request)
    return HttpResponseRedirect('/login')

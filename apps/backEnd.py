import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from crum import get_current_request

from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
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

from apps.empresa.models import Empresa
from apps.perfil.models import PerfilUsuario


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


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # def get(self, request, *args, **kwargs):


    def get_group_session(self):
        try:
            request = get_current_request()
            groups = self.request.user.groups.all()
            if groups.exists():
                if 'group' not in request.session:
                    request.session['group'] = groups[0]
                if 'permisos' not in request.session:
                    permisos = []
                else:
                    permisos = []
                    request.session['permisos'] = []
                for p in request.session['group'].permissions.all():
                    permisos.append(p.codename)
                request.session['permisos'] = permisos
        except Exception as e:
            pass

    def get_context_data(self, **kwargs):
        self.get_group_session()
        data = super().get_context_data(**kwargs)
        data['titulo'] = 'Menu Principal'
        data['empresa'] = nombre_empresa()
        data['icono'] = 'fas fa-tachometer-alt'
        data['entidad'] = 'Menu Principal'
        return data


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
# class LoginFormView(LoginView):
#     template_name = 'front-end/login.html'
#
#     @method_decorator(csrf_exempt)
#     def dispatch(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             return redirect(settings.LOGIN_REDIRECT_URL)
#         return super().dispatch(request, *args, **kwargs)
#
#     def post(self, request, *args, **kwargs):
#         data = {}
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(username=username, password=password)
#         if user is not None:
#             if user.estado == 1:
#                 login(request, user)
#                 data['resp'] = True
#             else:
#                 data['error'] = '<strong>Usuario Inactivo </strong>'
#         else:
#             data['error'] = '<strong>Usuario no valido </strong><br>' \
#                             'Verifica las credenciales de acceso y vuelve a intentarlo.'
#         return JsonResponse(data)
#
#     def get_context_data(self, **kwargs):
#         data = super().get_context_data(**kwargs)
#         data['title'] = 'Inicio de Sesion'
#         data['nomb'] = nombre_empresa()
#         return data


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
            request.session['group'] = Group.objects.get(pk=self.kwargs['pk'])
        except:
            pass
        return HttpResponseRedirect(reverse_lazy('dashborad'))


def disconnect(request):
    logout(request)
    return HttpResponseRedirect('/login')

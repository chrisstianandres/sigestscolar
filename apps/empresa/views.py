from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from apps.empresa.forms import Formulario
from apps.empresa.models import Empresa


class EmpresaView(TemplateView):
    model = Empresa
    template_name = 'empresa/empresa.html'
    template_name_add = 'empresa/form.html'
    icon = 'fas fa-school'
    entidad = 'Mi Empresa'
    form = Formulario

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'edit':
                objeto = self.model.objects.first()
                form = self.form(request.POST, instance=objeto)
                if form.is_valid():
                    form.save()
                else:
                    data['error'] = form.errors
            else:
                data['error'] = 'No ha seleccionado una opcion'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)

    def get(self, request, *args, **kwargs):
        data = {}
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'edit':
                    data = self.get_context_data()
                    data['action'] = action
                    data['form'] = self.form(instance=self.model.objects.first())
                    data['titulo_form'] = 'Editar datos de mi empresa'
                    return render(request, self.template_name_add, data)
            else:
                data = self.get_context_data()
                data['empresa'] = self.model.objects.filter(status=True).first()
                return render(request, self.template_name, data)
        except Exception as e:
            data['error'] = str(e)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['icono'] = self.icon
        data['boton'] = 'Guardar'
        data['titulo'] = 'Datos de la empresa'
        data['titulo_tabla'] = 'Datos de mi Empresa'
        data['entidad'] = self.entidad
        return data
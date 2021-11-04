from django.contrib.auth.models import User
from django.db import models

from apps.extras import ModeloBase


class Sexo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Sexo"
        verbose_name_plural = u"Sexos"
        unique_together = ('nombre',)

    def cantidad_matriculados(self):
        return Matricula.objects.values("id").filter(nivel__cerrado=False, nivel__periodo__activo=True,
                                                     inscripcion__persona__sexo=self).count()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Sexo, self).save(*args, **kwargs)


class Provincia(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Provincia"
        verbose_name_plural = u"Provincias"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def cantidad_matriculados(self, periodo):
        return Matricula.objects.values("id").filter(inscripcion__persona__provincia=self,
                                                     nivel__periodo=periodo).count()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Provincia, self).save(*args, **kwargs)


class Canton(ModeloBase):
    provincia = models.ForeignKey(Provincia, blank=True, null=True, verbose_name=u'Provincia', on_delete=models.PROTECT)
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Canton"
        verbose_name_plural = u"Cantones"
        ordering = ['nombre']
        unique_together = ('nombre', 'provincia')

    def cantidad_matriculados(self, periodo):
        return Matricula.objects.values("id").filter(inscripcion__persona__canton=self, nivel__periodo=periodo).count()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Canton, self).save(*args, **kwargs)


class Parroquia(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Parroquia"
        verbose_name_plural = u"Parroquias"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Parroquia, self).save(*args, **kwargs)


RH = [(1, '+'), (2, '-')]


class TipoSangre(ModeloBase):
    grupo = models.CharField(default='', max_length=2, verbose_name=u"Grupo", unique=True)
    rh = models.IntegerField(default=1, choices=RH, verbose_name=u"RH")

    def __str__(self):
        return '{}{}'.format(self.grupo, self.rh)

    class Meta:
        verbose_name = u"Tipo de Sangre"
        verbose_name_plural = u"Tipos de Sangre"
        ordering = ['grupo']
        unique_together = ('grupo',)

    def save(self, *args, **kwargs):
        self.grupo = self.grupo.upper()
        super(TipoSangre, self).save(*args, **kwargs)


class Persona(ModeloBase):
    nombres = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    apellido1 = models.CharField(default='', max_length=50, verbose_name=u"1er Apellido")
    apellido2 = models.CharField(default='', max_length=50, verbose_name=u"2do Apellido")
    cedula = models.CharField(default='', max_length=20, verbose_name=u"Cedula", blank=True)
    pasaporte = models.CharField(default='', max_length=20, blank=True, verbose_name=u"Pasaporte")
    ruc = models.CharField(default='', max_length=20, blank=True, null=True, verbose_name=u"Ruc")
    nacimiento = models.DateField(verbose_name=u"Fecha de nacimiento o constitución")
    genero = models.ForeignKey(Sexo, blank=True, null=True, verbose_name=u'Sexo', on_delete=models.PROTECT)
    lugarnacimiento = models.ForeignKey(Parroquia, blank=True, null=True, related_name='+', verbose_name=u"Lugar de nacimiento", on_delete=models.PROTECT)
    lugarecidencia = models.ForeignKey(Parroquia, blank=True, null=True, related_name='+', verbose_name=u"Lugar de residencia", on_delete=models.PROTECT)
    sector = models.CharField(default='', max_length=300, verbose_name=u"Sector de residencia")
    direccion = models.CharField(default='', max_length=300, verbose_name=u"Calle principal")
    direccion2 = models.CharField(default='', max_length=300, verbose_name=u"Calle secundaria")
    num_direccion = models.CharField(default='', max_length=15, verbose_name=u"Numero")
    referencia = models.CharField(default='', max_length=100, verbose_name=u"Referencia")
    telefono = models.CharField(default='', max_length=50, verbose_name=u"Telefono movil")
    telefono_conv = models.CharField(default='', max_length=50, verbose_name=u"Telefono fijo")
    email = models.CharField(default='', max_length=200, verbose_name=u"Correo electronico personal")
    emailinst = models.CharField(default='', max_length=200, verbose_name=u"Correo electronico institucional")
    sangre = models.ForeignKey(TipoSangre, blank=True, null=True, verbose_name=u"Tipo de Sangre", on_delete=models.PROTECT)
    libretamilitar = models.CharField(default='', max_length=20, verbose_name=u'Libreta militar')
    usuario = models.ForeignKey(User, null=True, on_delete=models.PROTECT)
    lgtbi = models.BooleanField(default=False, verbose_name=u'GLTBI')
    datosactualizados = models.IntegerField(default=0, verbose_name=u'Datos Actualizados')

    def __str__(self):
        return u'%s %s %s' % (self.apellido1, self.apellido2, self.nombres)

    class Meta:
        verbose_name = u"Persona"
        verbose_name_plural = u"Personal"
        ordering = ['apellido1', 'apellido2', 'nombres']
        unique_together = ('cedula', 'ruc', 'pasaporte',)

    def matriculado(self):
        return Matricula.objects.values("id").filter(cerrada=False, inscripcion__persona=self).exists()

    def tiene_matricula_periodo(self, periodo):
        return Matricula.objects.values("id").filter(cerrada=False, nivel__periodo=periodo,
                                                     inscripcion__persona=self).exists()

    def crear_perfil(self, administrativo=None, inscripcion=None, profesor=None, externo=None):
        if inscripcion:
            perfil = PerfilUsuario(persona=self,
                                   inscripcion=inscripcion)
            perfil.save()
        elif administrativo:
            perfil = PerfilUsuario(persona=self,
                                   administrativo=administrativo)
            perfil.save()
        elif profesor:
            perfil = PerfilUsuario(persona=self,
                                   profesor=profesor)
            perfil.save()
        elif externo:
            perfil = PerfilUsuario(persona=externo.persona,
                                   externo=externo)
            perfil.save()

    def perfilusuario_administrativo(self):
        if self.perfilusuario_set.values("id").filter(administrativo__isnull=False,
                                                      administrativo__activo=True).exists():
            return self.perfilusuario_set.filter(administrativo__isnull=False, administrativo__activo=True)[0]
        return None

    def perfilusuario_profesor(self):
        if self.perfilusuario_set.values("id").filter(profesor__isnull=False, profesor__activo=True).exists():
            return self.perfilusuario_set.filter(profesor__isnull=False, profesor__activo=True)[0]
        return None

    def perfil_inscripcion(self):
        if self.perfilusuario_set.values("id").filter(inscripcion__isnull=False, inscripcion__activo=True).exists():
            if self.perfilusuario_set.values("id").filter(inscripcion__isnull=False, inscripcion__activo=True,
                                                          inscripcionprincipal=True).exists():
                return self.perfilusuario_set.filter(inscripcion__isnull=False, inscripcion__activo=True,
                                                     inscripcionprincipal=True)[0]
            else:
                perfil = self.perfilusuario_set.filter(inscripcion__isnull=False, inscripcion__activo=True)[0]
                perfil.inscripcionprincipal = True
                perfil.save()
                return perfil
        return None

    def es_estudiante(self):
        return self.perfilusuario_set.values("id").filter(inscripcion__isnull=False).exists()

    def es_administrativo(self):
        return self.perfilusuario_set.values("id").filter(administrativo__isnull=False).exists()

    def es_profesor(self):
        return self.perfilusuario_set.values("id").filter(profesor__isnull=False).exists()

    def mis_inscripciones(self):
        return self.perfilusuario_set.values("id").filter(inscripcion__isnull=False)

    def necesita_cambiar_clave(self):
        return self.cambioclavepersona_set.values("id").exists()

    def clave_cambiada(self):
        self.cambioclavepersona_set.all().delete()

    def solicitud_cambio_clave(self, clave):
        if CambioClavePersona.objects.values("id").filter(persona=self, clavecambio=clave).exists():
            return CambioClavePersona.objects.filter(persona=self, clavecambio=clave)[0]
        return None

    def cambiar_clave(self):
        if self.cambioclavepersona_set.values("id").exists():
            cc = self.cambioclavepersona_set.all()[0]
            cc.solicitada = False
            cc.clavecambio = ""
        else:
            cc = CambioClavePersona(persona=self)
        cc.save()
        return cc

    def identificacion(self):
        if self.cedula:
            return self.cedula
        elif self.pasaporte:
            return self.pasaporte
        elif self.ruc:
            return self.ruc
        return ''

    def tipo_identificacion(self):
        if self.cedula:
            return 'C'
        elif self.pasaporte:
            return 'P'
        elif self.ruc:
            return 'R'
        return ''

    def telefonos(self):
        if self.telefono_conv and self.telefono:
            return self.telefono_conv + ", " + self.telefono
        elif self.telefono_conv:
            return self.telefono_conv
        elif self.telefono:
            return self.telefono
        return None

    def lista_telefonos(self):
        lista = []
        if self.telefono_conv:
            lista.append(self.telefono_conv)
        if self.telefono:
            lista.append(self.telefono)
        return lista

    def activo(self):
        return self.usuario.is_active

    def mi_cumpleannos(self):
        hoy = datetime.now().date()
        nacimiento = self.nacimiento
        if nacimiento.day == hoy.day and nacimiento.month == hoy.month:
            return True
        return False

    def edad(self):
        hoy = datetime.now().date()
        try:
            nac = self.nacimiento
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

    def emails(self):
        if self.emailinst:
            return self.emailinst
        elif self.email:
            return self.email
        return None

    def lista_emails(self):
        lista = []
        if self.emailinst:
            lista.append(self.emailinst)
        if self.email:
            lista.append(self.email)
        return lista

    def inscripcion_principal(self):
        if self.es_estudiante():
            if self.perfilusuario_set.values("id").filter(inscripcion__isnull=False,
                                                          inscripcionprincipal=True).exists():
                return self.perfilusuario_set.filter(inscripcion__isnull=False, inscripcionprincipal=True)[
                    0].inscripcion
            elif self.perfilusuario_set.values("id").filter(inscripcion__isnull=False).exists():
                perfil = self.perfilusuario_set.filter(inscripcion__isnull=False).order_by('-inscripcion__fecha')[0]
                perfil.inscripcionprincipal = True
                perfil.save()
                return perfil.inscripcion
        return None

    def profesor(self):
        if self.profesor_set.values("id").exists():
            return self.profesor_set.all()[0]
        return None

    def administrativo(self):
        if self.administrativo_set.values("id").exists():
            return self.administrativo_set.all()[0]
        return None

    def save(self, *args, **kwargs):
        if self.tipopersona == 1 or self.tipopersona == 3:
            self.apellido1 = self.apellido1.upper().strip()
            self.apellido2 = self.apellido2.upper().strip()
            self.cedula = self.cedula.upper().strip()
            self.pasaporte = self.pasaporte.upper().strip()
            self.nacionalidad = self.nacionalidad.upper().strip() if self.nacionalidad else ''
        else:
            self.ruc = self.ruc.upper().strip()
            self.cedula = ''
            self.pasaporte = ''
            self.nacionalidad = ''
        self.nombres = self.nombres.upper().strip()
        self.direccion = self.direccion.upper().strip()
        self.direccion2 = self.direccion2.upper().strip()
        self.num_direccion = self.num_direccion.upper().strip()
        self.sector = self.sector.upper().strip()
        self.ciudad = self.ciudad.upper().strip()
        self.telefono = self.telefono.upper().strip()
        self.telefono_conv = self.telefono_conv.upper().strip()
        self.email = self.email.lower()
        self.emailinst = self.emailinst.lower() if self.emailinst else ''
        super(Persona, self).save(*args, **kwargs)

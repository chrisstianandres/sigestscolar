"""
Django settings for sigestscolar project.

Generated by 'django-admin startproject' using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
import django_heroku

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from django.conf.global_settings import DATABASES

BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-#0!acpa9i=uarck@f(1a^m8s0j)l-7-1h-q((#$x1aq9muq%g^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.apps.AppsConfig',

    #crons
    'django_crontab',
    'django_heroku',

    #apps del sistema
    'apps.administrativo',
    'apps.alumno',
    'apps.curso',
    'apps.empresa',
    'apps.externo',
    'apps.factura',
    'apps.inscripcion',
    'apps.materia',
    'apps.matricula',
    'apps.paralelo',
    'apps.perfil',
    'apps.periodo',
    'apps.persona',
    'apps.producto',
    'apps.profesor',
    'apps.rubro'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'sigestscolar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sigestscolar.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
#
# DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql_psycopg2',
#             'NAME': 'bd_scolar',
#             'USER': 'postgres',
#             'PASSWORD': '1234',
#             'HOST': 'localhost',
#             'PORT': '5432',
#         }
#     }
import dj_database_url
from decouple import config
# DATABASES = {
#     'default': {
#         'ENGINE': dj_database_url.config(default=config('DATABASE_URL')),
#     }
# }
DATABASES['default'] = dj_database_url.config(default='postgres://bxsoroazpjrfbz:f30f5b57a8bd6a62c0d1900cd4744f4224e4890738eabe65e4e7fa7a227143dd@ec2-54-173-2-216.compute-1.amazonaws.com:5432/dfkchsoh541c61', conn_max_age=0)
# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ADMINISTRADOR_ID = 1

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_HOST_USER = 'wg29327@gmail.com'

EMAIL_HOST_PASSWORD = 'evcbhgdpvrrpmpcm'

DOMAIN = ''
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

SECRET_KEY_ENCRIPT = '1d47da2641a336aa57b8054abc018a8f'
LOGIN_REDIRECT_URL = '/dashborad/'

### ejecucion de crons
CRONJOBS = [
    # La función temporizada se ejecuta cada minuto
    ('*/1 * * * *', 'cronprueba.py'),
]


#django heroku
# django_heroku.settings(locals())



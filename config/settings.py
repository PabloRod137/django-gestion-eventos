"""
Configuración general del proyecto Django "App de Gestión de Eventos".

Generado inicialmente por 'django-admin startproject' y ajustado a mano
para las necesidades del proyecto. Documentación oficial de settings:
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os
from pathlib import Path

# BASE_DIR es la carpeta raíz del proyecto (donde está manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Seguridad básica ---
#
# SECRET_KEY firma internamente cookies de sesión, tokens CSRF, etc. En
# producción NUNCA debería ir escrita en el código ni subida a un repo
# público. Aquí se lee de la variable de entorno DJANGO_SECRET_KEY y, si
# no existe (como al clonar este repo para probarlo en local), se usa una
# clave de repuesto marcada como 'django-insecure-' (la misma convención
# que usa Django para avisar de que no es apta para producción).
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-c!oq-o7e75uf6-%$hv0=3jy(*eh*-^n#xl0p$ii$fj3s8d(+le',
)

# DEBUG=True: páginas de error detalladas y estáticos servidos sin
# configuración extra. Cómodo para desarrollar y para que cualquiera
# pueda levantar el proyecto sin complicaciones. En producción, False.
DEBUG = True

# Con DEBUG=True, Django permite automáticamente localhost/127.0.0.1
# aunque ALLOWED_HOSTS esté vacío.
ALLOWED_HOSTS = []


# --- Aplicaciones instaladas ---
# Las seis primeras vienen con Django (admin, autenticación, tipos de
# contenido, sesiones, mensajes flash, estáticos). 'events' es nuestra app.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'events',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Plantillas "compartidas" del proyecto (base.html, registro/login).
        # Las de cada app (templates/events/...) las encuentra Django solo,
        # gracias a APP_DIRS=True.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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


# --- Internacionalización ---
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'es-es'

# Con USE_TZ=True, Django guarda TODAS las fechas en UTC en la base de
# datos, y usa TIME_ZONE solo para convertir de/hacia UTC cuando el
# usuario introduce o visualiza una fecha (plantillas con |date,
# timezone.localtime() en el código...). Ver los comentarios en
# events/views.py y events/forms.py: es la parte del proyecto donde más
# fácil es cometer un error si no se tiene esto en cuenta.
TIME_ZONE = 'Europe/Madrid'

USE_I18N = True
USE_TZ = True


# --- Archivos estáticos (CSS, JS, imágenes) ---
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# --- Autenticación ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'event_list'
LOGOUT_REDIRECT_URL = 'login'

# Remitente que aparece en los emails de confirmación de inscripción.
DEFAULT_FROM_EMAIL = 'eventos@example.com'


# --- Correo ---
# https://docs.djangoproject.com/en/6.1/topics/email/
#
# Backend de "consola": en vez de enviar el email de verdad por SMTP,
# Django lo imprime en la terminal donde corre `runserver`. Es la forma
# estándar de probar el envío de correos en desarrollo. Para producción,
# bastaría con cambiar este backend por el de SMTP (o un servicio como
# SendGrid/Mailgun) sin tocar nada del código que llama a EmailMessage.
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

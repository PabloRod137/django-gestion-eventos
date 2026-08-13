# App de Gestión de Eventos

Aplicación Django para organizar eventos y gestionar inscripciones con aforo limitado.

Proyecto desarrollado como práctica del módulo de Django del máster de desarrollo full stack.

## Funcionalidades

- Registro, login y logout de usuarios
- Creación de eventos (título, descripción, categoría, ubicación, fechas, aforo)
- Inscripción y cancelación de inscripción a eventos, respetando el aforo máximo
- Vista de calendario mensual con los eventos de cada día
- Listado de "Mis inscripciones"
- Envío de email de confirmación al inscribirse (backend de consola en desarrollo)
- Exportación de la lista de asistentes a CSV (solo el organizador del evento)
- Panel de administración (Django admin) para gestionar categorías, eventos e inscripciones

## Modelos

- `Category`: categoría temática de un evento
- `Event`: evento con fechas, aforo y organizador
- `Registration`: inscripción de un usuario a un evento, con control de aforo

## Stack

- Python 3.12 + Django 6.1
- SQLite (desarrollo)
- Django templates + Bootstrap 5

## Puesta en marcha

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visita `http://127.0.0.1:8000/`.

## Estructura

```
config/       # configuración del proyecto Django
events/       # app principal: modelos, vistas, formularios, urls
templates/    # plantillas HTML
static/       # CSS/JS propios
```

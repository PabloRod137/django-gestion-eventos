# 🎟️ App de Gestión de Eventos

Aplicación Django para organizar eventos (charlas, talleres, quedadas...) y gestionar las inscripciones respetando un aforo máximo. Es uno de los proyectos que he desarrollado como práctica del módulo de Django dentro de mi máster de desarrollo full stack.

> **¿Qué resuelve exactamente?** Cualquiera puede crear un evento con un número limitado de plazas; los usuarios se apuntan y, en cuanto se llena el aforo, el sistema deja de admitir inscripciones (de verdad, no solo "de cara al usuario": lo comprueba también en el servidor, con protección contra condiciones de carrera).

## 🧭 Índice

- [¿Qué puedes hacer con esta app?](#-qué-puedes-hacer-con-esta-app)
- [Cómo está pensado por dentro](#-cómo-está-pensado-por-dentro)
- [Stack técnico](#-stack-técnico)
- [Ponerlo en marcha en tu máquina](#-ponerlo-en-marcha-en-tu-máquina)
- [Cómo probarlo rápido](#-cómo-probarlo-rápido)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Decisiones de diseño (y sus límites)](#-decisiones-de-diseño-y-sus-límites)
- [Posibles mejoras futuras](#-posibles-mejoras-futuras)

## ✅ ¿Qué puedes hacer con esta app?

- **Registrarte, iniciar sesión y cerrarla.**
- **Ver el listado de próximos eventos**, con filtro por categoría, sin necesidad de tener cuenta.
- **Crear un evento** (título, descripción, categoría, lugar, fechas y aforo). Quien lo crea queda como su organizador.
- **Apuntarte a un evento** con un clic. Si ya no quedan plazas, el botón se desactiva y, aunque alguien se lo salte a la fuerza, el servidor lo rechaza igualmente.
- **Recibir un email de confirmación** al apuntarte (en desarrollo se ve en la propia terminal, pero la infraestructura está lista para un servidor SMTP real).
- **Cancelar tu inscripción** cuando quieras, liberando la plaza para otra persona.
- **Consultar "Mis inscripciones"**: todos los eventos a los que estás apuntado.
- **Ver un calendario mensual** con los eventos de cada día, navegable mes a mes.
- **Exportar la lista de asistentes a CSV** — solo si eres tú quien organiza ese evento.
- **Gestionarlo todo desde el panel de administración de Django** (`/admin/`).

## 🧠 Cómo está pensado por dentro

Tres modelos en la app `events`:

```
Category (1) ---- (N) Event            -> un evento pertenece a una categoría (opcional)
Event    (1) ---- (N) Registration     -> las inscripciones de los usuarios a ese evento
```

Lo más interesante de este proyecto es cómo se controla el aforo. En vez de guardar "plazas restantes" como un número que se va descontando (lo cual es fácil que se desincronice de la realidad si algo falla a mitad de camino), el aforo se calcula **siempre al vuelo**: `Event.confirmed_count` cuenta cuántas inscripciones con estado "confirmada" tiene el evento en ese preciso instante, y `Event.spots_left` / `Event.is_full` se derivan de ahí. Así nunca hay un contador "mentiroso".

Eso sí, calcular el aforo al vuelo trae un problema clásico: **la condición de carrera**. Si dos personas pulsan "Apuntarme" casi a la vez y solo queda una plaza, en teoría las dos podrían comprobar "hay hueco" antes de que ninguna termine de guardar su inscripción, y acabarían apuntándose ambas. La vista `event_register` (en `events/views.py`) evita esto envolviendo la comprobación y la creación de la inscripción en una única transacción con `select_for_update()`, que bloquea la fila del evento mientras se resuelve la petición. Con SQLite (la base de datos de este proyecto en desarrollo) ese bloqueo no se aplica de verdad, pero el patrón es exactamente el que haría falta en producción con PostgreSQL o MySQL — está ahí para que el código sea correcto de verdad, no solo "aparentemente correcto".

Otro punto que mereció una vuelta extra: **las zonas horarias**. Django guarda internamente todas las fechas en UTC. Si en algún sitio del código formateas una fecha "a mano" con `strftime` en vez de pasarla antes por `timezone.localtime()` (o usar el filtro `|date` en las plantillas, que ya lo hace automáticamente), acabas mostrando la hora UTC en vez de la hora de Madrid — un desfase de 1 o 2 horas según la época del año. Este bug apareció de hecho en las primeras versiones del proyecto (en el email de confirmación y al colocar los eventos en el día correcto del calendario) y quedó corregido; los comentarios en `events/views.py` explican el porqué con detalle, por si te encuentras el mismo problema en otro proyecto Django.

## 🛠️ Stack técnico

| Pieza | Tecnología |
|---|---|
| Backend | Python 3.12 + Django 6.1 |
| Base de datos | SQLite (desarrollo/demo; en producción, PostgreSQL) |
| Frontend | Plantillas de Django + Bootstrap 5 (CDN) |
| Autenticación | `django.contrib.auth` |
| Correo | Backend de consola en desarrollo (listo para SMTP en producción) |

## 🚀 Ponerlo en marcha en tu máquina

```bash
# 1. Clona el repo y entra en la carpeta
git clone https://github.com/PabloRod137/django-gestion-eventos.git
cd django-gestion-eventos

# 2. Crea y activa un entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Aplica las migraciones (crea la base de datos)
python manage.py migrate

# 5. Crea un usuario administrador
python manage.py createsuperuser

# 6. Arranca el servidor
python manage.py runserver
```

Abre **http://127.0.0.1:8000/** en el navegador. Cuando alguien se apunte a un evento, verás el email de confirmación impreso directamente en esta misma terminal (backend de consola).

## 🔍 Cómo probarlo rápido

1. Regístrate en `/registro/`.
2. Crea un evento desde "Crear evento" con un aforo pequeño (por ejemplo, 1 plaza), para poder ver rápido qué pasa al completarse.
3. Apúntate: verás el email de confirmación en la terminal y el badge de plazas cambiará a "Aforo completo".
4. Prueba a exportar los asistentes a CSV (solo puedes si tú organizaste el evento).
5. Échale un ojo al calendario (`/calendario/`): tu evento debería aparecer en el día correcto.

## 📁 Estructura del proyecto

```
config/               # configuración del proyecto Django (settings, urls raíz)
events/                 # la app: modelos, vistas, formularios, admin, urls
    models.py             # Category, Event, Registration (aforo calculado al vuelo)
    views.py               # listados, calendario, apuntarse/cancelar, exportar CSV
    forms.py                 # formularios de registro y de creación de evento
    admin.py                   # configuración del panel de administración
templates/             # plantillas HTML (base.html + una por vista)
static/                # CSS propio
```

## 🎯 Decisiones de diseño (y sus límites)

- **El aforo se calcula al vuelo**, no se guarda como contador. Es la decisión que da más garantías de que el dato mostrado sea siempre correcto, a cambio de una consulta extra cuando se necesita.
- **La protección contra condiciones de carrera usa `select_for_update()`**, el patrón estándar de Django/SQL para esto. Funciona de verdad en PostgreSQL/MySQL; en SQLite (usado aquí en desarrollo) el bloqueo no tiene el mismo efecto práctico, pero el código es el correcto para cuando este proyecto se despliegue con una base de datos "de verdad".
- **Las inscripciones canceladas no se borran**, solo cambian de estado. Así se conserva el histórico y, si alguien se apunta, se da de baja y vuelve a apuntarse, se reutiliza la misma fila en vez de crear duplicados (hay además una restricción `unique_together` a nivel de base de datos que lo garantiza).
- **El email de confirmación usa el backend de consola.** Cambiar a un envío real (SMTP, SendGrid...) es solo cuestión de tocar `MAILERS` en `settings.py`; el código que llama a `EmailMessage` no necesita cambiar nada.

## 🔮 Posibles mejoras futuras

- Lista de espera automática cuando un evento está completo (y aviso por email si se libera una plaza).
- Recordatorio automático por email un día antes del evento.
- Permitir editar/borrar un evento ya creado (de momento solo se puede crear).
- Vista de calendario semanal, además de la mensual.

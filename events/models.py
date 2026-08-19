"""
Modelos de la app "events".

Tres modelos, relacionados así:

    Category (1) ---- (N) Event           -> un evento pertenece a una categoría (opcional)
    Event    (1) ---- (N) Registration    -> las inscripciones de los usuarios a ese evento
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """Categoría temática de un evento (Tecnología, Deporte, Cultura...). Muy simple a propósito."""

    name = models.CharField('nombre', max_length=80, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Un evento: charla, taller, quedada... con fecha, lugar y un aforo máximo.

    El control de aforo no se guarda como un número que se va descontando
    a mano: se calcula "al vuelo" contando cuántas inscripciones
    confirmadas (`Registration`) tiene el evento en cada momento (ver las
    propiedades más abajo). Es más lento que tener un contador cacheado,
    pero muchísimo más difícil que se desincronice con la realidad.
    """

    title = models.CharField('título', max_length=150)
    description = models.TextField('descripción', blank=True)
    # on_delete=SET_NULL + null=True: si se borra una categoría, los eventos
    # que la usaban no desaparecen, simplemente se quedan sin categoría.
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='events', verbose_name='categoría',
    )
    # Aquí sí usamos CASCADE: si se borra el usuario organizador, no tiene
    # mucho sentido conservar "huérfano" el evento que organizó.
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_events', verbose_name='organizador',
    )
    location = models.CharField('ubicación', max_length=150, blank=True)
    start_datetime = models.DateTimeField('inicio')
    end_datetime = models.DateTimeField('fin')
    capacity = models.PositiveIntegerField('aforo', default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def __str__(self):
        # title es un CharField normal (sin zona horaria de por medio), así
        # que aquí no hay ningún riesgo de mostrar una fecha mal convertida.
        return self.title

    def clean(self):
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')

    @property
    def confirmed_count(self):
        """Cuántas inscripciones CONFIRMADAS tiene el evento ahora mismo (no cuenta las canceladas)."""
        return self.registrations.filter(status=Registration.STATUS_CONFIRMED).count()

    @property
    def spots_left(self):
        """Plazas libres. Nunca negativo, aunque por lo que sea confirmed_count superase a capacity."""
        return max(self.capacity - self.confirmed_count, 0)

    @property
    def is_full(self):
        return self.spots_left <= 0


class Registration(models.Model):
    """
    La inscripción de un usuario a un evento.

    En vez de borrar la fila cuando alguien cancela su inscripción, cambiamos
    su `status` a "cancelada". Así, si luego se vuelve a apuntar al mismo
    evento, reutilizamos esa misma fila (ver events/views.py, event_register)
    en lugar de crear una nueva, lo cual además hace que unique_together
    seguir cumpliéndose sin complicaciones: cada pareja (evento, usuario)
    tiene como mucho una fila, sea cual sea su estado.
    """

    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, 'Confirmada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations', verbose_name='evento')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField('estado', max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registered_at']
        # A nivel de base de datos, impide que existan dos filas para el
        # mismo (evento, usuario). Es la última línea de defensa contra
        # inscripciones duplicadas, por si el código de la vista fallara.
        unique_together = ('event', 'user')
        verbose_name = 'inscripción'
        verbose_name_plural = 'inscripciones'

    def __str__(self):
        return f'{self.user} → {self.event}'

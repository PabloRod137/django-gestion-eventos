from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField('nombre', max_length=80, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField('título', max_length=150)
    description = models.TextField('descripción', blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='events', verbose_name='categoría',
    )
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
        return self.title

    def clean(self):
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')

    @property
    def confirmed_count(self):
        return self.registrations.filter(status=Registration.STATUS_CONFIRMED).count()

    @property
    def spots_left(self):
        return max(self.capacity - self.confirmed_count, 0)

    @property
    def is_full(self):
        return self.spots_left <= 0


class Registration(models.Model):
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
        unique_together = ('event', 'user')
        verbose_name = 'inscripción'
        verbose_name_plural = 'inscripciones'

    def __str__(self):
        return f'{self.user} → {self.event}'

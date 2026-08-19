"""
Tests automatizados de la app "events".

Se centran en el control de aforo: que Event.is_full/spots_left reflejen
siempre el número real de inscripciones confirmadas, que la vista rechace
una inscripción cuando ya no quedan plazas, y que cancelar una inscripción
libere el hueco. Para ejecutarlos:

    python manage.py test
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from .models import Event, Registration


class EventCapacityTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user('organizador', password='TestPass123!')
        start = timezone.now() + timedelta(days=1)
        self.event = Event.objects.create(
            title='Evento de prueba',
            organizer=self.organizer,
            start_datetime=start,
            end_datetime=start + timedelta(hours=2),
            capacity=1,
        )

    def test_evento_recien_creado_no_esta_lleno(self):
        self.assertFalse(self.event.is_full)
        self.assertEqual(self.event.spots_left, 1)

    def test_al_confirmar_una_inscripcion_se_llena_el_aforo(self):
        asistente = User.objects.create_user('asistente', password='TestPass123!')
        Registration.objects.create(event=self.event, user=asistente, status=Registration.STATUS_CONFIRMED)

        self.assertTrue(self.event.is_full)
        self.assertEqual(self.event.spots_left, 0)

    def test_la_vista_no_deja_apuntarse_si_no_quedan_plazas(self):
        # Primer asistente: ocupa la única plaza.
        asistente1 = User.objects.create_user('asistente1', password='TestPass123!')
        Registration.objects.create(event=self.event, user=asistente1, status=Registration.STATUS_CONFIRMED)

        # Segundo asistente: lo intenta a través de la vista real (no del modelo).
        asistente2 = User.objects.create_user('asistente2', password='TestPass123!')
        client = Client()
        client.login(username='asistente2', password='TestPass123!')
        client.post(f'/{self.event.pk}/apuntarse/', follow=True)

        confirmadas = Registration.objects.filter(event=self.event, status=Registration.STATUS_CONFIRMED)
        self.assertEqual(confirmadas.count(), 1)
        self.assertFalse(confirmadas.filter(user=asistente2).exists())

    def test_cancelar_inscripcion_libera_una_plaza(self):
        asistente = User.objects.create_user('asistente', password='TestPass123!')
        registration = Registration.objects.create(
            event=self.event, user=asistente, status=Registration.STATUS_CONFIRMED,
        )
        registration.status = Registration.STATUS_CANCELLED
        registration.save()

        self.assertFalse(self.event.is_full)
        self.assertEqual(self.event.spots_left, 1)

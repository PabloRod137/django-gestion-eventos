"""
Vistas de la app "events".

El punto más delicado de este archivo es event_register: ahí es donde se
decide si un usuario puede o no apuntarse a un evento según el aforo
disponible, y está protegido contra condiciones de carrera (ver el
comentario dentro de la función).
"""

import calendar
import csv
import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import EventForm, SignUpForm
from .models import Category, Event, Registration


def signup(request):
    """Registro de un usuario nuevo. Si todo va bien, lo deja logueado directamente."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido!')
            return redirect('event_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


class EventListView(ListView):
    """Listado público de eventos futuros, con filtro opcional por categoría (?category=<id>)."""

    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        # Solo eventos que todavía no han terminado. timezone.now() devuelve
        # el instante actual "aware" (consciente de zona horaria) en UTC,
        # que es como se comparan siempre las fechas frente a la base de
        # datos cuando USE_TZ=True.
        qs = Event.objects.filter(end_datetime__gte=timezone.now()).select_related('category')
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class EventDetailView(DetailView):
    """Ficha de un evento: descripción, aforo restante y, si has iniciado sesión, tu inscripción (si la tienes)."""

    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['registration'] = self.object.registrations.filter(user=user).first()
        return context


@login_required
def event_register(request, pk):
    """
    Inscribe al usuario logueado en un evento, respetando el aforo máximo.

    El "peligro" de este tipo de operación es la condición de carrera: si
    dos usuarios pulsan "Apuntarme" casi a la vez y quedaba exactamente
    una plaza libre, ambas peticiones podrían comprobar el aforo ANTES de
    que la otra termine de guardar su inscripción, y las dos verían "hay
    hueco" y se apuntarían, dejando el evento con una plaza de más.

    Para evitarlo, usamos select_for_update() dentro de una transacción:
    bloquea la fila del Event en la base de datos hasta que la transacción
    termina, así que si dos peticiones llegan a la vez, la segunda tiene
    que esperar a que la primera acabe (y su recuento de aforo ya será el
    correcto, actualizado). Nota para quien esté aprendiendo: SQLite (la
    base de datos que usa este proyecto en desarrollo) no aplica bloqueos
    de fila de verdad, así que en local esto no se puede "ver" fallar ni
    acertar; pero el patrón es el correcto y funciona tal cual con
    PostgreSQL o MySQL en producción.
    """
    event = get_object_or_404(Event, pk=pk)
    if request.method != 'POST':
        return redirect('event_detail', pk=pk)

    with transaction.atomic():
        # select_for_update() vuelve a leer el evento "bloqueando" su fila
        # hasta el final de este bloque `with`.
        event = Event.objects.select_for_update().get(pk=pk)

        existing = Registration.objects.filter(event=event, user=request.user).first()
        if existing and existing.status == Registration.STATUS_CONFIRMED:
            messages.info(request, 'Ya estabas apuntado a este evento.')
            return redirect('event_detail', pk=pk)

        if event.is_full:
            messages.error(request, 'Lo sentimos, el aforo de este evento ya está completo.')
            return redirect('event_detail', pk=pk)

        if existing:
            # Ya tenía una inscripción cancelada de antes: la reactivamos
            # en vez de crear una fila nueva (unique_together lo exige).
            existing.status = Registration.STATUS_CONFIRMED
            existing.save()
        else:
            Registration.objects.create(event=event, user=request.user, status=Registration.STATUS_CONFIRMED)

    messages.success(request, f'Te has apuntado a "{event.title}".')

    # El envío del email queda fuera de la transacción a propósito: es una
    # operación de red que puede tardar, y no tiene sentido mantener la fila
    # del evento bloqueada mientras esperamos a que el email salga.
    email = EmailMessage(
        subject=f'Confirmación de inscripción: {event.title}',
        body=(
            f'Hola {request.user.username},\n\n'
            f'Tu inscripción al evento "{event.title}" ha sido confirmada.\n'
            # timezone.localtime() convierte la fecha (guardada internamente
            # en UTC) a la hora de Madrid antes de formatearla. Si aquí se
            # formateara event.start_datetime directamente, se mostraría la
            # hora en UTC, que no coincide con la hora local casi nunca.
            f'Fecha: {timezone.localtime(event.start_datetime):%d/%m/%Y %H:%M}\n'
            f'Lugar: {event.location or "por confirmar"}\n\n'
            '¡Nos vemos allí!'
        ),
        to=[request.user.email] if request.user.email else [],
    )
    if email.to:
        email.send(fail_silently=True)

    return redirect('event_detail', pk=pk)


@login_required
def event_unregister(request, pk):
    """Cancela la inscripción propia a un evento (no la borra, solo cambia su estado, ver Registration)."""
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(Registration, event=event, user=request.user)
    if request.method == 'POST':
        registration.status = Registration.STATUS_CANCELLED
        registration.save()
        messages.success(request, f'Has cancelado tu inscripción a "{event.title}".')
        return redirect('event_detail', pk=pk)
    return render(request, 'events/registration_confirm_cancel.html', {'event': event})


@login_required
def my_registrations(request):
    """"Mis inscripciones": eventos a los que el usuario logueado está apuntado ahora mismo."""
    registrations = Registration.objects.filter(
        user=request.user, status=Registration.STATUS_CONFIRMED,
    ).select_related('event')
    return render(request, 'events/my_registrations.html', {'registrations': registrations})


@login_required
def event_create(request):
    """Crea un evento nuevo. El usuario que lo crea queda como organizador automáticamente."""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)  # commit=False: aún no guarda en la BD, nos da margen para completar el objeto
            event.organizer = request.user
            event.full_clean()
            event.save()
            messages.success(request, 'Evento creado correctamente.')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})


@login_required
def export_attendees(request, pk):
    """Descarga en CSV la lista de inscritos a un evento. Solo puede hacerlo quien lo organizó."""
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.id:
        # 403 Forbidden: el usuario está autenticado pero no tiene permiso
        # sobre ESTE recurso en concreto (distinto de un 401, que sería
        # "no has iniciado sesión").
        return HttpResponseForbidden('Solo el organizador puede exportar los asistentes.')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="asistentes_{event.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Usuario', 'Email', 'Estado', 'Fecha de inscripción'])
    for reg in event.registrations.select_related('user').order_by('user__username'):
        writer.writerow([
            reg.user.username,
            reg.user.email,
            reg.get_status_display(),
            # También aquí convertimos a hora local antes de mostrarla, por
            # el mismo motivo que en el email de confirmación.
            timezone.localtime(reg.registered_at).strftime('%d/%m/%Y %H:%M'),
        ])
    return response


def event_calendar(request):
    """
    Vista de calendario mensual: una tabla de 6 semanas (como cualquier
    calendario de pared) con los eventos de cada día. Usa el módulo
    `calendar` de la librería estándar de Python para generar la cuadrícula
    de fechas; nosotros solo tenemos que "rellenar" cada día con sus eventos.
    """
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    first_of_month = datetime.date(year, month, 1)
    # Truco para calcular el mes anterior/siguiente sin salirse de rango:
    # restamos/sumamos un día al primer/último día del mes y nos quedamos
    # con el día 1 de lo que resulte.
    prev_month = (first_of_month - datetime.timedelta(days=1)).replace(day=1)
    next_month = (first_of_month + datetime.timedelta(days=32)).replace(day=1)

    events = Event.objects.filter(start_datetime__year=year, start_datetime__month=month)
    events_by_day = {}
    for event in events:
        # Igual que en el email: convertimos a hora local antes de mirar
        # ".day". Si no lo hiciéramos, un evento que empieza, por ejemplo,
        # a las 00:30 de un día en Madrid podría estar guardado como las
        # 22:30 o 23:30 UTC del día ANTERIOR, y aparecería en la casilla
        # equivocada del calendario.
        local_start = timezone.localtime(event.start_datetime)
        events_by_day.setdefault(local_start.day, []).append(event)

    # calendar.Calendar(firstweekday=0) hace que las semanas empiecen en
    # lunes (0), como es habitual en España, en vez de en domingo.
    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_days = []
        for day in week:
            week_days.append({
                'date': day,
                'in_month': day.month == month,  # monthdatescalendar rellena también días de meses vecinos
                'events': events_by_day.get(day.day, []) if day.month == month else [],
                'is_today': day == today,
            })
        weeks.append(week_days)

    context = {
        'weeks': weeks,
        'month_date': first_of_month,  # se formatea en la plantilla con el filtro |date:"F Y" (localizado a español)
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
    }
    return render(request, 'events/calendar.html', context)

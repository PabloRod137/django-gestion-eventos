import calendar
import csv
import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import EventForm, SignUpForm
from .models import Category, Event, Registration


def signup(request):
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
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
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
    event = get_object_or_404(Event, pk=pk)
    if request.method != 'POST':
        return redirect('event_detail', pk=pk)

    existing = Registration.objects.filter(event=event, user=request.user).first()
    if existing and existing.status == Registration.STATUS_CONFIRMED:
        messages.info(request, 'Ya estabas apuntado a este evento.')
        return redirect('event_detail', pk=pk)

    if event.is_full:
        messages.error(request, 'Lo sentimos, el aforo de este evento ya está completo.')
        return redirect('event_detail', pk=pk)

    if existing:
        existing.status = Registration.STATUS_CONFIRMED
        existing.save()
    else:
        Registration.objects.create(event=event, user=request.user, status=Registration.STATUS_CONFIRMED)

    messages.success(request, f'Te has apuntado a "{event.title}".')

    email = EmailMessage(
        subject=f'Confirmación de inscripción: {event.title}',
        body=(
            f'Hola {request.user.username},\n\n'
            f'Tu inscripción al evento "{event.title}" ha sido confirmada.\n'
            f'Fecha: {event.start_datetime:%d/%m/%Y %H:%M}\n'
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
    registrations = Registration.objects.filter(
        user=request.user, status=Registration.STATUS_CONFIRMED,
    ).select_related('event')
    return render(request, 'events/my_registrations.html', {'registrations': registrations})


@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
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
    event = get_object_or_404(Event, pk=pk)
    if event.organizer_id != request.user.id:
        return HttpResponseForbidden('Solo el organizador puede exportar los asistentes.')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="asistentes_{event.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Usuario', 'Email', 'Estado', 'Fecha de inscripción'])
    for reg in event.registrations.select_related('user').order_by('user__username'):
        writer.writerow([reg.user.username, reg.user.email, reg.get_status_display(), reg.registered_at])
    return response


def event_calendar(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    first_of_month = datetime.date(year, month, 1)
    prev_month = (first_of_month - datetime.timedelta(days=1)).replace(day=1)
    next_month = (first_of_month + datetime.timedelta(days=32)).replace(day=1)

    events = Event.objects.filter(start_datetime__year=year, start_datetime__month=month)
    events_by_day = {}
    for event in events:
        events_by_day.setdefault(event.start_datetime.day, []).append(event)

    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_days = []
        for day in week:
            week_days.append({
                'date': day,
                'in_month': day.month == month,
                'events': events_by_day.get(day.day, []) if day.month == month else [],
                'is_today': day == today,
            })
        weeks.append(week_days)

    context = {
        'weeks': weeks,
        'month_date': first_of_month,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
    }
    return render(request, 'events/calendar.html', context)

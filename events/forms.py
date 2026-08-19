"""
Formularios de la app "events".

- SignUpForm: registro de usuarios (igual que en los otros proyectos del
  máster, para mantener la misma experiencia de registro en los tres).
- EventForm: alta de un evento nuevo.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Event


class SignUpForm(UserCreationForm):
    """Registro de usuario: añade el email (obligatorio) a lo que ya trae Django de serie."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class EventForm(forms.ModelForm):
    """Formulario de creación de eventos. Quien lo envía queda como organizador (se asigna en la vista)."""

    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'location', 'start_datetime', 'end_datetime', 'capacity']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            # datetime-local: el propio navegador muestra un selector de
            # fecha y hora nativo, sin necesidad de JavaScript adicional.
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hace falta indicar el formato de entrada explícitamente porque el
        # texto que manda el input datetime-local ("2026-08-20T18:00") no
        # coincide con los formatos de fecha por defecto de Django.
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class

    def clean(self):
        """
        El input datetime-local no manda información de zona horaria, así
        que Django lo interpreta como un datetime "naive" (sin tzinfo). Con
        USE_TZ=True en settings.py, hay que convertirlo a "aware" antes de
        que llegue a guardarse; si no, Django avisa con un RuntimeWarning y,
        peor, la hora que se ve más tarde en la web puede no coincidir con
        la que el usuario escribió (por el desfase del horario de verano).
        timezone.make_aware() interpreta el valor "naive" usando la zona
        horaria del proyecto (TIME_ZONE = 'Europe/Madrid').
        """
        cleaned_data = super().clean()
        for field_name in ('start_datetime', 'end_datetime'):
            value = cleaned_data.get(field_name)
            if value and timezone.is_naive(value):
                cleaned_data[field_name] = timezone.make_aware(value)
        return cleaned_data

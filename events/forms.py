from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Event


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'location', 'start_datetime', 'end_datetime', 'capacity']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        for name, field in self.fields.items():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class

from django.urls import path

from . import views

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('calendario/', views.event_calendar, name='event_calendar'),
    path('nuevo/', views.event_create, name='event_create'),
    path('mis-inscripciones/', views.my_registrations, name='my_registrations'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/apuntarse/', views.event_register, name='event_register'),
    path('<int:pk>/cancelar/', views.event_unregister, name='event_unregister'),
    path('<int:pk>/asistentes.csv', views.export_attendees, name='export_attendees'),
    path('registro/', views.signup, name='signup'),
]

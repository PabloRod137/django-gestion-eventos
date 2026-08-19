"""
Configuración del panel de administración (/admin/) para la app "events".
"""

from django.contrib import admin

from .models import Category, Event, Registration


class RegistrationInline(admin.TabularInline):
    """
    Muestra las inscripciones de un evento directamente dentro de su propia
    página de edición, en modo solo lectura: desde aquí un administrador
    puede CONSULTAR quién está apuntado, pero no editar los datos a mano
    (para eso ya está la vista normal de Registration en el admin).
    """

    model = Registration
    extra = 0  # no añadir filas vacías: aquí solo se consulta, no se crea
    readonly_fields = ('user', 'status', 'registered_at')
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # confirmed_count es una @property del modelo (no un campo de la BD),
    # pero el admin de Django la puede mostrar en list_display igualmente
    # siempre que no se intente además filtrar/ordenar por ella.
    list_display = ('title', 'category', 'organizer', 'start_datetime', 'capacity', 'confirmed_count')
    list_filter = ('category',)
    search_fields = ('title', 'location')
    date_hierarchy = 'start_datetime'
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'registered_at')
    list_filter = ('status', 'event')
    search_fields = ('user__username', 'event__title')

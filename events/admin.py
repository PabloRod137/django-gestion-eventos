from django.contrib import admin

from .models import Category, Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    readonly_fields = ('user', 'status', 'registered_at')
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
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

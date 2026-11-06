from django.contrib import admin
from .models import Asistencia, Persona


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'muestras', 'registrado')
    search_fields = ('nombre',)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('persona', 'fecha', 'hora', 'confianza')
    list_filter = ('fecha', 'persona')
    search_fields = ('persona__nombre',)
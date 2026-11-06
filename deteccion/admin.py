from django.contrib import admin
from .models import Asistencia


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'hora', 'rostros_detectados')
    list_filter = ('fecha',)
    search_fields = ('nombre',)
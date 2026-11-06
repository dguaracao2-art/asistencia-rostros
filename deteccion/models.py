from django.db import models
from django.utils import timezone


class Persona(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    muestras = models.PositiveSmallIntegerField(default=0)
    registrado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return self.nombre


class Asistencia(models.Model):
    persona = models.ForeignKey(
        Persona, on_delete=models.CASCADE, related_name='asistencias'
    )
    fecha = models.DateField(default=timezone.localdate)
    hora = models.TimeField(auto_now_add=True)
    confianza = models.FloatField(default=0)

    class Meta:
        ordering = ['-fecha', '-hora']
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        constraints = [
            models.UniqueConstraint(
                fields=['persona', 'fecha'],
                name='unica_asistencia_por_dia'
            )
        ]

    def __str__(self):
        return f'{self.persona.nombre} - {self.fecha}'
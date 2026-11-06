from django.db import models
from django.utils import timezone


class Asistencia(models.Model):
    nombre = models.CharField(max_length=100)
    fecha = models.DateField(default=timezone.localdate)
    hora = models.TimeField(auto_now_add=True)
    rostros_detectados = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-fecha', '-hora']
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'fecha'],
                name='unica_asistencia_por_dia'
            )
        ]

    def __str__(self):
        return f'{self.nombre} - {self.fecha}'
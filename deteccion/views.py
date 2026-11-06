import time

import cv2
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Asistencia
from .services.camara import Camara
from .services.detector import DetectorRostros

_detector = None


def _obtener_detector():
    """Carga el clasificador una sola vez y lo reutiliza."""
    global _detector
    if _detector is None:
        _detector = DetectorRostros()
    return _detector


def _generar_frames():
    """Generador que entrega frames JPEG continuamente al navegador."""
    camara = Camara.obtener()
    detector = _obtener_detector()
    while True:
        ok, frame = camara.leer()
        if not ok:
            time.sleep(0.1)
            continue

        rostros = detector.detectar(frame)
        frame = detector.dibujar(frame, rostros)

        ok, buffer = cv2.imencode('.jpg', frame)
        if not ok:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + buffer.tobytes() + b'\r\n')


def index(request):
    registros = Asistencia.objects.all()[:15]
    total_hoy = Asistencia.objects.filter(fecha=timezone.localdate()).count()
    return render(request, 'deteccion/index.html', {
        'registros': registros,
        'total_hoy': total_hoy,
    })


def video_feed(request):
    return StreamingHttpResponse(
        _generar_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


@require_POST
def registrar_asistencia(request):
    nombre = request.POST.get('nombre', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'mensaje': 'Escribe un nombre.'})

    camara = Camara.obtener()
    ok, frame = camara.leer()
    if not ok:
        return JsonResponse({'ok': False, 'mensaje': 'No se pudo leer la cámara.'})

    rostros = _obtener_detector().detectar(frame)
    if len(rostros) == 0:
        return JsonResponse({
            'ok': False,
            'mensaje': 'No se detectó ningún rostro. Ubícate frente a la cámara.'
        })

    hoy = timezone.localdate()
    if Asistencia.objects.filter(nombre__iexact=nombre, fecha=hoy).exists():
        return JsonResponse({
            'ok': False,
            'mensaje': f'{nombre} ya registró asistencia hoy.'
        })

    Asistencia.objects.create(
        nombre=nombre,
        fecha=hoy,
        rostros_detectados=len(rostros)
    )
    return JsonResponse({
        'ok': True,
        'mensaje': f'Asistencia registrada para {nombre}.'
    })
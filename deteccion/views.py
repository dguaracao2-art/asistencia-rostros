import time
from collections import Counter

import cv2
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Asistencia, Persona
from .services.camara import Camara
from .services.detector import DetectorRostros
from .services.reconocedor import Reconocedor

MUESTRAS = 25
SEGUNDOS_VIDA = 6.0
UMBRAL_DUPLICADO = 60.0

_detector = None


def _obtener_detector():
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


def _verificar_parpadeo(camara, detector, segundos=SEGUNDOS_VIDA):
    """
    Detección de vida. Observa la secuencia ojos abiertos -> cerrados -> abiertos.
    Una fotografía mantiene un estado constante, por lo que no supera la prueba.
    Devuelve (vivo, frame, rostro, motivo).
    """
    fin = time.time() + segundos
    fase = 0            # 0 esperando apertura, 1 esperando cierre, 2 confirmado
    cerrados = 0
    frame_ok = None
    rostro_ok = None
    vistos = 0

    while time.time() < fin and fase < 2:
        ok, frame = camara.leer()
        if not ok:
            time.sleep(0.03)
            continue

        rostros = detector.detectar(frame)
        if len(rostros) != 1:
            time.sleep(0.04)
            continue

        vistos += 1
        rostro = rostros[0]
        abiertos = detector.contar_ojos(frame, rostro) >= 2

        if abiertos:
            frame_ok, rostro_ok = frame.copy(), rostro

        if fase == 0 and abiertos:
            fase = 1
        elif fase == 1:
            if not abiertos:
                cerrados += 1
            elif cerrados >= 1:
                fase = 2
            else:
                cerrados = 0

        time.sleep(0.04)

    if vistos == 0:
        return False, None, None, 'No se detectó ningún rostro frente a la cámara.'
    if fase < 2:
        return False, None, None, ('No se detectó parpadeo. Mira a la cámara y '
                                   'parpadea para confirmar que eres una persona.')
    return True, frame_ok, rostro_ok, ''


def _identificar_estable(camara, detector, reconocedor, muestras=7,
                         umbral=UMBRAL_DUPLICADO):
    """
    Identifica el rostro con varias lecturas consecutivas y devuelve la
    coincidencia más frecuente. Reduce el efecto de lecturas aisladas erróneas.
    """
    if reconocedor.personas == 0:
        return None, None

    lecturas = []
    intentos = 0

    while len(lecturas) < muestras and intentos < muestras * 6:
        intentos += 1
        ok, frame = camara.leer()
        if not ok:
            time.sleep(0.04)
            continue

        rostros = detector.detectar(frame)
        if len(rostros) != 1:
            time.sleep(0.04)
            continue

        recorte = detector.recortar(frame, rostros[0])
        pid, conf = reconocedor.identificar(recorte, umbral=umbral)
        if pid is not None:
            lecturas.append((pid, conf))
        time.sleep(0.05)

    if not lecturas:
        return None, None

    pid = Counter(p for p, _ in lecturas).most_common(1)[0][0]
    mejor = min(c for p, c in lecturas if p == pid)
    return pid, mejor


def index(request):
    return render(request, 'deteccion/index.html', {
        'registros': Asistencia.objects.select_related('persona')[:15],
        'total_hoy': Asistencia.objects.filter(fecha=timezone.localdate()).count(),
        'personas': Persona.objects.all(),
    })


def video_feed(request):
    return StreamingHttpResponse(
        _generar_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


@require_POST
def registrar_persona(request):
    """
    Captura muestras del rostro y reentrena el modelo.
    Rechaza el registro si el rostro ya pertenece a otra persona del sistema.
    """
    nombre = request.POST.get('nombre', '').strip()
    if not nombre:
        return JsonResponse({'ok': False, 'mensaje': 'Escribe un nombre.'})

    camara = Camara.obtener()
    detector = _obtener_detector()
    reconocedor = Reconocedor.obtener()

    existente = Persona.objects.filter(nombre__iexact=nombre).first()

    duplicado_id, conf = _identificar_estable(camara, detector, reconocedor)
    if duplicado_id is not None and (existente is None or duplicado_id != existente.id):
        otro = Persona.objects.filter(id=duplicado_id).first()
        if otro is not None:
            return JsonResponse({
                'ok': False,
                'mensaje': f'Este rostro ya está registrado como "{otro.nombre}" '
                           f'(similitud {conf:.1f}). No se permite inscribir a la '
                           f'misma persona con dos nombres distintos.'
            })

    persona = existente
    creada = False
    if persona is None:
        persona = Persona.objects.create(nombre=nombre)
        creada = True

    capturadas = 0
    intentos = 0
    inicio = persona.muestras

    while capturadas < MUESTRAS and intentos < MUESTRAS * 6:
        intentos += 1
        ok, frame = camara.leer()
        if not ok:
            time.sleep(0.05)
            continue

        rostros = detector.detectar(frame)
        if len(rostros) != 1:
            time.sleep(0.05)
            continue

        recorte = detector.recortar(frame, rostros[0])
        reconocedor.guardar_muestra(persona.id, recorte, inicio + capturadas)
        capturadas += 1
        time.sleep(0.1)

    if capturadas == 0:
        if creada:
            persona.delete()
        return JsonResponse({
            'ok': False,
            'mensaje': 'No se capturó ningún rostro. Ubícate frente a la cámara.'
        })

    persona.muestras = inicio + capturadas
    persona.save()
    total = reconocedor.entrenar()

    return JsonResponse({
        'ok': True,
        'mensaje': f'{nombre} registrado con {capturadas} muestras. '
                   f'Personas en el modelo: {total}.'
    })


@require_POST
def registrar_asistencia(request):
    """Verifica que sea una persona real, la identifica y registra su asistencia."""
    camara = Camara.obtener()
    detector = _obtener_detector()
    reconocedor = Reconocedor.obtener()

    if reconocedor.personas == 0:
        return JsonResponse({
            'ok': False,
            'mensaje': 'Aún no hay personas registradas en el sistema.'
        })

    vivo, frame, rostro, motivo = _verificar_parpadeo(camara, detector)
    if not vivo:
        return JsonResponse({'ok': False, 'mensaje': motivo})

    recorte = detector.recortar(frame, rostro)
    persona_id, confianza = reconocedor.identificar(recorte)

    if persona_id is None:
        return JsonResponse({
            'ok': False,
            'mensaje': 'Rostro no reconocido. Regístrate primero en el sistema.'
        })

    persona = Persona.objects.filter(id=persona_id).first()
    if persona is None:
        return JsonResponse({'ok': False, 'mensaje': 'La persona ya no existe.'})

    hoy = timezone.localdate()
    if Asistencia.objects.filter(persona=persona, fecha=hoy).exists():
        return JsonResponse({
            'ok': False,
            'mensaje': f'{persona.nombre} ya registró asistencia hoy.'
        })

    Asistencia.objects.create(
        persona=persona, fecha=hoy, confianza=round(confianza, 2)
    )
    return JsonResponse({
        'ok': True,
        'mensaje': f'Asistencia registrada para {persona.nombre} '
                   f'(confianza {confianza:.1f}).'
    })
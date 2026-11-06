import os
import threading

import cv2
import numpy as np
from django.conf import settings


class Reconocedor:
    """
    Reconocimiento facial con LBPH (Local Binary Patterns Histograms).
    Entrena a partir de las muestras guardadas en media/rostros/<id_persona>/.
    En LBPH un valor de confianza MENOR indica mayor similitud.
    """

    UMBRAL = 75.0
    _instancia = None
    _lock_global = threading.Lock()

    def __init__(self):
        self.lock = threading.Lock()
        self.modelo = None
        self.personas = 0
        self.entrenar()

    @classmethod
    def obtener(cls):
        with cls._lock_global:
            if cls._instancia is None:
                cls._instancia = Reconocedor()
            return cls._instancia

    @staticmethod
    def carpeta(persona_id=None):
        base = os.path.join(settings.MEDIA_ROOT, 'rostros')
        return base if persona_id is None else os.path.join(base, str(persona_id))

    def guardar_muestra(self, persona_id, imagen, indice):
        destino = self.carpeta(persona_id)
        os.makedirs(destino, exist_ok=True)
        cv2.imwrite(os.path.join(destino, f'{indice}.jpg'), imagen)

    def entrenar(self):
        """
        Reconstruye el modelo con las muestras de las personas vigentes.
        Las carpetas de personas eliminadas se ignoran.
        """
        from ..models import Persona

        validos = set(Persona.objects.values_list('id', flat=True))
        imagenes, etiquetas = [], []
        base = self.carpeta()

        if os.path.isdir(base):
            for nombre_dir in os.listdir(base):
                if not nombre_dir.isdigit() or int(nombre_dir) not in validos:
                    continue
                ruta_dir = os.path.join(base, nombre_dir)
                for archivo in os.listdir(ruta_dir):
                    img = cv2.imread(os.path.join(ruta_dir, archivo),
                                     cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        imagenes.append(img)
                        etiquetas.append(int(nombre_dir))

        with self.lock:
            if not imagenes:
                self.modelo = None
                self.personas = 0
            else:
                modelo = cv2.face.LBPHFaceRecognizer_create()
                modelo.train(imagenes, np.array(etiquetas, dtype=np.int32))
                self.modelo = modelo
                self.personas = len(set(etiquetas))
        return self.personas

    def identificar(self, rostro, umbral=None):
        """Devuelve (persona_id, confianza) o (None, confianza) si no coincide."""
        limite = self.UMBRAL if umbral is None else umbral
        with self.lock:
            if self.modelo is None:
                return None, None
            etiqueta, confianza = self.modelo.predict(rostro)

        if confianza > limite:
            return None, confianza
        return etiqueta, confianza
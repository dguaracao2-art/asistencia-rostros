import threading
import cv2


class Camara:
    """
    Maneja una única instancia de la cámara para todo el proyecto.
    Evita el error de 'cámara ocupada' cuando el video en vivo y el
    registro de asistencia intentan leerla al mismo tiempo.
    """

    _instancia = None
    _lock_global = threading.Lock()

    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.lock = threading.Lock()

    @classmethod
    def obtener(cls):
        with cls._lock_global:
            if cls._instancia is None:
                cls._instancia = Camara()
            return cls._instancia

    def leer(self):
        with self.lock:
            return self.cap.read()

    def disponible(self):
        return self.cap.isOpened()
import cv2


class DetectorRostros:
    """
    Encapsula la detección de rostros y ojos con OpenCV.
    Usa clasificadores Haar Cascade entrenados que incluye la librería.
    """

    TAM = 200

    def __init__(self):
        base = cv2.data.haarcascades
        self.clasificador = cv2.CascadeClassifier(
            base + 'haarcascade_frontalface_default.xml')
        self.clasificador_ojos = cv2.CascadeClassifier(
            base + 'haarcascade_eye.xml')

        if self.clasificador.empty():
            raise RuntimeError('No se pudo cargar el clasificador de rostros.')
        if self.clasificador_ojos.empty():
            raise RuntimeError('No se pudo cargar el clasificador de ojos.')

    def detectar(self, frame):
        """Recibe un frame BGR y devuelve las coordenadas de los rostros."""
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris = cv2.equalizeHist(gris)
        return self.clasificador.detectMultiScale(
            gris, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

    def contar_ojos(self, frame, rostro):
        """Cuenta los ojos abiertos dentro de la mitad superior del rostro."""
        x, y, w, h = rostro
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi = gris[y:y + int(h * 0.6), x:x + w]
        if roi.size == 0:
            return 0
        roi = cv2.equalizeHist(roi)
        minimo = max(12, int(w * 0.12))
        ojos = self.clasificador_ojos.detectMultiScale(
            roi, scaleFactor=1.1, minNeighbors=6, minSize=(minimo, minimo)
        )
        return len(ojos)

    def recortar(self, frame, rostro):
        """Extrae el rostro, lo pasa a gris y lo normaliza a un tamaño fijo."""
        x, y, w, h = rostro
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        recorte = gris[y:y + h, x:x + w]
        recorte = cv2.resize(recorte, (self.TAM, self.TAM),
                             interpolation=cv2.INTER_AREA)
        return cv2.equalizeHist(recorte)

    def dibujar(self, frame, rostros):
        """Dibuja un recuadro sobre cada rostro y el contador en pantalla."""
        for (x, y, w, h) in rostros:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'Rostro', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        texto = f'Rostros detectados: {len(rostros)}'
        cv2.putText(frame, texto, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return frame
import cv2


class DetectorRostros:
    """
    Encapsula la detección de rostros con OpenCV.
    Usa el clasificador Haar Cascade entrenado que incluye la librería.
    """

    def __init__(self):
        ruta = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.clasificador = cv2.CascadeClassifier(ruta)
        if self.clasificador.empty():
            raise RuntimeError('No se pudo cargar el clasificador Haar de OpenCV.')

    def detectar(self, frame):
        """Recibe un frame BGR y devuelve las coordenadas de los rostros."""
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris = cv2.equalizeHist(gris)
        rostros = self.clasificador.detectMultiScale(
            gris,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )
        return rostros

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
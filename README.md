# Control de asistencia por detección de rostros

Aplicativo web desarrollado en Django que captura video en tiempo real desde la cámara, detecta rostros mediante OpenCV y registra la asistencia en una base de datos PostgreSQL.

Proyecto académico de la asignatura Construcción de Software — Universidad Estatal de Milagro (UNEMI).

## Tecnologías

- Python 3.12
- Django 6.1
- OpenCV 4.x (clasificador Haar Cascade)
- PostgreSQL 18

## Funcionalidades

- Transmisión de video en tiempo real en el navegador mediante streaming MJPEG.
- Detección de rostros con recuadro y contador superpuestos sobre el video.
- Registro de asistencia solo cuando se confirma la presencia de un rostro.
- Restricción de un único registro por persona y por día, aplicada a nivel de base de datos.
- Historial de registros visible en la misma pantalla.
- Panel de administración para consultar, filtrar y buscar asistencias.

## Instalación

1. Clonar el repositorio: git clone https://github.com/USUARIO/asistencia-rostros.git
cd asistencia-rostros

2. Crear y activar el entorno virtual: python -m venv venv
venv\Scripts\activate


3. Instalar las dependencias: pip install -r requirements.txt

4. Crear la base de datos en PostgreSQL:
   ```sql
   CREATE DATABASE asistencia_db;
   ```

5. Configurar las credenciales en `config/settings.py`, dentro del bloque `DATABASES`.

6. Aplicar las migraciones: python manage.py migrate

7. Crear el usuario administrador: python manage.py createsuperuser

8. Ejecutar el servidor: python manage.py runserver

9. Abrir `http://127.0.0.1:8000/` en el navegador.

## Estructura del proyecto
asistencia-rostros/
├── config/ Configuración general de Django
├── deteccion/
│ ├── services/
│ │ ├── camara.py Acceso único a la cámara
│ │ └── detector.py Detección de rostros con OpenCV
│ ├── templates/ Interfaz web
│ ├── models.py Modelo Asistencia
│ └── views.py Video en vivo y registro
├── requirements.txt
└── manage.py


## Nota sobre la versión de OpenCV

El proyecto requiere OpenCV 4.x. La versión 5.0 eliminó `CascadeClassifier` del paquete de Python, por lo que las versiones están fijadas en `requirements.txt`.

## Autores

- Christian Mora Archundia
- Aldahir Barreto Carranza
- Michael Méndez Barzola
- Danny Ismael Guaraca Orozco
- César Josué Cruz Neira

**Docente:** Msc. Mariana Almache Sanisaca
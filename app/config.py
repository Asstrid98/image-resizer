import os

class Config:
    # Configuración de la Base de Datos
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///image_resizer.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración del Servidor
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Seguridad y Límites (Vital para DevOps)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Limita subidas a 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # --- RETO 1.1: Presets de tamaño ---
    # Esto permite que el usuario no tenga que enviar números siempre
    SIZE_PRESETS = {
        'thumbnail': (150, 150),
        'medium': (800, 600),
        'large': (1920, 1080)
    }
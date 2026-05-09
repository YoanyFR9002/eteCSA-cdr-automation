"""
Configuración centralizada para ASN.1 Web Decoder
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración principal de la aplicación"""
    
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Secret key para sesiones Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    
    # Configuración de servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"
    
    # Límites de subida
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))  # 100MB default
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE
    
    # Directorios
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    EXPORT_FOLDER = BASE_DIR / "exports"
    LOG_FOLDER = BASE_DIR / "logs"
    
    # Asegurar que los directorios existen
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    EXPORT_FOLDER.mkdir(exist_ok=True)
    LOG_FOLDER.mkdir(exist_ok=True)
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Seguridad
    ALLOWED_EXTENSIONS = {'bin', 'hex', 'txt', 'dat', 'der', 'ber'}
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hora
    
    # API
    API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100 per minute")
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
    
    # Características
    ENABLE_SEARCH = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
    ENABLE_EXPORT = os.getenv("ENABLE_EXPORT", "true").lower() == "true"
    ENABLE_STATS = os.getenv("ENABLE_STATS", "true").lower() == "true"
    ENABLE_HEATMAP = os.getenv("ENABLE_HEATMAP", "true").lower() == "true"
    
    # Redis (opcional para caché)
    REDIS_HOST = os.getenv("REDIS_HOST", None)
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379")) if os.getenv("REDIS_PORT") else None
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Base de datos (si se usa en el futuro)
    DATABASE_URL = os.getenv("DATABASE_URL", None)
    
    # Proxy (útil para entornos con limitaciones de red)
    HTTP_PROXY = os.getenv("HTTP_PROXY", None)
    HTTPS_PROXY = os.getenv("HTTPS_PROXY", None)
    
    @classmethod
    def init_app(cls, app):
        """Inicializa configuración en aplicación Flask"""
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        app.config['UPLOAD_FOLDER'] = str(cls.UPLOAD_FOLDER)
        app.config['EXPORT_FOLDER'] = str(cls.EXPORT_FOLDER)
        app.config['SESSION_TIMEOUT'] = cls.SESSION_TIMEOUT
        
        # Configurar rate limiting si está disponible
        if cls.API_RATE_LIMIT:
            app.config['RATELIMIT_DEFAULT'] = cls.API_RATE_LIMIT


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    SECRET_KEY = "dev-secret-key-not-for-production"


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    LOG_LEVEL = "INFO"
    
    # Validar que SECRET_KEY esté configurada
    if Config.SECRET_KEY == "dev-key-change-in-production":
        raise ValueError("SECRET_KEY debe ser configurada en producción")


class TestingConfig(Config):
    """Configuración para tests"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    SECRET_KEY = "test-key"


# Mapeo de configuraciones
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}


def get_config() -> Config:
    """Obtiene configuración según entorno"""
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, config_map["default"])

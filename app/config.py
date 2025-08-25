"""
Configuración de la aplicación Flask.
Este módulo contiene todas las configuraciones necesarias para diferentes entornos.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

class Config:
    """Configuración base para todos los entornos."""
    
    # Clave secreta para sesiones y seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Lista de claves de API válidas, separadas por coma en .env
    API_KEYS = [key.strip() for key in os.environ.get('API_KEYS', '').split(',') if key]
    
    # Configuración de base de datos SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///messages.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    # Lista de palabras inapropiadas (filtro simple)
    INAPPROPRIATE_WORDS = [
        'spam', 'malware', 'virus', 'hack', 'phishing'
    ]

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Configuración para pruebas."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    TESTING = False
    # En producción, usar una base de datos real
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///messages_prod.db')

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
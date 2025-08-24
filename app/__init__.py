"""
Factory de aplicación Flask.
Este módulo configura y crea la aplicación Flask con todas sus dependencias.
"""
import os
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.models.message import db
from app.repositories.message_repository import MessageRepository
from app.services.message_service import MessageService
from app.controllers.message_controller import MessageController
from datetime import datetime, timezone  

def create_app(config_name=None):
    """
    Factory function para crear la aplicación Flask.
    
    Args:
        config_name: Nombre de la configuración a usar ('development', 'testing', 'production')
        
    Returns:
        Flask: Instancia configurada de la aplicación
    """
    # Crear instancia de Flask
    app = Flask(__name__)
    
    # Configurar la aplicación
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    app.config['JSON_AS_ASCII'] = False  # Para caracteres especiales (tildes, ñ, etc.)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['JSON_SORT_KEYS'] = False    
    
    # Configurar CORS para permitir peticiones desde frontend
    CORS(app)
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar manejadores de error
    register_error_handlers(app)
    
    # Configurar dependencias e inyección
    with app.app_context():
        setup_dependencies(app)
    
    return app

def setup_dependencies(app):
    """
    Configura las dependencias y la inyección de dependencias.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    # Crear tablas si no existen
    db.create_all()
    
    # Instanciar repositorios
    message_repository = MessageRepository()
    
    # Instanciar servicios
    message_service = MessageService(
        message_repository=message_repository,
        inappropriate_words=app.config['INAPPROPRIATE_WORDS']
    )
    
    # Instanciar controladores
    message_controller = MessageController(message_service)
    
    # Registrar blueprints
    app.register_blueprint(message_controller.blueprint)
    
    # Registrar endpoint de salud
    @app.route('/health')
    def health_check():
        """Endpoint para verificar el estado de la aplicación."""
        return {
            'status': 'ok',
            'message': 'Servicio funcionando correctamente',
            'service': 'Message Processing API',
            'timestamp': datetime.now(timezone.utc),
            'encoding': 'UTF-8 ✓'
        }
    
    @app.route('/')
    def index():
        """Endpoint raíz con información de la API."""
        return {
            'name': 'Message Processing API',
            'version': '1.0.0',
            'description': 'API RESTful para procesamiento de mensajes de chat',
            'endpoints': {
                'POST /api/messages': 'Crear un nuevo mensaje',
                'GET /api/messages/<session_id>': 'Obtener mensajes por sesión',
                'GET /api/message/<message_id>': 'Obtener mensaje específico',
                'GET /api/sessions/<session_id>/stats': 'Obtener estadísticas de sesión',
                'GET /health': 'Estado de la aplicación'
            }
        }

def register_error_handlers(app):
    """
    Registra manejadores de error globales.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    @app.errorhandler(404)
    def not_found(error):
        """Manejador para errores 404."""
        return {
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Endpoint no encontrado'
            }
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Manejador para errores 405."""
        return {
            'status': 'error',
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Método HTTP no permitido'
            }
        }, 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejador para errores 500."""
        return {
            'status': 'error',
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'Error interno del servidor'
            }
        }, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Manejador para errores 400."""
        return {
            'status': 'error',
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Petición malformada'
            }
        }, 400
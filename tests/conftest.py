"""
Configuración de pytest y fixtures compartidos.
Este módulo define fixtures reutilizables para todas las pruebas.
"""
import pytest
import tempfile
import os
from app import create_app
from app.models.message import db
from app.repositories.message_repository import MessageRepository
from app.services.message_service import MessageService

@pytest.fixture
def app():
    """Fixture que crea una aplicación Flask para testing."""
    # Crear archivo temporal para la base de datos de prueba
    db_fd, db_path = tempfile.mkstemp()
    
    # Configurar aplicación para testing
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        
    # Limpiar después de la prueba
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Fixture que crea un cliente de prueba."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Fixture que crea un runner para comandos CLI."""
    return app.test_cli_runner()

@pytest.fixture
def message_repository(app):
    """Fixture que crea un repositorio de mensajes."""
    with app.app_context():
        return MessageRepository()

@pytest.fixture
def message_service(app, message_repository):
    """Fixture que crea un servicio de mensajes."""
    with app.app_context():
        inappropriate_words = ['spam', 'malware', 'virus']
        return MessageService(message_repository, inappropriate_words)

@pytest.fixture
def sample_message_data():
    """Fixture con datos de mensaje de prueba válidos - TODOS los campos obligatorios."""
    return {
        "message_id": "msg-test-123",
        "session_id": "session-test-abc",
        "content": "Este es un mensaje de prueba",
        "timestamp": "2023-06-15T14:30:00Z",
        "sender": "user"
    }

@pytest.fixture
def sample_system_message_data():
    """Fixture con datos de mensaje del sistema - TODOS los campos obligatorios."""
    return {
        "message_id": "msg-system-456",
        "session_id": "session-test-abc",
        "content": "Respuesta del sistema automática",
        "timestamp": "2023-06-15T14:30:05Z",
        "sender": "system"
    }

@pytest.fixture
def invalid_message_data():
    """Fixture con datos de mensaje inválidos - campos faltantes o vacíos."""
    return {
        "message_id": "",  # ID vacío
        "session_id": "",  # session_id vacío
        "content": "",  # Contenido vacío
        "timestamp": "invalid-date",  # Fecha inválida
        "sender": "invalid"  # Sender inválido
    }

@pytest.fixture
def incomplete_message_data():
    """Fixture con datos de mensaje incompletos - faltan campos obligatorios."""
    return {
        "message_id": "msg-incomplete",
        "session_id": "session-test",
        "content": "Mensaje incompleto"
        # Faltan timestamp y sender obligatorios
    }
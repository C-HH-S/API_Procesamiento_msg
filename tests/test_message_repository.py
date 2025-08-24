"""
Pruebas unitarias para MessageRepository.
Este módulo prueba todas las operaciones de base de datos.
"""
import pytest
from datetime import datetime
from app.models.message import Message
from app.utils.exceptions import DatabaseError

class TestMessageRepository:
    """Suite de pruebas para MessageRepository."""
    
    def test_save_message_success(self, app, message_repository):
        """Prueba guardar un mensaje exitosamente."""
        with app.app_context():
            # Crear mensaje
            message = Message(
                message_id="test-msg-1",
                session_id="test-session-1",
                content="Contenido de prueba",
                timestamp=datetime.utcnow(),
                sender="user"
            )
            
            # Guardar mensaje
            saved_message = message_repository.save(message)
            
            # Verificaciones
            assert saved_message.id is not None
            assert saved_message.message_id == "test-msg-1"
            assert saved_message.session_id == "test-session-1"
            assert saved_message.content == "Contenido de prueba"
            assert saved_message.sender == "user"
    
    def test_find_by_message_id_exists(self, app, message_repository):
        """Prueba buscar un mensaje que existe."""
        with app.app_context():
            # Crear y guardar mensaje
            message = Message(
                message_id="test-msg-2",
                session_id="test-session-1",
                content="Contenido de prueba",
                timestamp=datetime.utcnow(),
                sender="user"
            )
            message_repository.save(message)
            
            # Buscar mensaje
            found_message = message_repository.find_by_message_id("test-msg-2")
            
            # Verificaciones
            assert found_message is not None
            assert found_message.message_id == "test-msg-2"
    
    def test_find_by_message_id_not_exists(self, app, message_repository):
        """Prueba buscar un mensaje que no existe."""
        with app.app_context():
            found_message = message_repository.find_by_message_id("non-existent")
            assert found_message is None
    
    def test_find_by_session_id_with_messages(self, app, message_repository):
        """Prueba buscar mensajes por session_id cuando existen."""
        with app.app_context():
            session_id = "test-session-2"
            
            # Crear varios mensajes para la misma sesión
            messages = []
            for i in range(5):
                message = Message(
                    message_id=f"test-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user" if i % 2 == 0 else "system"
                )
                message_repository.save(message)
                messages.append(message)
            
            # Buscar mensajes
            found_messages, total_count = message_repository.find_by_session_id(session_id)
            
            # Verificaciones
            assert len(found_messages) == 5
            assert total_count == 5
            assert all(msg.session_id == session_id for msg in found_messages)
    
    def test_find_by_session_id_with_pagination(self, app, message_repository):
        """Prueba paginación en búsqueda por session_id."""
        with app.app_context():
            session_id = "test-session-pagination"
            
            # Crear 15 mensajes
            for i in range(15):
                message = Message(
                    message_id=f"pag-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user"
                )
                message_repository.save(message)
            
            # Primera página
            messages_page1, total = message_repository.find_by_session_id(
                session_id, limit=5, offset=0
            )
            assert len(messages_page1) == 5
            assert total == 15
            
            # Segunda página
            messages_page2, total = message_repository.find_by_session_id(
                session_id, limit=5, offset=5
            )
            assert len(messages_page2) == 5
            assert total == 15
            
            # Tercera página
            messages_page3, total = message_repository.find_by_session_id(
                session_id, limit=5, offset=10
            )
            assert len(messages_page3) == 5
            assert total == 15
    
    def test_find_by_session_id_with_sender_filter(self, app, message_repository):
        """Prueba filtro por sender en búsqueda por session_id."""
        with app.app_context():
            session_id = "test-session-filter"
            
            # Crear mensajes con diferentes senders
            for i in range(6):
                message = Message(
                    message_id=f"filter-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user" if i < 3 else "system"
                )
                message_repository.save(message)
            
            # Buscar solo mensajes de usuario
            user_messages, user_total = message_repository.find_by_session_id(
                session_id, sender="user"
            )
            assert len(user_messages) == 3
            assert user_total == 3
            assert all(msg.sender == "user" for msg in user_messages)
            
            # Buscar solo mensajes del sistema
            system_messages, system_total = message_repository.find_by_session_id(
                session_id, sender="system"
            )
            assert len(system_messages) == 3
            assert system_total == 3
            assert all(msg.sender == "system" for msg in system_messages)
    
    def test_exists_by_message_id(self, app, message_repository):
        """Prueba verificación de existencia por message_id."""
        with app.app_context():
            # Verificar que no existe inicialmente
            assert not message_repository.exists_by_message_id("test-exists")
            
            # Crear mensaje
            message = Message(
                message_id="test-exists",
                session_id="test-session",
                content="Contenido",
                timestamp=datetime.utcnow(),
                sender="user"
            )
            message_repository.save(message)
            
            # Verificar que ahora existe
            assert message_repository.exists_by_message_id("test-exists")
    
    def test_count_by_session_id(self, app, message_repository):
        """Prueba conteo de mensajes por session_id."""
        with app.app_context():
            session_id = "test-session-count"
            
            # Inicialmente no hay mensajes
            assert message_repository.count_by_session_id(session_id) == 0
            
            # Crear 3 mensajes
            for i in range(3):
                message = Message(
                    message_id=f"count-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user"
                )
                message_repository.save(message)
            
            # Verificar conteo
            assert message_repository.count_by_session_id(session_id) == 3
    
    def test_count_by_session_id_with_sender_filter(self, app, message_repository):
        """Prueba conteo con filtro por sender."""
        with app.app_context():
            session_id = "test-session-count-filter"
            
            # Crear mensajes mixtos
            for i in range(4):
                message = Message(
                    message_id=f"count-filter-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user" if i < 2 else "system"
                )
                message_repository.save(message)
            
            # Verificar conteos
            total_count = message_repository.count_by_session_id(session_id)
            user_count = message_repository.count_by_session_id(session_id, "user")
            system_count = message_repository.count_by_session_id(session_id, "system")
            
            assert total_count == 4
            assert user_count == 2
            assert system_count == 2
    
    def test_delete_by_message_id_exists(self, app, message_repository):
        """Prueba eliminación de mensaje existente."""
        with app.app_context():
            # Crear mensaje
            message = Message(
                message_id="test-delete",
                session_id="test-session",
                content="Contenido a eliminar",
                timestamp=datetime.utcnow(),
                sender="user"
            )
            message_repository.save(message)
            
            # Verificar que existe
            assert message_repository.exists_by_message_id("test-delete")
            
            # Eliminar mensaje
            deleted = message_repository.delete_by_message_id("test-delete")
            assert deleted is True
            
            # Verificar que ya no existe
            assert not message_repository.exists_by_message_id("test-delete")
    
    def test_delete_by_message_id_not_exists(self, app, message_repository):
        """Prueba eliminación de mensaje que no existe."""
        with app.app_context():
            deleted = message_repository.delete_by_message_id("non-existent")
            assert deleted is False
    
    def test_get_session_ids(self, app, message_repository):
        """Prueba obtención de session_ids únicos."""
        with app.app_context():
            session_ids = ["session-1", "session-2", "session-1", "session-3"]
            
            # Crear mensajes con diferentes session_ids
            for i, session_id in enumerate(session_ids):
                message = Message(
                    message_id=f"session-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.utcnow(),
                    sender="user"
                )
                message_repository.save(message)
            
            # Obtener session_ids únicos
            unique_sessions = message_repository.get_session_ids()
            
            # Verificar que son únicos
            assert len(unique_sessions) == 3
            assert set(unique_sessions) == {"session-1", "session-2", "session-3"}
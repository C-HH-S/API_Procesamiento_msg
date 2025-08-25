"""
Pruebas unitarias para MessageService.
Este módulo prueba la lógica de negocio del procesamiento de mensajes.
"""
import pytest
from datetime import datetime
from app.utils.exceptions import (
    ValidationError, 
    InvalidFormatError, 
    InappropriateContentError,
    MessageNotFoundError,
    DatabaseError
)

class TestMessageService:
    """Suite de pruebas para MessageService."""
    
    def test_process_message_success(self, app, message_service, sample_message_data):
        """Prueba procesamiento exitoso de un mensaje válido."""
        with app.app_context():
            # Procesar mensaje
            result = message_service.process_message(sample_message_data)
            
            # Verificaciones
            assert result['message_id'] == sample_message_data['message_id']
            assert result['session_id'] == sample_message_data['session_id']
            assert result['content'] == sample_message_data['content']
            assert result['sender'] == sample_message_data['sender']
            assert 'timestamp' in result
            
            # Verificar metadatos
            assert 'metadata' in result
            assert result['metadata']['word_count'] == 6  # "Este es un mensaje de prueba"
            assert result['metadata']['character_count'] == 28
    
    def test_process_message_invalid_format(self, app, message_service):
        """Prueba procesamiento de mensaje con formato inválido."""
        with app.app_context():
            invalid_data = {
                "message_id": "",  # ID vacío
                "session_id": "session-test",
                "content": "Contenido válido",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user"
            }
            
            with pytest.raises(ValidationError):
                message_service.process_message(invalid_data)
    
    def test_process_message_missing_fields(self, app, message_service):
        """Prueba procesamiento de mensaje con campos faltantes."""
        with app.app_context():
            incomplete_data = {
                "message_id": "msg-123",
                "session_id": "session-test"
                # Faltan campos requeridos
            }
            
            with pytest.raises(ValidationError) as exc_info:
                message_service.process_message(incomplete_data)
            
            assert "Campos requeridos faltantes" in str(exc_info.value)
    
    def test_process_message_inappropriate_content(self, app, message_service):
        """Prueba procesamiento de mensaje con contenido inapropiado."""
        with app.app_context():
            inappropriate_data = {
                "message_id": "msg-bad-123",
                "session_id": "session-test",
                "content": "Este mensaje contiene spam y malware",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user"
            }
            
            with pytest.raises(InappropriateContentError) as exc_info:
                message_service.process_message(inappropriate_data)
            
            assert "contenido inapropiado" in str(exc_info.value).lower()
    
    def test_process_message_invalid_sender(self, app, message_service):
        """Prueba procesamiento de mensaje con sender inválido."""
        with app.app_context():
            invalid_sender_data = {
                "message_id": "msg-invalid-sender",
                "session_id": "session-test",
                "content": "Contenido válido",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "invalid_sender"  # Sender inválido
            }
            
            with pytest.raises(InvalidFormatError) as exc_info:
                message_service.process_message(invalid_sender_data)
            
            assert "'sender' debe ser 'user' o 'system'" in str(exc_info.value)
    
    def test_process_message_invalid_timestamp(self, app, message_service):
        """Prueba procesamiento de mensaje con timestamp inválido."""
        with app.app_context():
            invalid_timestamp_data = {
                "message_id": "msg-invalid-timestamp",
                "session_id": "session-test",
                "content": "Contenido válido",
                "timestamp": "not-a-valid-timestamp",
                "sender": "user"
            }
            
            with pytest.raises(InvalidFormatError) as exc_info:
                message_service.process_message(invalid_timestamp_data)
            
            assert "formato ISO 8601" in str(exc_info.value)
    
    def test_get_messages_by_session_success(self, app, message_service, sample_message_data, sample_system_message_data):
        """Prueba obtención exitosa de mensajes por sesión."""
        with app.app_context():
            # Procesar dos mensajes para la misma sesión
            message_service.process_message(sample_message_data)
            message_service.process_message(sample_system_message_data)
            
            # Obtener mensajes de la sesión
            result = message_service.get_messages_by_session("session-test-abc")
            
            # Verificaciones
            assert len(result['messages']) == 2
            assert result['pagination']['total'] == 2
            assert result['pagination']['limit'] == 10
            assert result['pagination']['offset'] == 0
            assert result['pagination']['has_next'] is False
            assert result['pagination']['has_prev'] is False
    
    def test_get_messages_by_session_with_pagination(self, app, message_service):
        """Prueba paginación en obtención de mensajes por sesión."""
        with app.app_context():
            session_id = "session-pagination-test"
            
            # Crear 15 mensajes
            for i in range(15):
                message_data = {
                    "message_id": f"msg-pag-{i}",
                    "session_id": session_id,
                    "content": f"Contenido del mensaje {i}",
                    "timestamp": "2023-06-15T14:30:00Z",
                    "sender": "user"
                }
                message_service.process_message(message_data)
            
            # Primera página (5 elementos)
            result_page1 = message_service.get_messages_by_session(session_id, limit=5, offset=0)
            assert len(result_page1['messages']) == 5
            assert result_page1['pagination']['total'] == 15
            assert result_page1['pagination']['has_next'] is True
            assert result_page1['pagination']['has_prev'] is False
            
            # Segunda página
            result_page2 = message_service.get_messages_by_session(session_id, limit=5, offset=5)
            assert len(result_page2['messages']) == 5
            assert result_page2['pagination']['has_next'] is True
            assert result_page2['pagination']['has_prev'] is True
    
    def test_get_messages_by_session_with_sender_filter(self, app, message_service):
        """Prueba filtro por sender en obtención de mensajes."""
        with app.app_context():
            session_id = "session-filter-test"
            
            # Crear mensajes mixtos
            for i in range(6):
                message_data = {
                    "message_id": f"msg-filter-{i}",
                    "session_id": session_id,
                    "content": f"Contenido {i}",
                    "timestamp": "2023-06-15T14:30:00Z",
                    "sender": "user" if i < 3 else "system"
                }
                message_service.process_message(message_data)
            
            # Filtrar solo mensajes de usuario
            user_result = message_service.get_messages_by_session(session_id, sender="user")
            assert len(user_result['messages']) == 3
            assert user_result['pagination']['total'] == 3
            assert all(msg['sender'] == 'user' for msg in user_result['messages'])
            
            # Filtrar solo mensajes del sistema
            system_result = message_service.get_messages_by_session(session_id, sender="system")
            assert len(system_result['messages']) == 3
            assert system_result['pagination']['total'] == 3
            assert all(msg['sender'] == 'system' for msg in system_result['messages'])
    
    def test_get_messages_by_session_invalid_sender(self, app, message_service):
        """Prueba filtro con sender inválido."""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                message_service.get_messages_by_session("session-test", sender="invalid")
            
            assert "sender debe ser uno de" in str(exc_info.value)
    
    def test_get_messages_by_session_empty(self, app, message_service):
        """Prueba obtención de mensajes de sesión vacía."""
        with app.app_context():
            result = message_service.get_messages_by_session("session-empty")
            
            assert len(result['messages']) == 0
            assert result['pagination']['total'] == 0
    
    def test_get_message_by_id_success(self, app, message_service, sample_message_data):
        """Prueba obtención exitosa de mensaje por ID."""
        with app.app_context():
            # Procesar mensaje
            message_service.process_message(sample_message_data)

            
            # Obtener mensaje por ID
            result = message_service.get_message_by_id("msg-test-123")
            
            # Verificaciones
            assert result['message_id'] == "msg-test-123"
            assert result['content'] == "Este es un mensaje de prueba"
    
    def test_get_message_by_id_not_found(self, app, message_service):
        """Prueba obtención de mensaje inexistente."""
        with app.app_context():
            with pytest.raises(MessageNotFoundError) as exc_info:
                message_service.get_message_by_id("non-existent-msg")
            
            assert "No se encontró mensaje con ID" in str(exc_info.value)
    
    def test_get_session_statistics(self, app, message_service):
        """Prueba obtención de estadísticas de sesión."""
        with app.app_context():
            session_id = "session-stats-test"
            
            # Crear mensajes mixtos
            messages_data = [
                {"message_id": "stats-1", "sender": "user"},
                {"message_id": "stats-2", "sender": "user"},
                {"message_id": "stats-3", "sender": "system"},
                {"message_id": "stats-4", "sender": "system"},
                {"message_id": "stats-5", "sender": "system"}
            ]
            
            for msg_data in messages_data:
                full_data = {
                    "message_id": msg_data["message_id"],
                    "session_id": session_id,
                    "content": "Contenido de prueba",
                    "timestamp": "2023-06-15T14:30:00Z",
                    "sender": msg_data["sender"]
                }
                message_service.process_message(full_data)
            
            # Obtener estadísticas
            stats = message_service.get_session_statistics(session_id)
            
            # Verificaciones
            assert stats['session_id'] == session_id
            assert stats['total_messages'] == 5
            assert stats['user_messages'] == 2
            assert stats['system_messages'] == 3
    
    def test_process_message_database_error(self, app, message_service, sample_message_data, monkeypatch):
        """Simula un fallo de base de datos durante process_message."""
        from app.repositories.message_repository import MessageRepository
        from app.utils.exceptions import DatabaseError

        def mock_save_message(*args, **kwargs):
            raise DatabaseError("Error al guardar en DB")

        # Cambia "save_message" por el nombre real de tu método (ej: add_message)
        monkeypatch.setattr(MessageRepository, "save", mock_save_message)

        with app.app_context():
            with pytest.raises(DatabaseError) as exc_info:
                message_service.process_message(sample_message_data)

            assert "Error al guardar en DB" in str(exc_info.value)

    def test_process_message_unexpected_error(self, app, message_service, sample_message_data, monkeypatch):
        """Simula un error inesperado (se espera Exception cruda según implementación actual)."""
        from app.repositories.message_repository import MessageRepository

        def mock_save_message(*args, **kwargs):
            raise Exception("error raro")

        monkeypatch.setattr(MessageRepository, "save", mock_save_message)

        with app.app_context():
            with pytest.raises(Exception) as exc_info:
                message_service.process_message(sample_message_data)

            assert "error raro" in str(exc_info.value).lower()


    def test_get_message_by_id_database_error(self, app, message_service, sample_message_data, monkeypatch):
        """Simula error de DB al buscar mensaje por ID."""
        from app.repositories.message_repository import MessageRepository
        from app.utils.exceptions import DatabaseError

        def mock_find_by_message_id(*args, **kwargs):
            raise DatabaseError("Error al consultar DB")

        monkeypatch.setattr(MessageRepository, "find_by_message_id", mock_find_by_message_id)

        with app.app_context():
            with pytest.raises(DatabaseError) as exc_info:
                message_service.get_message_by_id(sample_message_data["message_id"])

            assert "Error al consultar DB" in str(exc_info.value)


def test_get_message_by_id_not_found(app, message_service, monkeypatch):
    """Debe lanzar MessageNotFoundError si no existe el mensaje."""
    def mock_find_by_message_id(*args, **kwargs):
        return None

    from app.repositories.message_repository import MessageRepository
    monkeypatch.setattr(MessageRepository, "find_by_message_id", mock_find_by_message_id)

    with app.app_context():
        with pytest.raises(MessageNotFoundError):
            message_service.get_message_by_id("id-inexistente")


def test_delete_message_ok(app, message_service, monkeypatch):
    from app.repositories.message_repository import MessageRepository

    def mock_delete_by_message_id(self, message_id):
        return True

    monkeypatch.setattr(MessageRepository, "delete_by_message_id", mock_delete_by_message_id)

    with app.app_context():
        result = message_service.delete_message("msg-1")
        assert result is True



def test_delete_message_not_found(app, message_service, monkeypatch):
    """Debe retornar False cuando no se encuentra el mensaje a eliminar."""     
    from app.repositories.message_repository import MessageRepository

    # Agregamos 'self' como primer argumento
    def mock_delete_by_message_id(self, message_id):
        return False

    monkeypatch.setattr(MessageRepository, "delete_by_message_id", mock_delete_by_message_id)

    with app.app_context():
        result = message_service.delete_message("msg-404")
        assert result is False


def test_get_session_stats_error(app, message_service, monkeypatch):
    """Debe propagar DatabaseError si ocurre fallo en repositorio al obtener stats."""
    def mock_count_by_session_id(session_id, sender=None):
        raise DatabaseError("Error al contar mensajes")

    from app.repositories.message_repository import MessageRepository
    monkeypatch.setattr(MessageRepository, "count_by_session_id", mock_count_by_session_id)

    with app.app_context():
        with pytest.raises(DatabaseError):
            message_service.get_session_statistics("session-x")


class MockMessage:
    def __init__(self, content):
        self.content = content
    def to_dict(self):
        return {"content": self.content}
    
    def test_search_messages_globally_ok(app, message_service, monkeypatch):
        """Debe retornar lista de mensajes y total al buscar globalmente."""
        def mock_search_globally(self, query, limit, offset):
            return [MockMessage("m1"), MockMessage("m2")], 2

        from app.repositories.message_repository import MessageRepository
        monkeypatch.setattr(MessageRepository, "search_globally", mock_search_globally)

        with app.app_context():
            results, total = message_service.search_messages_globally("hola", 10, 0)
            assert [msg["content"] for msg in results] == ["m1", "m2"]
            assert total == 2


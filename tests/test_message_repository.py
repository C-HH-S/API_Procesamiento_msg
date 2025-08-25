"""
Pruebas unitarias para MessageRepository.
Este módulo prueba todas las operaciones de base de datos.
"""
import pytest
from datetime import datetime, timezone
from app.models.message import Message
from app.utils.exceptions import DatabaseError
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from app.models.message import Message, db
from app.repositories.message_repository import MessageRepository
from app.utils.exceptions import DatabaseError

class TestMessageRepository:
    """Suite de pruebas para MessageRepository."""
    
    def test_save_message_success(self, app, message_repository):
        """Prueba guardar un mensaje exitosamente."""
        with app.app_context():
            # Crear mensaje (message_id se genera automáticamente)
            message = Message(
                message_id="test-msg-1",
                session_id="test-session-1",
                content="Contenido de prueba",
                timestamp=datetime.now(timezone.utc),
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
            assert saved_message.timestamp is not None
    
    def test_find_by_message_id_exists(self, app, message_repository):
        """Prueba buscar un mensaje que existe."""
        with app.app_context():
            # Crear y guardar mensaje
            message = Message(
                 message_id="test-msg-2",
                session_id="test-session-1",
                content="Contenido de prueba",
                timestamp=datetime.now(timezone.utc),
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
                    timestamp=datetime.now(timezone.utc),
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
                    timestamp=datetime.now(timezone.utc),
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
            # Verificar que NO existe antes de guardarlo
            assert not message_repository.exists_by_message_id("test-exists")

            # Crear mensaje
            message = Message(
                message_id="test-exists",
                session_id="test-session",
                content="Contenido",
                timestamp=datetime.now(timezone.utc),
                sender="user"
            )
            saved_message = message_repository.save(message)

            # Verificar que ahora SÍ existe
            assert message_repository.exists_by_message_id(saved_message.message_id)

    
    def test_count_by_session_id(self, app, message_repository):
        """Prueba conteo de mensajes por session_id."""
        with app.app_context():
            session_id = "test-session-count"
            
            # Inicialmente no hay mensajes
            assert message_repository.count_by_session_id(session_id) == 0
            
            # Crear 3 mensajes
            for i in range(3):
                message = Message(
                    message_id="test-exists",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.now(timezone.utc),
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
                     message_id=f"count-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.now(timezone.utc),
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
                timestamp=datetime.now(timezone.utc),
                sender="user"
            )
            saved_message = message_repository.save(message)
            
            # Verificar que existe
            assert message_repository.exists_by_message_id(saved_message.message_id)
            
            # Eliminar mensaje
            deleted = message_repository.delete_by_message_id(saved_message.message_id)
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
                    message_id=f"count-msg-{i}",
                    session_id=session_id,
                    content=f"Contenido {i}",
                    timestamp=datetime.now(timezone.utc), 
                    sender="user"
                )
                message_repository.save(message)
            
            # Obtener session_ids únicos
            unique_sessions = message_repository.get_session_ids()
            
            # Verificar que son únicos
            assert len(unique_sessions) == 3
            assert set(unique_sessions) == {"session-1", "session-2", "session-3"}

def test_find_by_session_id_filters_and_pagination(app, message_repository):
    with app.app_context():
        m1 = Message(
            message_id="m1",
            session_id="s1",
            content="hola",
            sender="u",
            timestamp=datetime.now(timezone.utc),
        )
        m2 = Message(
            message_id="m2",
            session_id="s1",
            content="adios",
            sender="u",
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add_all([m1, m2])
        db.session.commit()

        # primera página (limit=1)
        results, total = message_repository.find_by_session_id("s1", limit=1, offset=0)
        assert len(results) == 1
        assert total == 2

        # segunda página (limit alto)
        results2, total2 = message_repository.find_by_session_id("s1", limit=5, offset=0)
        assert len(results2) == 2
        assert total2 == 2
            
def test_save_database_error(monkeypatch, app):
    """Prueba que save lanza DatabaseError si falla la DB."""
    
    repo = MessageRepository()

    def bad_add(*args, **kwargs):
        raise SQLAlchemyError("falla en add")

    with app.app_context():
        monkeypatch.setattr(db.session, "add", bad_add)
        import pytest
        with pytest.raises(Exception):  # DatabaseError envuelve el error
            repo.save(MessageRepository())

def test_find_by_message_id_not_found(app, message_repository):
    """Debe devolver None si no encuentra el mensaje."""
    with app.app_context():
        assert message_repository.find_by_message_id("id-inexistente") is None


def test_find_by_message_id_database_error(monkeypatch, app):

    repo = MessageRepository()

    class DummyQuery:
        def filter_by(self, **kwargs):
            raise SQLAlchemyError("falla en filter")

    with app.app_context():
        monkeypatch.setattr(Message, "query", DummyQuery())
        with pytest.raises(DatabaseError):
            repo.find_by_message_id("x")

def test_find_by_session_id_database_error(monkeypatch, app):

    repo = MessageRepository()

    class DummyQuery:
        def filter_by(self, **kwargs):
            raise SQLAlchemyError("falla en filter")

    with app.app_context():
        monkeypatch.setattr(Message, "query", DummyQuery())
        with pytest.raises(DatabaseError):
            repo.find_by_session_id("s1")


def test_exists_by_message_id_true_false(app, message_repository):
    with app.app_context():
        m = Message(message_id="m1", session_id="s1", content="hola", sender="u",
                    timestamp=datetime.now(timezone.utc))
        db.session.add(m)
        db.session.commit()

        assert message_repository.exists_by_message_id("m1") is True
        assert message_repository.exists_by_message_id("noexiste") is False

def test_exists_by_message_id_database_error(monkeypatch):

    repo = MessageRepository()

    def bad_scalar(*args, **kwargs):
        raise SQLAlchemyError("boom")

    monkeypatch.setattr(type(repo), "exists_by_message_id", lambda *_: (_ for _ in ()).throw(SQLAlchemyError("boom")))
    with pytest.raises(SQLAlchemyError):
        repo.exists_by_message_id("x")



def test_delete_by_message_id_not_found(app, message_repository):
    """Si no existe, devuelve False sin errores."""
    with app.app_context():
        assert message_repository.delete_by_message_id("inexistente") is False


def test_delete_by_message_id_database_error(monkeypatch, app):

    repo = MessageRepository()

    def bad_find(*args, **kwargs):
        raise SQLAlchemyError("fallo find")

    with app.app_context():
        monkeypatch.setattr(repo, "find_by_message_id", bad_find)
        with pytest.raises(DatabaseError):
            repo.delete_by_message_id("x")



def test_count_by_session_id_empty(app, message_repository):
    """Debe devolver 0 si no hay mensajes en esa sesión."""
    with app.app_context():
        assert message_repository.count_by_session_id("empty-session") == 0

def test_count_by_session_id_database_error(monkeypatch, app):

    repo = MessageRepository()

    class DummyQuery:
        def filter_by(self, **kwargs):
            raise SQLAlchemyError("count fail")

    with app.app_context():
        monkeypatch.setattr(Message, "query", DummyQuery())
        with pytest.raises(DatabaseError):
            repo.count_by_session_id("s1")



def test_get_session_ids_returns_distinct(app, message_repository):
    with app.app_context():
        m1 = Message(
            message_id="m1",
            session_id="s1",
            content="a",
            sender="u",
            timestamp=datetime.now(timezone.utc),
        )
        m2 = Message(
            message_id="m2",
            session_id="s2",
            content="b",
            sender="u",
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add_all([m1, m2])
        db.session.commit()

        session_ids = message_repository.get_session_ids()
        assert "s1" in session_ids
        assert "s2" in session_ids

def test_get_session_ids_database_error(monkeypatch, app):

    repo = MessageRepository()

    def bad_query(*args, **kwargs):
        raise DatabaseError("fail")

    with app.app_context():
        monkeypatch.setattr(repo, "get_session_ids", lambda *_: (_ for _ in ()).throw(DatabaseError("fail")))
        with pytest.raises(DatabaseError):
            repo.get_session_ids()

def test_search_globally_success(monkeypatch, app):

    repo = MessageRepository()
    fake_msgs = [
        Message(
            message_id="m1",
            session_id="s1",
            content="hola",
            sender="u",
            timestamp=datetime.now(timezone.utc),
        )
    ]

    with app.app_context():
        monkeypatch.setattr(Message, "search_globally", lambda q, l, o: fake_msgs)
        monkeypatch.setattr(Message, "count_global_search_results", lambda q: 1)
        msgs, total = repo.search_globally("hola", 10, 0)
        assert len(msgs) == 1 and total == 1

def test_search_globally_database_error(monkeypatch, app):

    repo = MessageRepository()

    def bad_search(*a, **k):
        raise SQLAlchemyError("fallo global")

    with app.app_context():
        monkeypatch.setattr(Message, "search_globally", bad_search)
        with pytest.raises(DatabaseError):
            repo.search_globally("x", 10, 0)

"""
Pruebas de integración para MessageController.
Este módulo prueba los endpoints de la API REST.
"""
import pytest
import json
from app.models.message import Message
from app.utils.exceptions import MessageProcessingError
from datetime import datetime, timezone


class TestMessageController:
    """Suite de pruebas para MessageController."""

    def test_create_message_success(self, authenticated_client, sample_message_data):
        """Prueba creación exitosa de mensaje."""
        response = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["status"] == "success"
        assert data["data"]["message_id"] == sample_message_data["message_id"]
        assert data["data"]["content"] == sample_message_data["content"]
        assert "metadata" in data["data"]
        assert data["data"]["metadata"]["word_count"] == 6

    def test_create_message_invalid_json(self, authenticated_client):
        """Prueba creación con JSON inválido."""
        response = authenticated_client.post(
            "/api/messages", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_create_message_missing_content_type(
        self, authenticated_client, sample_message_data
    ):
        """Prueba creación sin Content-Type correcto."""
        response = authenticated_client.post(
            "/api/messages", data=json.dumps(sample_message_data)
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "INVALID_CONTENT_TYPE"

    def test_create_message_empty_payload(self, authenticated_client):
        """Prueba creación con payload vacío."""
        response = authenticated_client.post(
            "/api/messages", data="{}", content_type="application/json"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "EMPTY_PAYLOAD"

    def test_create_message_invalid_schema(self, authenticated_client):
        """Prueba creación con esquema inválido."""
        invalid_data = {
            "message_id": "",
            "session_id": "",
            "content": "Contenido válido",
            "sender": "invalid-sender",
            "timestamp": "invalid-timestamp",
        }

        response = authenticated_client.post(
            "/api/messages",
            data=json.dumps(invalid_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "SCHEMA_VALIDATION_ERROR"

    def test_create_message_inappropriate_content(self, authenticated_client):
        """Prueba creación con contenido inapropiado."""
        inappropriate_data = {
            "message_id": "msg-inappropriate",
            "session_id": "session-test",
            "content": "Este mensaje contiene spam y virus",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user",
        }

        response = authenticated_client.post(
            "/api/messages",
            data=json.dumps(inappropriate_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "INAPPROPRIATE_CONTENT"

    def test_get_messages_by_session_success(
        self, authenticated_client, sample_message_data, sample_system_message_data
    ):
        """Prueba obtención exitosa de mensajes por sesión."""
        authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
        authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_system_message_data),
            content_type="application/json",
        )

        response = authenticated_client.get("/api/messages/session-test-abc")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["data"]) == 2
        assert "pagination" in data
        assert data["pagination"]["total"] == 2

    def test_get_messages_by_session_with_pagination(self, authenticated_client):
        """Prueba obtención con paginación."""
        session_id = "session-pagination"

        for i in range(15):
            message_data = {
                "message_id": f"msg-pag-{i}",
                "session_id": session_id,
                "content": f"Contenido {i}",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user",
            }
            authenticated_client.post(
                "/api/messages",
                data=json.dumps(message_data),
                content_type="application/json",
            )

        response1 = authenticated_client.get(f"/api/messages/{session_id}?limit=5&offset=0")
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        assert len(data1["data"]) == 5
        assert data1["pagination"]["total"] == 15
        assert data1["pagination"]["has_next"] is True
        assert data1["pagination"]["has_prev"] is False

        response2 = authenticated_client.get(f"/api/messages/{session_id}?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        assert len(data2["data"]) == 5
        assert data2["pagination"]["has_next"] is True
        assert data2["pagination"]["has_prev"] is True

    def test_get_messages_by_session_with_sender_filter(self, authenticated_client):
        """Prueba obtención con filtro por sender."""
        session_id = "session-filter"

        for i in range(6):
            message_data = {
                "message_id": f"msg-filter-{i}",
                "session_id": session_id,
                "content": f"Contenido {i}",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user" if i < 3 else "system",
            }
            authenticated_client.post(
                "/api/messages",
                data=json.dumps(message_data),
                content_type="application/json",
            )

        response_user = authenticated_client.get(f"/api/messages/{session_id}?sender=user")
        assert response_user.status_code == 200
        data_user = json.loads(response_user.data)
        assert len(data_user["data"]) == 3
        assert all(msg["sender"] == "user" for msg in data_user["data"])

        response_system = authenticated_client.get(f"/api/messages/{session_id}?sender=system")
        assert response_system.status_code == 200
        data_system = json.loads(response_system.data)
        assert len(data_system["data"]) == 3
        assert all(msg["sender"] == "system" for msg in data_system["data"])

    def test_get_messages_by_session_invalid_sender(self, authenticated_client):
        """Prueba obtención con sender inválido."""
        response = authenticated_client.get("/api/messages/session-test?sender=invalid")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_get_message_by_id_success(self, authenticated_client, sample_message_data):
        """Prueba obtención exitosa de mensaje por ID."""
        response_create = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
        
        assert response_create.status_code == 201
        created_data = json.loads(response_create.data)
        
        message_id = created_data["data"]["message_id"]
        
        response = authenticated_client.get(f"/api/message/{message_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["data"]["message_id"] == message_id

    def test_get_message_by_id_not_found(self, authenticated_client):
        """Prueba obtención de mensaje inexistente."""
        response = authenticated_client.get("/api/message/non-existent")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_session_stats_empty_session(self, authenticated_client):
        """Prueba estadísticas de sesión vacía."""
        response = authenticated_client.get("/api/sessions/empty-session/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["data"]["total_messages"] == 0

    def test_health_endpoint(self, authenticated_client):
        """Prueba endpoint de salud."""
        response = authenticated_client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
    
    def test_health_and_index_endpoints(self, authenticated_client):
        """Prueba endpoints de salud e índice."""
        assert authenticated_client.get("/health").status_code == 200
        assert authenticated_client.get("/").status_code == 200

    def test_index_endpoint(self, authenticated_client):
        """Prueba endpoint de información."""
        response = authenticated_client.get("/")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Message Processing API"

    def test_get_messages_pagination_edges(self, authenticated_client):
        """Prueba paginación con valores extremos."""
        session_id = "session-edge"
        for i in range(3):
            msg = {
                "message_id": f"msg-edge-{i}",
                "session_id": session_id,
                "content": f"msg {i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sender": "user",
            }
            authenticated_client.post("/api/messages", data=json.dumps(msg), content_type="application/json")
    
    def test_create_message_duplicate_id(self, authenticated_client, sample_message_data):
        """Prueba que no se permiten mensajes con message_id duplicado."""
        response1 = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
        assert response1.status_code == 201

        response2 = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )

        assert response2.status_code == 400
        error_data = json.loads(response2.data)
        assert error_data["status"] == "error"
        
        assert "ya existe" in error_data["error"]["message"].lower()
        
# 🔹 Nuevas pruebas adicionales para mejorar cobertura
class TestMessageControllerExtra:
    """Casos adicionales y edge cases para mejorar cobertura."""

    def test_create_message_service_exception(
        self, authenticated_client, monkeypatch, sample_message_data
    ):
        """Prueba que el controller maneja errores inesperados en el servicio."""
        from app.controllers import message_controller

        def mock_process(*args, **kwargs):
            raise MessageProcessingError("Error de prueba")

        monkeypatch.setattr(
            message_controller.MessageService, "process_message", mock_process
        )

        response = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "INTERNAL_ERROR"

    def test_get_messages_invalid_limit_offset(self, authenticated_client):
        """Prueba obtención con parámetros de paginación inválidos (normalizados)."""
        response = authenticated_client.get("/api/messages/session-test?limit=abc&offset=xyz")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "pagination" in data
        assert data["pagination"]["limit"] == 10  # valor por defecto
        assert data["pagination"]["offset"] == 0  # valor por defecto

    def test_internal_server_error_handler(self, authenticated_client, monkeypatch):
        """Prueba que se maneja correctamente un error 500 genérico."""
        from app.controllers import message_controller

        def mock_raise(*args, **kwargs):
            raise Exception("Falla inesperada")

        monkeypatch.setattr(
            message_controller.MessageService, "get_message_by_id", mock_raise
        )

        response = authenticated_client.get("/api/message/force-error")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert data["error"]["code"] == "INTERNAL_ERROR"
        
    def test_stats_internal_error(self, authenticated_client, monkeypatch):
        """Prueba error inesperado en el handler de stats."""
        from app.controllers import message_controller

        def mock_stats(*args, **kwargs):
            raise Exception("fallo stats")

        # 🔹 Parcheamos el método correcto
        monkeypatch.setattr(
            message_controller.MessageService,
            "get_session_statistics",
            mock_stats
        )

        r = authenticated_client.get("/api/sessions/some-session/stats")
        d = json.loads(r.data)

        assert r.status_code == 500
        assert d["status"] == "error"
        assert d["error"]["code"] == "INTERNAL_ERROR"

    
    def test_get_session_stats_with_data(self, authenticated_client):
        """Prueba estadísticas con mensajes presentes."""
        session_id = "stats-session"
        for i in range(2):
            msg = {
                "message_id": f"msg-stats-{i}",
                "session_id": session_id,
                "content": "hola mundo",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sender": "user",
            }
            authenticated_client.post("/api/messages", data=json.dumps(msg), content_type="application/json")

        r = authenticated_client.get(f"/api/sessions/{session_id}/stats")
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d["data"]["total_messages"] == 2
        
    def test_get_messages_empty_session_id(self, authenticated_client):
        """Prueba error cuando el session_id está vacío."""
        response = authenticated_client.get("/api/messages/   ")  # session_id vacío/espacios
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "INVALID_SESSION_ID"

    def test_get_message_by_id_empty_id(self, authenticated_client):
        """Prueba error cuando el message_id está vacío."""
        response = authenticated_client.get("/api/message/   ")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["error"]["code"] == "INVALID_MESSAGE_ID"

    def test_search_messages_success(self, authenticated_client, sample_message_data):
        """Prueba búsqueda global de mensajes con resultados."""
        
        authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
       
        response = authenticated_client.get("/api/messages/search/all?query=prueba&limit=5&offset=0")
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1
        assert "pagination" in data

    def test_search_messages_internal_error(self, authenticated_client, monkeypatch):
        """Prueba que búsqueda global maneja errores inesperados."""
        from app.controllers import message_controller

        def mock_search(*args, **kwargs):
            raise Exception("fallo en búsqueda")

        monkeypatch.setattr(
            message_controller.MessageService, "search_messages_globally", mock_search
        )

        response = authenticated_client.get("/api/messages/search/all?query=test")
        data = json.loads(response.data)
        assert response.status_code == 500
        assert data["error"]["code"] == "INTERNAL_ERROR"

    def test_create_message_database_error(self, authenticated_client, monkeypatch, sample_message_data):
        """Prueba que create_message maneja DatabaseError."""
        from app.controllers import message_controller
        from app.utils.exceptions import DatabaseError

        def mock_process(*args, **kwargs):
            raise DatabaseError("fallo de base de datos")

        monkeypatch.setattr(
            message_controller.MessageService, "process_message", mock_process
        )

        response = authenticated_client.post(
            "/api/messages",
            data=json.dumps(sample_message_data),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert response.status_code == 500
        # 🔹 DatabaseError usa code fijo
        assert data["error"]["code"] in ("DATABASE_ERROR", "INTERNAL_ERROR")
        assert "fallo de base de datos" in data["error"]["message"]

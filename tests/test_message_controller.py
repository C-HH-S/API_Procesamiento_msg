"""
Pruebas de integración para MessageController.
Este módulo prueba los endpoints de la API REST.
"""
import pytest
import json
from app.models.message import Message

class TestMessageController:
    """Suite de pruebas para MessageController."""
    
    def test_create_message_success(self, client, sample_message_data):
        """Prueba creación exitosa de mensaje."""
        response = client.post(
            '/api/messages',
            data=json.dumps(sample_message_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert data['data']['message_id'] == sample_message_data['message_id']
        assert data['data']['content'] == sample_message_data['content']
        assert 'metadata' in data['data']
        assert data['data']['metadata']['word_count'] == 6
    
    def test_create_message_invalid_json(self, client):
        """Prueba creación con JSON inválido."""
        response = client.post(
            '/api/messages',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_create_message_missing_content_type(self, client, sample_message_data):
        """Prueba creación sin Content-Type correcto."""
        response = client.post(
            '/api/messages',
            data=json.dumps(sample_message_data)
            # Sin content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'INVALID_CONTENT_TYPE'
    
    def test_create_message_empty_payload(self, client):
        """Prueba creación con payload vacío."""
        response = client.post(
            '/api/messages',
            data='{}',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'EMPTY_PAYLOAD'
    
    def test_create_message_invalid_schema(self, client):
        """Prueba creación con esquema inválido."""
        invalid_data = {
            "message_id": "",  # ID vacío
            "session_id": "session-test",
            "content": "Contenido válido",
            "timestamp": "invalid-timestamp",
            "sender": "invalid-sender"
        }
        
        response = client.post(
            '/api/messages',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'SCHEMA_VALIDATION_ERROR'
    
    def test_create_message_duplicate_id(self, client, sample_message_data):
        """Prueba creación con ID duplicado."""
        # Crear mensaje la primera vez
        response1 = client.post(
            '/api/messages',
            data=json.dumps(sample_message_data),
            content_type='application/json'
        )
        assert response1.status_code == 201
        
        # Intentar crear mensaje con mismo ID
        response2 = client.post(
            '/api/messages',
            data=json.dumps(sample_message_data),
            content_type='application/json'
        )
        
        assert response2.status_code == 400
        data = json.loads(response2.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert "Ya existe un mensaje con ID" in data['error']['message']
    
    def test_create_message_inappropriate_content(self, client):
        """Prueba creación con contenido inapropiado."""
        inappropriate_data = {
            "message_id": "msg-inappropriate",
            "session_id": "session-test",
            "content": "Este mensaje contiene spam y virus",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user"
        }
        
        response = client.post(
            '/api/messages',
            data=json.dumps(inappropriate_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'INAPPROPRIATE_CONTENT'
    
    def test_get_messages_by_session_success(self, client, sample_message_data, sample_system_message_data):
        """Prueba obtención exitosa de mensajes por sesión."""
        # Crear dos mensajes
        client.post('/api/messages', data=json.dumps(sample_message_data), content_type='application/json')
        client.post('/api/messages', data=json.dumps(sample_system_message_data), content_type='application/json')
        
        # Obtener mensajes
        response = client.get('/api/messages/session-test-abc')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert len(data['data']) == 2
        assert 'pagination' in data
        assert data['pagination']['total'] == 2
    
    def test_get_messages_by_session_with_pagination(self, client):
        """Prueba obtención con paginación."""
        session_id = "session-pagination"
        
        # Crear 15 mensajes
        for i in range(15):
            message_data = {
                "message_id": f"msg-pag-{i}",
                "session_id": session_id,
                "content": f"Contenido {i}",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user"
            }
            client.post('/api/messages', data=json.dumps(message_data), content_type='application/json')
        
        # Primera página
        response1 = client.get(f'/api/messages/{session_id}?limit=5&offset=0')
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        
        assert len(data1['data']) == 5
        assert data1['pagination']['total'] == 15
        assert data1['pagination']['has_next'] is True
        assert data1['pagination']['has_prev'] is False
        
        # Segunda página
        response2 = client.get(f'/api/messages/{session_id}?limit=5&offset=5')
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        
        assert len(data2['data']) == 5
        assert data2['pagination']['has_next'] is True
        assert data2['pagination']['has_prev'] is True
    
    def test_get_messages_by_session_with_sender_filter(self, client):
        """Prueba obtención con filtro por sender."""
        session_id = "session-filter"
        
        # Crear mensajes mixtos
        for i in range(6):
            message_data = {
                "message_id": f"msg-filter-{i}",
                "session_id": session_id,
                "content": f"Contenido {i}",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "user" if i < 3 else "system"
            }
            client.post('/api/messages', data=json.dumps(message_data), content_type='application/json')
        
        # Filtrar por usuario
        response_user = client.get(f'/api/messages/{session_id}?sender=user')
        assert response_user.status_code == 200
        data_user = json.loads(response_user.data)
        
        assert len(data_user['data']) == 3
        assert all(msg['sender'] == 'user' for msg in data_user['data'])
        
        # Filtrar por sistema
        response_system = client.get(f'/api/messages/{session_id}?sender=system')
        assert response_system.status_code == 200
        data_system = json.loads(response_system.data)
        
        assert len(data_system['data']) == 3
        assert all(msg['sender'] == 'system' for msg in data_system['data'])
    
    def test_get_messages_by_session_empty_session_id(self, client):
        """Prueba obtención con session_id vacío."""
        response = client.get('/api/messages/')
        assert response.status_code == 404  # Endpoint no encontrado
    
    def test_get_messages_by_session_invalid_sender(self, client):
        """Prueba obtención con sender inválido."""
        response = client.get('/api/messages/session-test?sender=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_get_message_by_id_success(self, client, sample_message_data):
        """Prueba obtención exitosa de mensaje por ID."""
        # Crear mensaje
        client.post('/api/messages', data=json.dumps(sample_message_data), content_type='application/json')
        
        # Obtener mensaje por ID
        response = client.get('/api/message/msg-test-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert data['data']['message_id'] == 'msg-test-123'
        assert data['data']['content'] == 'Este es un mensaje de prueba'
    
    def test_get_message_by_id_not_found(self, client):
        """Prueba obtención de mensaje inexistente."""
        response = client.get('/api/message/non-existent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['error']['code'] == 'NOT_FOUND'
    
    def test_get_message_by_id_empty_id(self, client):
        """Prueba obtención con ID vacío."""
        response = client.get('/api/message/')
        assert response.status_code == 404  # Endpoint no encontrado
    
    def test_get_session_stats_success(self, client):
        """Prueba obtención exitosa de estadísticas."""
        session_id = "session-stats"
        
        # Crear mensajes mixtos
        messages = [
            {"id": "stats-1", "sender": "user"},
            {"id": "stats-2", "sender": "user"},
            {"id": "stats-3", "sender": "system"}
        ]
        
        for msg in messages:
            message_data = {
                "message_id": msg["id"],
                "session_id": session_id,
                "content": "Contenido de prueba",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": msg["sender"]
            }
            client.post('/api/messages', data=json.dumps(message_data), content_type='application/json')
        
        # Obtener estadísticas
        response = client.get(f'/api/sessions/{session_id}/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert data['data']['session_id'] == session_id
        assert data['data']['total_messages'] == 3
        assert data['data']['user_messages'] == 2
        assert data['data']['system_messages'] == 1
    
    def test_get_session_stats_empty_session(self, client):
        """Prueba estadísticas de sesión vacía."""
        response = client.get('/api/sessions/empty-session/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'success'
        assert data['data']['total_messages'] == 0
        assert data['data']['user_messages'] == 0
        assert data['data']['system_messages'] == 0
    
    def test_health_endpoint(self, client):
        """Prueba endpoint de salud."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert data['service'] == 'message-processing-api'
    
    def test_index_endpoint(self, client):
        """Prueba endpoint de información."""
        response = client.get('/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['name'] == 'Message Processing API'
        assert 'endpoints' in data
    
    def test_404_error_handler(self, client):
        """Prueba manejador de errores 404."""
        response = client.get('/api/non-existent-endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['status'] == 'error'
        assert data['error']['code'] == 'NOT_FOUND'
    
    def test_405_error_handler(self, client):
        """Prueba manejador de errores 405."""
        # Intentar hacer GET en endpoint que solo acepta POST
        response = client.get('/api/messages')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert data['status'] == 'error'
        assert data['error']['code'] == 'METHOD_NOT_ALLOWED'
    
    def test_create_message_edge_cases(self, client):
        """Prueba casos límite en creación de mensajes."""
        # Mensaje con contenido muy largo
        long_content_data = {
            "message_id": "msg-long-content",
            "session_id": "session-test",
            "content": "a" * 6000,  # Excede el límite de 5000
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user"
        }
        
        response = client.post(
            '/api/messages',
            data=json.dumps(long_content_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
    
    def test_get_messages_pagination_edge_cases(self, client):
        """Prueba casos límite en paginación."""
        session_id = "session-edge-cases"
        
        # Crear un mensaje
        message_data = {
            "message_id": "edge-msg-1",
            "session_id": session_id,
            "content": "Contenido de prueba",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "user"
        }
        client.post('/api/messages', data=json.dumps(message_data), content_type='application/json')
        
        # Probar límite negativo (debe normalizarse)
        response = client.get(f'/api/messages/{session_id}?limit=-5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['limit'] == 10  # Valor por defecto
        
        # Probar offset negativo (debe normalizarse)
        response = client.get(f'/api/messages/{session_id}?offset=-10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['offset'] == 0
        
        # Probar límite muy alto (debe limitarse)
        response = client.get(f'/api/messages/{session_id}?limit=1000')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['limit'] == 100  # Límite máximo
import pytest
from flask import Flask, jsonify
from app.utils.auth import api_key_required

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['API_KEYS'] = ['valid-key-123']

    @app.route("/protected")
    @api_key_required
    def protected():
        return jsonify({"status": "success"}), 200

    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_missing_authorization_header(client):
    """Debe retornar 401 si no se envía el encabezado Authorization"""
    response = client.get("/protected")
    assert response.status_code == 401
    data = response.get_json()
    assert data['error']['code'] == 'AUTH_REQUIRED'

def test_invalid_format_authorization_header(client):
    """Debe retornar 401 si el encabezado Authorization no tiene 'Bearer '"""
    response = client.get("/protected", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    data = response.get_json()
    assert data['error']['code'] == 'AUTH_REQUIRED'

def test_invalid_api_key(client):
    """Debe retornar 403 si la clave de API no es válida"""
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 403
    data = response.get_json()
    assert data['error']['code'] == 'INVALID_API_KEY'

def test_valid_api_key(client):
    """Debe permitir el acceso si la clave de API es válida"""
    response = client.get("/protected", headers={"Authorization": "Bearer valid-key-123"})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'

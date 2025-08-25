"""
Mecanismo de autenticación para la API.
Este módulo contiene el decorador para proteger los endpoints.
"""
from functools import wraps
from flask import request, jsonify, current_app

def api_key_required(f):
    """
    Decorador para requerir una clave de API válida en las peticiones.
    La clave se debe pasar en el encabezado 'Authorization' como 'Bearer <api_key>'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Obtener el encabezado de autorización
        auth_header = request.headers.get('Authorization')

        # 2. Verificar si el encabezado existe y tiene el formato correcto
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'AUTH_REQUIRED',
                    'message': 'Encabezado de autorización "Bearer" es requerido.'
                }
            }), 401

        # 3. Extraer la clave de API del encabezado
        api_key = auth_header.split(' ')[1]

        # 4. Verificar la clave contra la lista de claves válidas
        if api_key not in current_app.config.get('API_KEYS', []):
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'INVALID_API_KEY',
                    'message': 'Clave de API inválida.'
                }
            }), 403

        # 5. Si la clave es válida, continuar con la función original
        return f(*args, **kwargs)

    return decorated_function
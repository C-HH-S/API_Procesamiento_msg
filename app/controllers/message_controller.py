"""
Controladores para la API de mensajes
Este módulo maneja las peticiones HTTP y coordina las respuestas.
"""
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError as MarshmallowValidationError
from typing import Tuple
import json
import traceback
from app import limiter
from werkzeug.exceptions import BadRequest
from app.utils.auth import api_key_required
from app.controllers.realtime_controller import broadcast_new_message
from flask import current_app

from app.services.message_service import MessageService
from app.schemas.message_schema import (
    message_input_schema, 
    message_response_schema, 
    message_list_response_schema,
    error_response_schema
)
from app.utils.exceptions import (
    MessageProcessingError, 
    ValidationError, 
    InvalidFormatError, 
    InappropriateContentError,
    MessageNotFoundError,
    DatabaseError
)

class MessageController:
    """Controlador para operaciones de mensajes."""
    
    def __init__(self, message_service: MessageService):
        """
        Inicializa el controlador.
        
        Args:
            message_service: Servicio de procesamiento de mensajes
        """
        self.message_service = message_service
        self.blueprint = Blueprint('messages', __name__, url_prefix='/api')
        self._register_routes()
    
    def _register_routes(self):
        """Registra las rutas del controlador."""
        self.blueprint.route('/messages', methods=['POST'])(
            limiter.limit(lambda: current_app.config.get("RATELIMIT_DEFAULT", "100 per hour"))(self.create_message)
        )

        self.blueprint.route('/messages/<session_id>', methods=['GET'])(
            api_key_required(self.get_messages_by_session)
        )

        self.blueprint.route('/message/<message_id>', methods=['GET'])(
            api_key_required(self.get_message_by_id)
        )

        self.blueprint.route('/sessions/<session_id>/stats', methods=['GET'])(
            api_key_required(self.get_session_stats)
        )

        self.blueprint.route('/messages/search/all', methods=['GET'])(
            api_key_required(self.search_messages_globally)
        ) 
    
    def create_message(self) -> Tuple[dict, int]:
        """
        Endpoint POST /api/messages
        Crea un nuevo mensaje.
        """
        try:
            # 1. Validar que el contenido sea JSON
            if not request.is_json:
                return self._error_response(
                    "INVALID_CONTENT_TYPE",
                    "Content-Type debe ser application/json"
                ), 400
            
            # 2. Obtener datos de la petición con manejo de JSON inválido
            try:
                json_data = request.get_json()
            except (json.JSONDecodeError, BadRequest) as e:
                return self._error_response(
                    "INVALID_JSON",
                    "JSON malformado en el cuerpo de la petición"
                ), 400
            
            if not json_data:
                return self._error_response(
                    "EMPTY_PAYLOAD",
                    "El cuerpo de la petición está vacío"
                ), 400
            
            # 3. Validar esquema con Marshmallow
            try:
                validated_data = message_input_schema.load(json_data)
            except MarshmallowValidationError as e:
                return self._error_response(
                    "SCHEMA_VALIDATION_ERROR",
                    "Errores de validación de esquema",
                    e.messages
                ), 400
            
            # 4. Procesar mensaje a través del servicio
            processed_message = self.message_service.process_message(validated_data)
            
            # 5. Preparar respuesta exitosa
            # Transmitir el nuevo mensaje a través del WebSocket
            broadcast_new_message(processed_message)
            response_data = {
                'status': 'success',
                'data': processed_message
            }
            
            return response_data, 201
        
        except BadRequest as e:
            # Captura específicamente los errores BadRequest de Flask/Werkzeug
            return self._error_response(
                "INVALID_JSON",
                "JSON malformado en el cuerpo de la petición"
            ), 400
        
        except ValidationError as e:
            return self._error_response(e.code, e.message, getattr(e, 'details', None)), e.status_code
        except InvalidFormatError as e:
            return self._error_response(e.code, e.message, getattr(e, 'details', None)), e.status_code
        except InappropriateContentError as e:
            return self._error_response(e.code, e.message, getattr(e, 'details', None)), e.status_code
        except DatabaseError as e:
            return self._error_response(e.code, e.message), 500
        except Exception as e:
            # Log del error para debugging
            print(f"Error inesperado en create_message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return self._error_response(
                "INTERNAL_ERROR",
                f"Error interno del servidor: {str(e)}"
            ), 500
    
    def get_messages_by_session(self, session_id: str) -> Tuple[dict, int]:
        """
        Endpoint GET /api/messages/<session_id>
        Obtiene mensajes por session_id con paginación.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            # 1. Obtener parámetros de query
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            sender = request.args.get('sender', None, type=str)
            
            # 2. Validar session_id
            if not session_id or not session_id.strip():
                return self._error_response(
                    "INVALID_SESSION_ID",
                    "session_id no puede estar vacío"
                ), 400
            
            # 3. Obtener mensajes del servicio
            result = self.message_service.get_messages_by_session(
                session_id, limit, offset, sender
            )
            
            # 4. Preparar respuesta
            response_data = {
                'status': 'success',
                'data': result['messages'],
                'pagination': result['pagination']
            }
            
            return response_data, 200
            
        except ValidationError as e:
            return self._error_response(e.code, e.message, getattr(e, 'details', None)), e.status_code
        except DatabaseError as e:
            return self._error_response(e.code, e.message), 500
        except Exception as e:
            print(f"Error inesperado en get_messages_by_session: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return self._error_response(
                "INTERNAL_ERROR",
                f"Error interno del servidor: {str(e)}"
            ), 500
    
    def get_message_by_id(self, message_id: str) -> Tuple[dict, int]:
        """
        Endpoint GET /api/message/<message_id>
        Obtiene un mensaje específico por ID.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            # 1. Validar message_id
            if not message_id or not message_id.strip():
                return self._error_response(
                    "INVALID_MESSAGE_ID",
                    "message_id no puede estar vacío"
                ), 400
            
            # 2. Obtener mensaje del servicio
            message_data = self.message_service.get_message_by_id(message_id)
            
            # 3. Preparar respuesta
            response_data = {
                'status': 'success',
                'data': message_data
            }
            
            return response_data, 200
            
        except MessageNotFoundError as e:
            return self._error_response(e.code, e.message), e.status_code
        except DatabaseError as e:
            return self._error_response(e.code, e.message), 500
        except Exception as e:
            print(f"Error inesperado en get_message_by_id: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return self._error_response(
                "INTERNAL_ERROR",
                f"Error interno del servidor: {str(e)}"
            ), 500
    
    def get_session_stats(self, session_id: str) -> Tuple[dict, int]:
        """
        Endpoint GET /api/sessions/<session_id>/stats
        Obtiene estadísticas de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            tuple: (response_data, status_code)
        """
        try:
            # 1. Validar session_id
            if not session_id or not session_id.strip():
                return self._error_response(
                    "INVALID_SESSION_ID",
                    "session_id no puede estar vacío"
                ), 400
            
            # 2. Obtener estadísticas del servicio
            stats = self.message_service.get_session_statistics(session_id)
            
            # 3. Preparar respuesta
            response_data = {
                'status': 'success',
                'data': stats
            }
            
            return response_data, 200
            
        except DatabaseError as e:
            return self._error_response(e.code, e.message), 500
        except Exception as e:
            print(f"Error inesperado en get_session_stats: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return self._error_response(
                "INTERNAL_ERROR",
                f"Error interno del servidor: {str(e)}"
            ), 500
    
    def _error_response(self, code: str, message: str, details=None) -> dict:
        """
        Crea una respuesta de error estandarizada.
        
        Args:
            code: Código del error
            message: Mensaje descriptivo
            details: Detalles adicionales del error
            
        Returns:
            dict: Respuesta de error formateada
        """
        return {
            'status': 'error',
            'error': {
                'code': code,
                'message': message,
                'details': details
            }
        }
        
    
    def search_messages_globally(self) -> Tuple[dict, int]:
        """Maneja la petición GET para buscar mensajes por contenido en todas las sesiones."""
        try:
            query = request.args.get('query')
            
            # Obtener parámetros de paginación
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))

            # Obtener resultados del servicio
            results = self.message_service.search_messages_globally(query, limit, offset)
            
            # Serializar y devolver la respuesta
            return message_list_response_schema.dump(results), 200

        except ValidationError as e:
            return self._error_response(e.code, e.message, e.details), 400
        except Exception as e:
            print(f"Error inesperado en search_messages_globally: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return self._error_response(
                "INTERNAL_ERROR",
                f"Error interno del servidor: {str(e)}"
            ), 500
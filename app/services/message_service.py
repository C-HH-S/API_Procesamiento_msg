"""
Lógica de negocio para el procesamiento de mensajes - Versión corregida.
Este módulo contiene toda la lógica de negocio para el manejo de mensajes.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.utils.validators import MessageValidator, ContentFilter, PaginationValidator
from app.utils.exceptions import ValidationError, InvalidFormatError, InappropriateContentError, MessageNotFoundError

class MessageService:
    """Servicio para procesamiento de mensajes."""
    
    def __init__(self, message_repository: MessageRepository, inappropriate_words: List[str]):
        """
        Inicializa el servicio de mensajes.
        
        Args:
            message_repository: Repositorio para operaciones de base de datos
            inappropriate_words: Lista de palabras inapropiadas para filtrado
        """
        self.message_repository = message_repository
        self.inappropriate_words = inappropriate_words
    
    def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje completo: valida, filtra, procesa y almacena.
        
        Args:
            message_data: Datos del mensaje a procesar
            
        Returns:
            Dict: Mensaje procesado con metadatos
            
        Raises:
            ValidationError: Si los datos son inválidos
            InvalidFormatError: Si el formato es incorrecto
            InappropriateContentError: Si contiene contenido inapropiado
            MessageProcessingError: Si el message_id ya existe
        """
        # 1. Validar campos básicos requeridos
        self._validate_basic_fields(message_data)
        
        # 2. Verificar si el message_id ya existe (solo si se proporciona)
        if message_data.get('message_id') and self.message_repository.exists_by_message_id(message_data['message_id']):
            raise ValidationError(f"Ya existe un mensaje con ID: {message_data['message_id']}")
        
        # 3. Filtrar contenido inapropiado
        ContentFilter.check_inappropriate_content(
            message_data['content'], 
            self.inappropriate_words
        )
        
        # 4. Crear mensaje con metadatos calculados automáticamente
        message = self._create_message_from_data(message_data)
        
        # 5. Guardar mensaje
        saved_message = self.message_repository.save(message)
        
        # 6. Retornar mensaje procesado
        return saved_message.to_dict()
    
    def _validate_basic_fields(self, data: Dict[str, Any]) -> None:
        """
        Valida los campos básicos requeridos.
        
        Args:
            data: Diccionario con los datos del mensaje
            
        Raises:
            ValidationError: Si faltan campos requeridos
            InvalidFormatError: Si el formato es inválido
        """
        # Campos requeridos (sin message_id porque se genera automáticamente)
        required_fields = ['session_id', 'content', 'sender']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            raise ValidationError(
                f"Campos requeridos faltantes: {', '.join(missing_fields)}",
                details={"missing_fields": missing_fields}
            )
        
        # Validar tipos y formatos
        MessageValidator.validate_session_id(data['session_id'])
        MessageValidator.validate_content(data['content'])
        MessageValidator.validate_sender(data['sender'])
        
        # Validar message_id solo si se proporciona
        if data.get('message_id'):
            MessageValidator.validate_message_id(data['message_id'])
    
    def get_messages_by_session(
        self, 
        session_id: str, 
        limit: int = 10, 
        offset: int = 0, 
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene mensajes por session_id con paginación.
        
        Args:
            session_id: ID de la sesión
            limit: Límite de resultados por página
            offset: Desplazamiento para paginación  
            sender: Filtro opcional por remitente
            
        Returns:
            Dict: Respuesta con mensajes y metadatos de paginación
            
        Raises:
            ValidationError: Si los parámetros son inválidos
        """
        # Validar parámetros de paginación
        limit, offset = PaginationValidator.validate_pagination_params(limit, offset, 100)
        
        # Validar sender si se proporciona
        if sender and sender not in MessageValidator.VALID_SENDERS:
            raise ValidationError(f"sender debe ser uno de: {MessageValidator.VALID_SENDERS}")
        
        # Obtener mensajes y total
        messages, total_count = self.message_repository.find_by_session_id(
            session_id, limit, offset, sender
        )
        
        # Preparar respuesta
        return {
            'messages': [message.to_dict() for message in messages],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': (offset + limit) < total_count,
                'has_prev': offset > 0
            }
        }
    
    def get_message_by_id(self, message_id: str) -> Dict[str, Any]:
        """
        Obtiene un mensaje por su ID.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Dict: Datos del mensaje
            
        Raises:
            MessageNotFoundError: Si el mensaje no existe
        """
        message = self.message_repository.find_by_message_id(message_id)
        if not message:
            raise MessageNotFoundError(f"No se encontró mensaje con ID: {message_id}")
        
        return message.to_dict()
    
    def _create_message_from_data(self, message_data: Dict[str, Any]) -> Message:
        """
        Crea una instancia de Message desde los datos.
        
        Args:
            message_data: Datos del mensaje
            
        Returns:
            Message: Instancia del mensaje
        """
        # Parsear timestamp si se proporciona
        timestamp = None
        if message_data.get('timestamp'):
            timestamp = MessageValidator.validate_timestamp(message_data['timestamp'])
        
        # Crear mensaje (el constructor se encarga de generar automáticamente
        # los campos que no se proporcionen)
        message = Message(
            session_id=message_data['session_id'],
            content=message_data['content'],
            sender=message_data['sender'],
            message_id=message_data.get('message_id'),  # Puede ser None
            timestamp=timestamp  # Puede ser None
        )
        
        return message
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict: Estadísticas de la sesión
        """
        total_messages = self.message_repository.count_by_session_id(session_id)
        user_messages = self.message_repository.count_by_session_id(session_id, 'user')
        system_messages = self.message_repository.count_by_session_id(session_id, 'system')
        
        return {
            'session_id': session_id,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'system_messages': system_messages
        }
    
    def search_messages_globally(self, query: str, limit: int, offset: int) -> Dict[str, Any]:
        """
        Busca mensajes globalmente y devuelve resultados paginados.
        
        Args:
            query: Texto de búsqueda.
            limit: Límite de resultados por página.
            offset: Desplazamiento.
            
        Returns:
            Dict: Un diccionario con los mensajes y datos de paginación.
            
        Raises:
            ValidationError: Si la consulta es inválida.
        """
        # Validar la consulta de búsqueda
        if not query or len(query.strip()) < 3:
            raise ValidationError(
                "La consulta de búsqueda debe tener al menos 3 caracteres.",
                code="SEARCH_QUERY_TOO_SHORT"
            )
        
        # Validar y normalizar parámetros de paginación
        limit, offset = PaginationValidator.validate_pagination_params(
            limit, offset, max_limit=100
        )

        messages, total_results = self.message_repository.search_globally(
            query, limit, offset
        )

        next_offset = offset + limit if (offset + limit) < total_results else None

        return {
            "data": [msg.to_dict() for msg in messages],
            "pagination": {
                "total_results": total_results,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset
            }
        }
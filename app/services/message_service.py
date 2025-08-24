"""
Lógica de negocio para el procesamiento de mensajes.
Este módulo contiene toda la lógica de negocio para el manejo de mensajes.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

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
        # 1. Validar formato del mensaje
        MessageValidator.validate_message_data(message_data)
        
        # 2. Verificar si el message_id ya existe
        if self.message_repository.exists_by_message_id(message_data['message_id']):
            raise ValidationError(f"Ya existe un mensaje con ID: {message_data['message_id']}")
        
        # 3. Filtrar contenido inapropiado
        ContentFilter.check_inappropriate_content(
            message_data['content'], 
            self.inappropriate_words
        )
        
        # 4. Procesar y agregar metadatos
        processed_data = self._add_metadata(message_data)
        
        # 5. Crear y guardar el mensaje
        message = self._create_message_from_data(processed_data)
        saved_message = self.message_repository.save(message)
        
        # 6. Retornar mensaje procesado
        return saved_message.to_dict()
    
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
        
        # Si no hay mensajes, no es necesariamente un error
        # Puede ser una sesión nueva o sin mensajes que coincidan con los filtros
        
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
    
    def _add_metadata(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega metadatos al mensaje.
        
        Args:
            message_data: Datos originales del mensaje
            
        Returns:
            Dict: Datos del mensaje con metadatos agregados
        """
        content = message_data['content']
        
        # Calcular metadatos
        word_count = len(content.split()) if content.strip() else 0
        character_count = len(content)
        
        # Crear copia de los datos originales
        processed_data = message_data.copy()
        
        # Agregar metadatos
        processed_data.update({
            'word_count': word_count,
            'character_count': character_count,
            'processed_at': datetime.utcnow()
        })
        
        return processed_data
    
    def _create_message_from_data(self, processed_data: Dict[str, Any]) -> Message:
        """
        Crea una instancia de Message desde los datos procesados.
        
        Args:
            processed_data: Datos del mensaje con metadatos
            
        Returns:
            Message: Instancia del mensaje
        """
        # Parsear timestamp
        timestamp = MessageValidator.validate_timestamp(processed_data['timestamp'])
        
        # Crear mensaje
        message = Message(
            message_id=processed_data['message_id'],
            session_id=processed_data['session_id'],
            content=processed_data['content'],
            timestamp=timestamp,
            sender=processed_data['sender'],
            word_count=processed_data['word_count'],
            character_count=processed_data['character_count']
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
"""
Validadores para la aplicación.
Este módulo contiene funciones de validación para mensajes y otros datos.
"""
import re
from typing import Dict, List, Any
from .exceptions import ValidationError, InvalidFormatError, InappropriateContentError

class MessageValidator:
    """Validador para mensajes de chat."""
    
    VALID_SENDERS = ['user', 'system']
    
    @staticmethod
    def validate_message_data(data: Dict[str, Any]) -> None:
        """
        Valida los datos completos de un mensaje.
        
        Args:
            data: Diccionario con los datos del mensaje
            
        Raises:
            ValidationError: Si faltan campos requeridos
            InvalidFormatError: Si el formato es inválido
        """
        # Validar campos requeridos
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
    
    @staticmethod
    def validate_session_id(session_id: str) -> None:
        """Valida el ID de sesión."""
        if not isinstance(session_id, str) or not session_id.strip():
            raise InvalidFormatError("session_id debe ser una cadena no vacía")
        
        if len(session_id) > 255:
            raise InvalidFormatError("session_id no puede exceder 255 caracteres")
    
    @staticmethod
    def validate_content(content: str) -> None:
        """Valida el contenido del mensaje."""
        if not isinstance(content, str):
            raise InvalidFormatError("content debe ser una cadena")
        
        if len(content.strip()) == 0:
            raise InvalidFormatError("content no puede estar vacío")
        
        if len(content) > 5000:
            raise InvalidFormatError("content no puede exceder 5000 caracteres")
    
    @staticmethod
    def validate_sender(sender: str) -> None:
        """Valida el remitente del mensaje."""
        if not isinstance(sender, str):
            raise InvalidFormatError("sender debe ser una cadena")
        
        if sender not in MessageValidator.VALID_SENDERS:
            raise InvalidFormatError(
                f"El campo 'sender' debe ser 'user' o 'system'",
                details={"valid_senders": MessageValidator.VALID_SENDERS}
            )

class ContentFilter:
    """Filtro de contenido para mensajes."""
    
    @staticmethod
    def check_inappropriate_content(content: str, inappropriate_words: List[str]) -> None:
        """
        Verifica si el contenido contiene palabras inapropiadas.
        
        Args:
            content: Contenido a verificar
            inappropriate_words: Lista de palabras inapropiadas
            
        Raises:
            InappropriateContentError: Si se encuentra contenido inapropiado
        """
        content_lower = content.lower()
        found_words = []
        
        for word in inappropriate_words:
            if word.lower() in content_lower:
                found_words.append(word)
        
        if found_words:
            raise InappropriateContentError(
                "El mensaje contiene contenido inapropiado",
                details={"inappropriate_words_found": found_words}
            )

class PaginationValidator:
    """Validador para parámetros de paginación."""
    
    @staticmethod
    def validate_pagination_params(limit: int, offset: int, max_limit: int = 100) -> tuple:
        """
        Valida y normaliza parámetros de paginación.
        
        Returns:
            tuple: (limit, offset) validados
        """
        # Validar limit
        if limit < 1:
            limit = 10  # valor por defecto
        elif limit > max_limit:
            limit = max_limit
        
        # Validar offset
        if offset < 0:
            offset = 0
        
        return limit, offset
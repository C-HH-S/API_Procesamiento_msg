"""
Excepciones personalizadas para la aplicación.
Este módulo define las excepciones específicas del dominio de negocio.
"""

class MessageProcessingError(Exception):
    """Excepción base para errores de procesamiento de mensajes."""
    
    def __init__(self, message, code=None, status_code=400):
        super().__init__(message)
        self.message = message
        self.code = code or 'PROCESSING_ERROR'
        self.status_code = status_code

class ValidationError(MessageProcessingError):
    """Excepción para errores de validación."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 'VALIDATION_ERROR', 400)
        self.details = details

class InvalidFormatError(MessageProcessingError):
    """Excepción para errores de formato inválido."""
    
    def __init__(self, message, details=None):
        super().__init__(message, 'INVALID_FORMAT', 400)
        self.details = details

class InappropriateContentError(MessageProcessingError):
    """Excepción para contenido inapropiado."""
    
    def __init__(self, message="El mensaje contiene contenido inapropiado", details=None):
        super().__init__(message, 'INAPPROPRIATE_CONTENT', 400)
        self.details = details

class MessageNotFoundError(MessageProcessingError):
    """Excepción para cuando no se encuentra un mensaje o sesión."""
    
    def __init__(self, message="Mensaje o sesión no encontrada"):
        super().__init__(message, 'NOT_FOUND', 404)

class DatabaseError(MessageProcessingError):
    """Excepción para errores de base de datos."""
    
    def __init__(self, message="Error en la base de datos"):
        super().__init__(message, 'DATABASE_ERROR', 500)
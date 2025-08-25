"""
Esquemas de serialización para la API
Este módulo define los esquemas de validación y serialización usando Marshmallow.
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime

class MessageInputSchema(Schema):
    """Esquema para validar entrada de mensajes."""
    
    # Todos los campos son ahora obligatorios
    message_id = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    session_id = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    content = fields.Str(required=True, validate=validate.Length(min=1, max=5000))
    sender = fields.Str(required=True, validate=validate.OneOf(['user', 'system']))
    timestamp = fields.Str(required=True)
    
    @validates_schema
    def validate_timestamp(self, data, **kwargs):
        """Valida que el timestamp sea un formato ISO válido."""
        timestamp_str = data.get('timestamp', '')
        if not timestamp_str:
            raise ValidationError("timestamp es requerido")
        
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            raise ValidationError("timestamp debe estar en formato ISO 8601 (ej: 2023-06-15T14:30:00Z)")


class MessageMetadataSchema(Schema):
    """Esquema para metadatos del mensaje."""
    
    word_count = fields.Int(dump_only=True)
    character_count = fields.Int(dump_only=True)
    processed_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)

class MessageOutputSchema(Schema):
    """Esquema para salida de mensajes."""
    
    message_id = fields.Str()
    session_id = fields.Str()
    content = fields.Str()
    timestamp = fields.Str()
    sender = fields.Str()
    metadata = fields.Nested(MessageMetadataSchema)

class MessageResponseSchema(Schema):
    """Esquema para respuestas exitosas."""
    
    status = fields.Str(dump_default='success')
    data = fields.Nested(MessageOutputSchema)

class MessageListResponseSchema(Schema):
    """Esquema para respuestas de lista de mensajes."""
    
    status = fields.Str(dump_default='success')
    data = fields.List(fields.Nested(MessageOutputSchema))
    pagination = fields.Dict()

class ErrorDetailSchema(Schema):
    """Esquema para detalles de error."""
    
    code = fields.Str()
    message = fields.Str()
    details = fields.Raw(allow_none=True)

class ErrorResponseSchema(Schema):
    """Esquema para respuestas de error."""
    
    status = fields.Str(dump_default='error')
    error = fields.Nested(ErrorDetailSchema)

# Instancias de esquemas para reutilizar
message_input_schema = MessageInputSchema()
message_output_schema = MessageOutputSchema()
message_response_schema = MessageResponseSchema()
message_list_response_schema = MessageListResponseSchema()
error_response_schema = ErrorResponseSchema()
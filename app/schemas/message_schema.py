"""
Esquemas de serialización para la API - Versión simplificada.
Este módulo define los esquemas de validación y serialización usando Marshmallow.
"""
from marshmallow import Schema, fields, validate

class MessageInputSchema(Schema):
    """Esquema para validar entrada de mensajes."""
    
    # message_id es opcional, se genera automáticamente si no se proporciona
    message_id = fields.Str(validate=validate.Length(min=1, max=255), allow_none=True, missing=None)
    session_id = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    content = fields.Str(required=True, validate=validate.Length(min=1, max=5000))
    sender = fields.Str(required=True, validate=validate.OneOf(['user', 'system']))
    # timestamp es opcional, se genera automáticamente si no se proporciona
    timestamp = fields.Str(allow_none=True, missing=None)

class MessageMetadataSchema(Schema):
    """Esquema para metadatos del mensaje."""
    
    word_count = fields.Int()
    character_count = fields.Int()

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
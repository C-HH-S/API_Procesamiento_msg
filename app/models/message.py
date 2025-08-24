"""
Modelos de datos para la aplicación.
Este módulo define las entidades de base de datos usando SQLAlchemy.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Instancia global de SQLAlchemy
db = SQLAlchemy()

class Message(db.Model):
    """
    Modelo para mensajes de chat.
    
    Representa un mensaje en el sistema con todos sus metadatos.
    """
    __tablename__ = 'messages'
    
    # Campos principales del mensaje
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender = db.Column(db.String(10), nullable=False)
    
    # Metadatos del mensaje
    word_count = db.Column(db.Integer, nullable=False, default=0)
    character_count = db.Column(db.Integer, nullable=False, default=0)
    processed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __init__(self, message_id, session_id, content, timestamp, sender, word_count=0, character_count=0):
        """
        Inicializa un nuevo mensaje.
        
        Args:
            message_id: ID único del mensaje
            session_id: ID de la sesión
            content: Contenido del mensaje
            timestamp: Timestamp del mensaje
            sender: Remitente ('user' o 'system')
            word_count: Número de palabras (calculado automáticamente si no se proporciona)
            character_count: Número de caracteres (calculado automáticamente si no se proporciona)
        """
        self.message_id = message_id
        self.session_id = session_id
        self.content = content
        self.timestamp = timestamp
        self.sender = sender
        self.word_count = word_count if word_count > 0 else self._calculate_word_count(content)
        self.character_count = character_count if character_count > 0 else len(content)
        self.processed_at = datetime.now(timezone.utc)
    
    def _calculate_word_count(self, content):
        """Calcula el número de palabras en el contenido."""
        if not content:
            return 0
        return len(content.split())
    
    def to_dict(self):
        """
        Convierte el mensaje a un diccionario.
        
        Returns:
            dict: Representación en diccionario del mensaje
        """
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() + 'Z' if self.timestamp else None,
            'sender': self.sender,
            'metadata': {
                'word_count': self.word_count,
                'character_count': self.character_count,
                'processed_at': self.processed_at.isoformat() + 'Z' if self.processed_at else None
            }
        }
    
    def __repr__(self):
        """Representación string del mensaje."""
        return f'<Message {self.message_id}>'
    
    @classmethod
    def find_by_message_id(cls, message_id):
        """Busca un mensaje por su message_id."""
        return cls.query.filter_by(message_id=message_id).first()
    
    @classmethod
    def find_by_session_id(cls, session_id, limit=10, offset=0, sender=None):
        """
        Busca mensajes por session_id con paginación y filtros.
        
        Args:
            session_id: ID de la sesión
            limit: Límite de resultados
            offset: Desplazamiento para paginación
            sender: Filtro opcional por remitente
            
        Returns:
            list: Lista de mensajes
        """
        query = cls.query.filter_by(session_id=session_id)
        
        if sender:
            query = query.filter_by(sender=sender)
        
        return query.order_by(cls.timestamp.asc()).offset(offset).limit(limit).all()
    
    @classmethod
    def count_by_session_id(cls, session_id, sender=None):
        """
        Cuenta mensajes por session_id.
        
        Args:
            session_id: ID de la sesión
            sender: Filtro opcional por remitente
            
        Returns:
            int: Número total de mensajes
        """
        query = cls.query.filter_by(session_id=session_id)
        
        if sender:
            query = query.filter_by(sender=sender)
        
        return query.count()
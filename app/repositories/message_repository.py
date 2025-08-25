"""
Repositorio para operaciones de base de datos de mensajes.
Este módulo maneja toda la persistencia de datos siguiendo el patrón Repository.
"""
from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from app.models.message import Message, db
from app.utils.exceptions import DatabaseError, MessageNotFoundError

class MessageRepository:
    """Repositorio para operaciones de mensajes en base de datos."""
    
    def save(self, message: Message) -> Message:
        """
        Guarda un mensaje en la base de datos.
        
        Args:
            message: Instancia del mensaje a guardar
            
        Returns:
            Message: El mensaje guardado con ID asignado
            
        Raises:
            DatabaseError: Si ocurre un error en la base de datos
        """
        try:
            db.session.add(message)
            db.session.commit()  # Confirma la transacción
            return message
        except SQLAlchemyError as e:
            db.session.rollback()
            raise DatabaseError(f"Error al guardar mensaje: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"Error inesperado al guardar mensaje: {str(e)}")
    
    def find_by_message_id(self, message_id: str) -> Optional[Message]:
        """
        Busca un mensaje por su message_id.
        
        Args:
            message_id: ID del mensaje a buscar
            
        Returns:
            Message or None: El mensaje encontrado o None si no existe
        """
        try:
            return Message.query.filter_by(message_id=message_id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al buscar mensaje: {str(e)}")
    
    def find_by_session_id(
        self, 
        session_id: str, 
        limit: int = 10, 
        offset: int = 0, 
        sender: Optional[str] = None
    ) -> Tuple[List[Message], int]:
        """
        Busca mensajes por session_id con paginación y filtros.
        
        Args:
            session_id: ID de la sesión
            limit: Límite de resultados por página
            offset: Desplazamiento para paginación
            sender: Filtro opcional por remitente
            
        Returns:
            tuple: (lista_de_mensajes, total_count)
            
        Raises:
            DatabaseError: Si ocurre un error en la base de datos
        """
        try:
            # Construir query base
            query = Message.query.filter_by(session_id=session_id)
            
            # Aplicar filtro por sender si se proporciona
            if sender:
                query = query.filter_by(sender=sender)
            
            # Obtener total de resultados para paginación
            total_count = query.count()
            
            # Aplicar paginación y ordenamiento
            messages = query.order_by(Message.timestamp.asc()).offset(offset).limit(limit).all()
            
            return messages, total_count
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al buscar mensajes por sesión: {str(e)}")
    
    def exists_by_message_id(self, message_id: str) -> bool:
        """
        Verifica si existe un mensaje con el message_id dado.
        
        Args:
            message_id: ID del mensaje a verificar
            
        Returns:
            bool: True si existe, False en caso contrario
        """
        try:
            return db.session.query(Message.query.filter_by(message_id=message_id).exists()).scalar()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al verificar existencia de mensaje: {str(e)}")
    
    def delete_by_message_id(self, message_id: str) -> bool:
        """
        Elimina un mensaje por su message_id.
        
        Args:
            message_id: ID del mensaje a eliminar
            
        Returns:
            bool: True si se eliminó, False si no se encontró
            
        Raises:
            DatabaseError: Si ocurre un error en la base de datos
        """
        try:
            message = self.find_by_message_id(message_id)
            if not message:
                return False
            
            db.session.delete(message)
            db.session.commit()
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise DatabaseError(f"Error al eliminar mensaje: {str(e)}")
    
    def count_by_session_id(self, session_id: str, sender: Optional[str] = None) -> int:
        """
        Cuenta mensajes por session_id.
        
        Args:
            session_id: ID de la sesión
            sender: Filtro opcional por remitente
            
        Returns:
            int: Número total de mensajes
        """
        try:
            query = Message.query.filter_by(session_id=session_id)
            
            if sender:
                query = query.filter_by(sender=sender)
                
            return query.count()
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al contar mensajes: {str(e)}")
    
    def get_session_ids(self, limit: int = 100) -> List[str]:
        """
        Obtiene lista de session_ids únicos.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            List[str]: Lista de session_ids únicos
        """
        try:
            result = db.session.query(Message.session_id).distinct().limit(limit).all()
            return [row[0] for row in result]
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener session_ids: {str(e)}")
    
    def search_globally(self, query: str, limit: int, offset: int) -> Tuple[List[Message], int]:
        """
        Realiza una búsqueda global paginada de mensajes en todas las sesiones.
        
        Args:
            query: Texto a buscar.
            limit: Límite de resultados.
            offset: Desplazamiento de resultados.
            
        Returns:
            Tuple: Una tupla con (lista de mensajes, total de resultados).
        """
        try:
            messages = Message.search_globally(query, limit, offset)
            total_results = Message.count_global_search_results(query)
            return messages, total_results
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al buscar mensajes globalmente: {str(e)}")

    def verify_persistence(self, message_id: str) -> bool:
        """
        Verifica que un mensaje esté realmente persistido en la BD.
        Útil para debugging.
        
        Args:
            message_id: ID del mensaje a verificar
            
        Returns:
            bool: True si el mensaje está persistido
        """
        try:
            # Fuerza una nueva consulta sin usar caché de sesión
            db.session.expunge_all()
            message = db.session.query(Message).filter_by(message_id=message_id).first()
            return message is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al verificar persistencia: {str(e)}")
    
    def get_all_messages_debug(self, limit: int = 50) -> List[Message]:
        """
        Obtiene todos los mensajes para debugging.
        Solo para desarrollo/debugging.
        
        Args:
            limit: Límite de mensajes a obtener
            
        Returns:
            List[Message]: Lista de todos los mensajes
        """
        try:
            return Message.query.order_by(Message.processed_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error al obtener mensajes para debug: {str(e)}")
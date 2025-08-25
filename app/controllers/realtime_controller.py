"""
Controlador de eventos para SocketIO.
"""
from app import socketio
from flask import request

@socketio.on('connect')
def handle_connect():
    print(f"Cliente SocketIO conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente SocketIO desconectado: {request.sid}")

def broadcast_new_message(message_data: dict):
    socketio.emit('new_message', message_data)
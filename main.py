"""
Punto de entrada principal de la aplicación.
Este módulo inicia la aplicación Flask con soporte completo para UTF-8.
"""
import os
import sys
import eventlet
from app import create_app, socketio

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import locale
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
        except:
            pass  

# Crear aplicación
app = create_app()

if __name__ == '__main__':
    # Obtener host y puerto desde las variables de entorno
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print("🚀 Iniciando Message Processing API con SocketIO")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"🔧 Modo debug: {debug_mode}")
    print(f"❤️  Health check: http://{host}:{port}/health")
    print("🌍 Encoding: UTF-8 ✓")
    
    # Usar eventlet para ejecutar el servidor con SocketIO
    eventlet.wsgi.server(
        eventlet.listen(('', port)),
        app,
        log=None
    )
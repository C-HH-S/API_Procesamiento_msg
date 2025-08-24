"""
Punto de entrada principal de la aplicación.
Este módulo inicia la aplicación Flask.
"""
import os
import sys
from app import create_app

# Configuración de encoding para sistemas Windows y Unix
if sys.platform.startswith('win'):
    import locale
    # Forzar encoding UTF-8 en Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
        except:
            pass
else:
    # Para sistemas Unix/Linux/macOS
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Crear aplicación
app = create_app()

if __name__ == '__main__':
    # Configuración para desarrollo
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"🚀 Iniciando Message Processing API")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"🔧 Modo debug: {debug_mode}")
    print(f"📚 Documentación: http://{host}:{port}/")
    print(f"❤️  Health check: http://{host}:{port}/health")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        # Configuraciones adicionales para Unicode
        threaded=True,
        use_reloader=debug_mode
    )
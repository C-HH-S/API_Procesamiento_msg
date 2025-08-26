# Message Processing API 🚀

Una API RESTful avanzada para procesamiento de mensajes de chat con funcionalidades en tiempo real, desarrollada en Python con Flask.

## 📋 Descripción

Esta API permite:
- ✅ Recibir y procesar mensajes de chat
- ✅ Validar formato y contenido de mensajes
- ✅ Almacenar mensajes en base de datos SQLite
- ✅ Recuperar mensajes por sesión con paginación
- ✅ Filtrar contenido inapropiado
- ✅ Generar estadísticas de sesión
- ✅ **Comunicación WebSocket en tiempo real**
- ✅ **Autenticación con API Keys**
- ✅ **Rate limiting por IP**
- ✅ **Búsqueda global de mensajes**

## 🛠️ Stack Tecnológico

- **Python 3.10+**
- **Flask** - Framework web
- **Flask-SocketIO** - WebSocket en tiempo real
- **SQLAlchemy** - ORM para base de datos
- **SQLite** - Base de datos
- **Marshmallow** - Serialización y validación
- **Flask-Limiter** - Rate limiting
- **Flask-CORS** - Soporte CORS
- **Eventlet** - Servidor WSGI asíncrono
- **Pytest** - Framework de pruebas

## 🗂️ Arquitectura

El proyecto sigue principios de **Arquitectura Limpia** con separación clara de responsabilidades:

```
message-processing-api/
├── app/
│   ├── __init__.py              # Factory de aplicación Flask
│   ├── config.py                # Configuraciones de entorno
│   ├── controllers/             # Controladores HTTP y WebSocket
│   │   ├── message_controller.py
│   │   └── realtime_controller.py
│   ├── models/                  # Modelos de base de datos
│   │   └── message.py
│   ├── repositories/            # Capa de acceso a datos
│   │   └── message_repository.py
│   ├── services/               # Lógica de negocio
│   │   └── message_service.py
│   ├── schemas/                # Esquemas de validación
│   │   └── message_schema.py
│   └── utils/                  # Utilidades y helpers
│       ├── auth.py
│       ├── exceptions.py
│       └── validators.py
├── tests/                      # Suite de pruebas
├── main.py                     # Punto de entrada
├── requirements.txt            # Dependencias de Python
├── Dockerfile                  # Configuración de Docker
├── .env                       # Variables de entorno
└── README.md                  # Este archivo
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd message-processing-api
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# El archivo .env ya está incluido con valores de desarrollo
# Para producción, modifica los valores apropiados:

FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DATABASE_FILENAME=messages.db
SECRET_KEY=your-secret-key-change-in-production
API_KEYS=key-123,test-key-456
```

5. **Inicializar la aplicación**
```bash
python main.py
```

La API estará disponible en `http://localhost:5000`

### 🐳 Docker (Alternativa)

```bash
# Construir imagen
docker build -t message-api .

# Ejecutar contenedor
docker run -p 5000:5000 message-api
```

## 📚 Documentación de la API

### 🔐 Autenticación

Todos los endpoints (excepto `/health` y `/`) requieren autenticación con API Key:

```bash
curl -H "Authorization: Bearer key-123" \
     -H "Content-Type: application/json" \
     -d '{"session_id":"test","content":"Hola","sender":"user"}' \
     http://localhost:5000/api/messages
```

### 📡 WebSocket en Tiempo Real

La API incluye soporte WebSocket para recibir notificaciones de nuevos mensajes, se añadió un componente .html para realizar la prueba:

```javascript
// Conectar al WebSocket
const socket = io('http://localhost:5000');

// Escuchar nuevos mensajes
socket.on('new_message', (data) => {
    console.log('Nuevo mensaje:', data);
});
```
# Abrir en navegador
open index_socket.html

-**Eventos**

-connect: Cuando se establece la conexión
-disconnect: Cuando se cierra la conexión
-new_message: Cuando se crea un nuevo mensaje (broadcast automático)

### 🎯 Rate Limiting

- **100 requests por hora** por IP en el endpoint de creación de mensajes
- Límites configurables en `config.py`

### Endpoints Principales

#### POST /api/messages 🔐
Crea un nuevo mensaje.

**Headers:**
```
Authorization: Bearer <api_key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message_id": "msg-unique-123",
  "session_id": "session-abc-456",
  "content": "Este es el contenido del mensaje",
  "timestamp": "2023-06-15T14:30:00Z",
  "sender": "user"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "message_id": "msg-unique-123",
    "session_id": "session-abc-456",
    "content": "Este es el contenido del mensaje",
    "timestamp": "2023-06-15T14:30:00Z",
    "sender": "user",
    "metadata": {
      "word_count": 7,
      "character_count": 34,
      "processed_at": "2023-06-15T14:30:01Z",
      "updated_at": "2023-06-15T14:30:01Z"
    }
  }
}
```

#### GET /api/messages/{session_id}
Obtiene mensajes de una sesión con paginación.

**Query Parameters:**
- `limit` (opcional): Número máximo de mensajes (default: 10, max: 100)
- `offset` (opcional): Desplazamiento para paginación (default: 0)
- `sender` (opcional): Filtrar por remitente ("user" o "system")

**Example:** `GET /api/messages/session-05?limit=10&offset=0&sender=user`

**Response (200):**
```json
{
    "data": [
        {
            "content": "¡Hola!, prueba con postman #3",
            "message_id": "msg-13",
            "metadata": {
                "character_count": 29,
                "processed_at": "2025-08-26T19:20:11.792081Z",
                "updated_at": "2025-08-26T19:20:11.792081Z",
                "word_count": 5
            },
            "sender": "system",
            "session_id": "05",
            "timestamp": "2023-06-15T14:30:00Z"
        }
    ],
    "pagination": {
        "has_next": false,
        "has_prev": false,
        "limit": 10,
        "offset": 0,
        "total": 1
    },
    "status": "success"
}
```

#### GET /api/message/{message_id}
Obtiene un mensaje específico por message_id.
**Example:** `GET /api/message/msg-001`

#### GET /api/sessions/{session_id}/stats
Obtiene estadísticas de una sesión.
**Example:** `GET /api/sessions/session-04/stats`

**Response (200):**
```json
{
    "data": {
        "session_id": "04",
        "system_messages": 2,
        "total_messages": 2,
        "user_messages": 0
    },
    "status": "success"
}
```

#### 🔍 GET /api/messages/search/all
Búsqueda global de mensajes.

**Query Parameters:**
- `query` (requerido): Texto a buscar (mínimo 3 caracteres)
- `limit` (opcional): Número de resultados (default: 10, max: 100)
- `offset` (opcional): Desplazamiento (default: 0)

**Example:** `GET /api/messages/search/all?query=hola&limit=10`

**Response (200):**
```json
{
    "data": [
        {
            "content": "olvide decir hola",
            "message_id": "msg-11",
            "metadata": {
                "character_count": 26,
                "processed_at": "2025-08-26T19:17:42.868392Z",
                "updated_at": "2025-08-26T19:17:42.868392Z",
                "word_count": 4
            },
            "sender": "system",
            "session_id": "04",
            "timestamp": "2023-06-15T14:30:00Z"
        },
        {
            "content": "Hola, mi nombre es Claudia",
            "message_id": "msg-12",
            "metadata": {
                "character_count": 29,
                "processed_at": "2025-08-26T19:19:52.670528Z",
                "updated_at": "2025-08-26T19:19:52.670528Z",
                "word_count": 5
            },
            "sender": "system",
            "session_id": "04",
            "timestamp": "2023-06-15T14:30:00Z"
        },
        {
            "content": "¡Hola!, como estas?",
            "message_id": "msg-13",
            "metadata": {
                "character_count": 29,
                "processed_at": "2025-08-26T19:20:11.792081Z",
                "updated_at": "2025-08-26T19:20:11.792081Z",
                "word_count": 5
            },
            "sender": "system",
            "session_id": "05",
            "timestamp": "2023-06-15T14:30:00Z"
        }
    ],
    "pagination": {
        "limit": 10,
        "next_offset": null,
        "offset": 0,
        "total_results": 3
    },
    "status": "success"
}
```

### Endpoints de Sistema

#### GET /health
Verifica el estado de la aplicación.

```json
{
  "status": "ok",
  "message": "Servicio funcionando correctamente",
  "service": "Message Processing API",
  "timestamp": "2023-06-15T14:30:00Z",
  "encoding": "UTF-8 ✓"
}
```

#### GET /
Información general de la API.

### 🚫 Manejo de Errores

Todos los errores siguen el mismo formato estandarizado:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Descripción del error",
    "details": {
      "missing_fields": ["timestamp", "sender"]
    }
  }
}
```

**Códigos de Error Comunes:**
- `INVALID_FORMAT` - Formato de datos inválido
- `VALIDATION_ERROR` - Error de validación
- `SCHEMA_VALIDATION_ERROR` - Error en esquema Marshmallow
- `INAPPROPRIATE_CONTENT` - Contenido inapropiado detectado
- `NOT_FOUND` - Recurso no encontrado
- `DATABASE_ERROR` - Error en base de datos
- `AUTH_REQUIRED` - Autenticación requerida
- `INVALID_API_KEY` - API Key inválida
- `SEARCH_QUERY_TOO_SHORT` - Query de búsqueda muy corta

**Códigos de Estado HTTP:**
- `200` - Éxito
- `201` - Creado exitosamente
- `400` - Error de validación/formato
- `401` - No autorizado
- `403` - API Key inválida
- `404` - No encontrado
- `429` - Rate limit excedido
- `500` - Error interno del servidor

## 🧪 Pruebas

### Ejecutar todas las pruebas
```bash
pytest
```

### Ejecutar con cobertura
```bash
pytest --cov=app --cov-report=html
```

### Estructura de Pruebas

```
tests/
├── conftest.py                 # Configuración y fixtures compartidos
├── test_auth.py               # Pruebas de autenticación
├── test_message_controller.py # Pruebas de controladores
├── test_message_repository.py # Pruebas de repositorio
├── test_message_service.py    # Pruebas de servicios
└── test_realtime_controller.py # Pruebas de WebSocket
```

### Ejecutar pruebas específicas
```bash
# Pruebas del repositorio
pytest tests/test_message_repository.py -v

# Pruebas del servicio  
pytest tests/test_message_service.py -v

# Pruebas del controlador
pytest tests/test_message_controller.py -v
```
El proyecto mantiene una alta cobertura de código. Para generar informes:

# Generar reporte de cobertura en consola
coverage report

# Generar reporte HTML
coverage html

# Ver el reporte HTML
# En Windows
start htmlcov/index.html

# En Linux/Mac
open htmlcov/index.html

**Fixtures Disponibles**
Las pruebas incluyen fixtures útiles para testing:

-app: Aplicación Flask configurada para testing
-client: Cliente de prueba HTTP
-message_repository: Repositorio de mensajes
-message_service: Servicio de mensajes
-sample_message_data: Datos de mensaje válidos
-invalid_message_data: Datos de mensaje inválidos


## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Entorno de ejecución
FLASK_ENV=development|testing|production

# Configuración de servidor
FLASK_DEBUG=True|False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Base de datos
DATABASE_URL=sqlite:///messages.db

# Seguridad
SECRET_KEY=your-secret-key-here
API_KEYS=key1,key2,key3  # Lista separada por comas
```

## 🛡️ Filtro de Contenido

La API incluye un filtro de contenido que bloquea mensajes con:
- spam
- malware  
- virus
- hack
- phishing

Lista configurable en `app/config.py`.
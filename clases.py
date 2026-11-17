from pydantic import BaseModel as esquema
from typing import Optional as opcion
# from fastapi import Request
# from fastapi.responses import JSONResponse as JSON
# from starlette.middleware.base import BaseHTTPMiddleware

# Definimos la API Key secreta (idealmente cárgala desde una variable de entorno en Render)
# API_KEY = os.getenv("API_KEY", "Black-347")

# clase para definir el esquema de datos para el cambio de perfil
class SolicitudCambioPerfil(esquema):
    id_controlador: str
    nombre_perfil: str
    receta_yaml: dict
    actualizado_por: str

# esquema para definir la gestion del usuario en el saas_manager
class SolicitudUsuario(esquema):
    id_usuario: str
    nombre: str
    email: str
    rol: opcion[str] = "standard"

# esquema para definir la gestion de la receta en el dispositivo
class SolicitudDispositivo(esquema):
    id_dispositivo: str
    id_usuario: str
    nombre_dispositivo: str
    sistema_operativo: str = "windows 11"
    estado: opcion[str] = "activo"


# El middleware para validar la API Key en cada petición HTTP
"""
class Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Excluir rutas públicas o de documentación para que no fallen al abrirlas en el navegador
        ruta_escape = ["/", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in ruta_escape:
            return await call_next(request)

        # Obtener la API Key de las cabeceras HTTP (ej: "X-API-Key: tu_clave")
        llave_cliente = request.headers.get("X-API-Key")

        # Validar si la clave existe y coincide
        if not llave_cliente or llave_cliente != API_KEY:
            JSON(
                status_code=403,
                content={
                    "detail": (
                        "Acceso denegado: API Key inválida, faltante o no autorizada."
                    )
                },
            )
            return JSON()

        # Si es válida, continuar con la petición normal
        response = await call_next(request)
        return response
"""

class UsuarioRegistro(esquema):
    id_usuario_registro: str
    nombre: str
    email: str
    contraseña: str
    rol: opcion[str] = "standard"

class UsuarioLogin(esquema):
    email: str
    contraseña: str

class Token(esquema):
    access_token: str
    token_type: str = "bearer"


from fastapi import solicitud
from fastapi.responses import JSONResponse as JSON
from starlette.middleware.base import BaseHTTPMiddleware 
import os 
from pydantic import BaseModel as esquema

# Definimos la API Key secreta (idealmente cárgala desde una variable de entorno en Render)
API_KEY = os.getenv("API_KEY", "Black-347")

# El middleware para validar la API Key en cada petición HTTP
class Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: solicitud, call_next):
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
    
class SolicitudCambioPerfil(esquema):
    
    id_controlador: str
    nombre_perfil: str
    receta_yaml: dict
    actualizado_por: str


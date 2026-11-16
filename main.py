import datetime as LaFecha
import os as sistema
import certifi as Certificado
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# Definimos la API Key secreta (idealmente cárgala desde una variable de entorno en Render)
API_KEY = sistema.getenv("API_KEY", "Black-347")

# Configuramos la base de datos y los endpoints de la API
MONGO_URI = sistema.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/")
client = AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)
db = client["saas_manager"] 


# El middleware para validar la API Key en cada petición HTTP
class Middleware(BaseHTTPMiddleware):

  async def dispatch(self, request: Request, call_next):
    # 1. Excluir rutas públicas o de documentación para que no fallen al abrirlas en el navegador
    paths_to_skip = ["/", "/docs", "/openapi.json", "/redoc"]
    if request.url.path in paths_to_skip:
      return await call_next(request)

    # 2. Obtener la API Key de las cabeceras HTTP (ej: "X-API-Key: tu_clave")
    client_api_key = request.headers.get("X-API-Key")

    # 3. Validar si la clave existe y coincide
    if not client_api_key or client_api_key != API_KEY:
      return JSONResponse(
          status_code=403,
          content={
              "detail": (
                  "Acceso denegado: API Key inválida, faltante o no autorizada."
              )
          },
      )

    # Si es válida, continuar con la petición normal
    response = await call_next(request)
    return response


# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="OS Context Tuner API (oct_backend_api)",
    version="1.0.0",
)

# Registrar el middleware en la app
app.add_middleware(Middleware)




class ProfileChangeRequest(BaseModel):
  device_id: str
  profile_name: str
  yaml_recipe: dict
  updated_by: str


@app.get("/")
def home():
  return {"status": "online", "message": "API pública sin restricciones de Key."}


@app.post("/api/profiles/update")
async def update_system_profile(data: ProfileChangeRequest):
  """Este endpoint ahora requerirá obligatoriamente la cabecera 'X-API-Key'"""
  await db.profiles.update_one(
      {"device_id": data.device_id},
      {
          "$set": {
              "device_id": data.device_id,
              "profile_name": data.profile_name,
              "yaml_recipe": data.yaml_recipe,
              "updated_by": data.updated_by,
              "timestamp": LaFecha.datetime.utcnow(),
          }
      },
      upsert=True,
  )
  return {"status": "success", "message": "Perfil guardado correctamente."}


# Nota sobre WebSockets: Los WebSockets estándar no pasan por el BaseHTTPMiddleware
# de la misma forma para validar cabeceras en el handshake de manera sencilla.
# Para proteger el WebSocket, se suele validar la API Key enviándola en los Query Parameters (ej: /ws/agent?api_key=123)
@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket, api_key: str | None = None):
  if api_key != API_KEY:
    await websocket.close(code=4008)  # Código de cierre por política de seguridad
    return

  await websocket.accept()
  try:
    while True:
      data = await websocket.receive_json()
      await websocket.send_json({"status": "acknowledged", "data": data})
  except WebSocketDisconnect:
    print("Agente desconectado.")


if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


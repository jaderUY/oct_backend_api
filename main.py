import datetime
import os
import certifi
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import uvicorn

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="OS Context Tuner API (oct_backend_api)",
    version="1.0.0",
    description=(
        "Backend asíncrono para la gestión y sincronización de perfiles de"
        " contexto."
    ),
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE BASE DE DATOS (MongoDB Atlas + Motor)
# ---------------------------------------------------------
# Intenta leer la URI desde las variables de entorno; si no existe, usa una por defecto para pruebas locales.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://tu_usuario:tu_password@cluster.mongodb.net/?retryWrites=true&w=majority",
)

# Conexión asíncrona segura validando certificados TLS con certifi
client = AsyncIOMotorClient(
    MONGO_URI, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000
)
db = client["oct_database"]

# Lista global para mantener las conexiones WebSocket activas (Agentes de Windows)
connected_agents: list[WebSocket] = []


# ---------------------------------------------------------
# MODELOS DE DATOS (Pydantic)
# ---------------------------------------------------------
class ProfileChangeRequest(BaseModel):
  device_id: str
  profile_name: str
  yaml_recipe: dict  # Estructura YAML/JSON del perfil del sistema
  updated_by: str  # Ejemplo: "windows_agent" o "android_app"


# ---------------------------------------------------------
# ENDPOINTS REST (HTTP)
# ---------------------------------------------------------
@app.get("/")
def home():
  return {
      "status": "online",
      "project": "OS Context Tuner (oct_backend_api)",
      "message": "API asíncrona funcionando correctamente.",
  }


@app.post("/api/profiles/update")
async def update_system_profile(data: ProfileChangeRequest):
  """Endpoint HTTP POST para recibir y guardar los cambios de perfiles

  provenientes del agente de Windows o la app móvil hacia MongoDB Atlas.
  """
  try:
    profile_document = {
        "device_id": data.device_id,
        "profile_name": data.profile_name,
        "yaml_recipe": data.yaml_recipe,
        "updated_by": data.updated_by,
        "timestamp": datetime.datetime.utcnow(),
    }

    # Actualiza o inserta el documento basándose en el 'device_id' (upsert)
    await db.profiles.update_one(
        {"device_id": data.device_id}, {"$set": profile_document}, upsert=True
    )

    return {
        "status": "success",
        "message": "Perfil de contexto guardado en MongoDB Atlas exitosamente.",
        "device_id": data.device_id,
        "profile_name": data.profile_name,
    }

  except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Error al guardar el perfil en la base de datos: {str(e)}",
    )


# ---------------------------------------------------------
# ENDPOINT WEBSOCKET (Tiempo Real)
# ---------------------------------------------------------
@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
  """Canal WebSocket bidireccional para la comunicación en tiempo real

  con el agente de Windows de OS Context Tuner.
  """
  await websocket.accept()
  connected_agents.append(websocket)
  print("¡Agente de Windows conectado al WebSocket!")

  try:
    while True:
      # Recibir datos, métricas o comandos enviados por el agente
      data = await websocket.receive_json()
      print(f"Datos recibidos del agente: {data}")

      # Responder al agente de Windows de forma inmediata
      await websocket.send_json({
          "status": "acknowledged",
          "message": "Comando o métrica procesada correctamente por el servidor",
      })

  except WebSocketDisconnect:
    connected_agents.remove(websocket)
    print("El agente de Windows se ha desconectado.")


# ---------------------------------------------------------
# EJECUCIÓN LOCAL
# ---------------------------------------------------------
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


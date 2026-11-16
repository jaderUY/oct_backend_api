from datetime import datetime, timezone
import os
import motor.motor_asyncio
import uvicorn
import clases
import certifi as Certificado
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Configuramos la base de datos de MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/")
cliente = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)

# Inicializamos la aplicación FastAPI sin middlewares
app = FastAPI(
    title="OS Context Tuner API (oct_backend_api)",
    version="1.0.0",
    description="API simplificada para gestionar perfiles de sistema y comunicación asíncrona."
)

db = cliente["saas_manager"]

@app.get("/")
def inicio():
    return {"status": "online", "message": "API pública y abierta funcionando correctamente."}

@app.post("/api/profiles/update")
async def actualizarPerfilSistema(data: clases.SolicitudCambioPerfil):
    # Recibe y guarda o actualiza el perfil en MongoDB Atlas de forma directa
    await db.profiles.update_one(
        {"id_controlador": data.id_controlador},
        {
            "$set": {
                "id_controlador": data.id_controlador,
                "nombre_perfil": data.nombre_perfil,
                "receta_yaml": data.receta_yaml,
                "actualizado_por": data.actualizado_por,
                "timestamp": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    return {"status": "success", "message": "Perfil guardado correctamente en la base de datos."}

@app.websocket("/ws/agent")
async def endpointWebsocket(websocket: WebSocket):
    # Conexión WebSocket directa y abierta para el agente
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"status": "acknowledged", "received_data": data})
    except WebSocketDisconnect:
        print("El agente remoto se ha desconectado.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
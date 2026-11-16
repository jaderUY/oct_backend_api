import datetime
import os
import motor.motor_asyncio
import uvicorn
import clases 
import certifi as Certificado
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Configuramos la base de datos y los endpoints de la API
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/") #Para mejor seguridad
cliente = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)


# Inicializamos la aplicación FastAPI y le agregamos el middleware de validación de API Key
app = FastAPI( title="OS Context Tuner API (oct_backend_api)", version="1.0.0", description="esta api tiene el rol de gestionar perfiles de sistema y comunicarse con agentes remotos. y permitir la la conexión asincronica entre la aplicacion movil y de escritorio con la base de datos" )
app.add_middleware(clases.Middleware)  # Registrar el middleware en la app
db = cliente["saas_manager"]  

"""
@app.get("/procesar")
async def procesar_datos():
    time.sleep(5)
    return {"mensaje": "Procesado"}
"""

@app.get("/")
def inicio():
    return {"status": "online", "message": "API pública para gestionar perfiles de sistema y comunicarse con agentes remotos."}

@app.post("/api/profiles/update")
async def actualizarPerfilSistema(data: clases.SolicitudCambioPerfil):
    # Este endpoint ahora requerirá obligatoriamente la cabecera 'X-API-Key'
    await db.profiles.update_one(
        {"id_controlador": data.id_controlador},
        {
            "$set": {
                "id_controlador": data.id_controlador,
                "nombre_perfil": data.nombre_perfil,
                "receta_yaml": data.receta_yaml,
                "actualizado_por": data.actualizado_por,
                "timestamp": datetime.utcnow(),
            }
        },
        upsert=True,
    )
    mensaje = {"status": "success", "message": "Perfil guardado correctamente."}
    return mensaje

# Endpoint para la comunicación WebSocket con los agentes remotos
@app.websocket("/ws/agent")
async def endpointWebsocket(websocket: WebSocket, api_key: str | None = None):
    if api_key != clases.API_KEY:
        await websocket.close(code=4008)  # Código de cierre por política de seguridad
        return
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"status": "acknowledged", "data": data})
    except WebSocketDisconnect:
        raise RuntimeError("El agente remoto se ha desconectado.")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


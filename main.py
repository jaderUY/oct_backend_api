from datetime import datetime, timezone
import os as entorno
import motor.motor_asyncio
import uvicorn
import clases as Objetos
import certifi as Certificado
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException

# Configuramos la base de datos de MongoDB Atlas
MONGO_URI = entorno.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/")
cliente = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)
db = cliente["saas_manager"]

app = FastAPI(
    title="OS Context Tuner API (oct_backend_api)",
    version="1.0.0",
    description=(
        """
        API simplificada para gestionar perfiles de sistema y comunicación
        asíncrona.
        """
    ),
    contact={
        "name": "Jader Araujo",
        "email": "jaderdavidaraujoarboleda@gmail.com"
    }
)

"""
@app.get("/procesar")
async def procesar_datos():
    time.sleep(5)
    return {"mensaje": "Procesado"}
"""

@app.get("/")
def inicio():
    estatuto = {"status": "online", "message": "API pública y abierta funcionando correctamente."}
    return estatuto

"""
@app.post("/recibir")
async def recibir_datos(datos: dict):
    nombre = datos["nombre_perfil"]
    return {"status": "ok"}
"""

@app.post("/api/profiles/update")
async def actualizarPerfilSistema(data: Objetos.SolicitudCambioPerfil):
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

    estado = {"status": "success", "message": "Perfil guardado correctamente en la base de datos."}
    return estado


# endpoint GET para consultar el perfil asignado a un controlador
@app.get("/api/profiles/{id_controlador}")
async def obtenerPerfilSistema(id_controlador: str):
    # Buscamos el documento por id_controlador y excluimos el campo interno _id
    perfil = await db.profiles.find_one(
        {"id_controlador": id_controlador}, {"_id": 0}
    )

    if not perfil:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No se encontró ningún perfil registrado para el controlador:"
                f" {id_controlador}"
            ),
        )
    estado = {"status": "success", "data": perfil}
    return estado

# enpoint POST para registrar o actualizar un usuario en la base de datos
@app.post("/api/users")
async def registrar_usuario(data: Objetos.SolicitudUsuario):
    await db.users.update_one(
        {"id_usuario": data.id_usuario},
        {
            "$set": {
                "id_usuario": data.id_usuario,
                "nombre": data.nombre,
                "email": data.email,
                "rol": data.rol,
                "timestamp": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    estatuto = {"status": "success", "message": "Usuario registrado o actualizado correctamente."}
    return estatuto

@app.get("/api/users/{id_usuario}")
async def obtener_usuario(id_usuario: str):
    usuario = await db.users.find_one({"id_usuario": id_usuario}, {"_id": 0})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    estatuto = {"status": "success", "data": usuario}
    return estatuto

# endpoint POST para registrar o actualizar de una vez un dispositivo en la base de datos
@app.post("/api/devices")
async def registrar_dispositivo(data: Objetos.SolicitudDispositivo):
    await db.devices.update_one(
        {"id_dispositivo": data.id_dispositivo},
        {
            "$set": {
                "id_dispositivo": data.id_dispositivo,
                "id_usuario": data.id_usuario,
                "nombre_dispositivo": data.nombre_dispositivo,
                "sistema_operativo": data.sistema_operativo,
                "estado": data.estado,
                "ultimo_registro": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
    return {"status": "success", "message": "Dispositivo registrado correctamente."}

@app.get("/api/users/{id_usuario}/devices")
async def listar_dispositivos_usuario(id_usuario: str):
    cursor = db.devices.find({"id_usuario": id_usuario}, {"_id": 0})
    dispositivos = await cursor.to_list(length=100)
    return {"status": "success", "data": dispositivos}

"""
@app.post("/validar")
async def validar_llave(llave: str):
    if llave != "12345":
        return {"error": "No autorizado"}
    return {"status": "acceso concedido"}
"""

@app.websocket("/ws/agent")
async def endpointWebsocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"status": "acknowledged", "received_data": data})
    except WebSocketDisconnect:
        print("El agente remoto se ha desconectado.")
    finally:
        await websocket.close()

if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


from datetime import datetime, timezone, timedelta
import os as entorno
import motor.motor_asyncio
import uvicorn
import certifi as Certificado
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
import bcrypt
from jose import jwt
from typing import Optional as opcion

import clases as Objetos

# Configuración de seguridad JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Configuramos la base de datos de MongoDB Atlas
SECRET_KEY = entorno.getenv("SECRET_KEY", "Black-345")
MONGO_URI = entorno.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/")
cliente = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)
db = cliente["saas_manager"]

def obtener_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verificar_password(password_plano: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password_plano.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def crear_access_token(data: dict, expires_delta: opcion[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

app = FastAPI(
    title="OS Context Tuner API (oct_backend_api)",
    version="1.0.0",
    description="API optimizada para gestionar perfiles de sistema, autenticación y comunicación asíncrona.",
    contact={
        "name": "Jader Araujo",
        "email": "jaderdavidaraujoarboleda@gmail.com"
    }
)

@app.get("/")
def inicio():
    return {"status": "online", "message": "API pública y abierta funcionando correctamente."}

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
    return {"status": "success", "message": "Perfil guardado correctamente en la base de datos."}

@app.get("/api/profiles/{id_controlador}")
async def obtenerPerfilSistema(id_controlador: str):
    perfil = await db.profiles.find_one({"id_controlador": id_controlador}, {"_id": 0})
    if not perfil:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún perfil registrado para el controlador: {id_controlador}"
        )
    return {"status": "success", "data": perfil}

@app.post("/api/users")
async def registrar_usuario_saas(data: Objetos.SolicitudUsuario):
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
    return {"status": "success", "message": "Usuario registrado o actualizado correctamente."}

@app.get("/api/users/{id_usuario}")
async def obtener_usuario(id_usuario: str):
    usuario = await db.users.find_one({"id_usuario": id_usuario}, {"_id": 0})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"status": "success", "data": usuario}

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
    return {"status": "success", "dispositivos": dispositivos}

@app.post("/api/auth/register", response_model=dict)
async def registrar_usuario(data: Objetos.UsuarioRegistro):
    usuario_existente = await db.users.find_one({"email": data.email})
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )

    hashed_password = obtener_password_hash(data.contraseña)

    nuevo_usuario = {
        "id_usuario": data.id_usuario_registro,  # Sincronizado a id_usuario
        "nombre": data.nombre,
        "email": data.email,
        "password_hash": hashed_password,
        "rol": data.rol,
        "timestamp": datetime.now(timezone.utc),
    }

    await db.users.insert_one(nuevo_usuario)
    return {"status": "success", "message": "Usuario registrado exitosamente."}

@app.post("/api/auth/login", response_model=Objetos.Token)
async def login_usuario(data: Objetos.UsuarioLogin):
    usuario = await db.users.find_one({"email": data.email})
    if not usuario or not verificar_password(data.contraseña, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (email o contraseña inválidos).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_access_token(
        data={"sub": usuario["id_usuario"], "email": usuario["email"], "rol": usuario.get("rol", "standard")},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

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
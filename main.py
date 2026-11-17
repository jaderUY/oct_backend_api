from datetime import datetime, timezone, timedelta
import os as entorno
import motor.motor_asyncio
import uvicorn
import clases as Objetos
import certifi as Certificado
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from passlib.context import CryptContext
from jose import jwt
from typing import Optional as opcion

# Configuración de seguridad JWT
duracion_token = 60 * 24
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = duracion_token

# Configuramos la base de datos de MongoDB Atlas
SECRET_KEY = entorno.getenv("SECRET_KEY", "Black-345")
MONGO_URI = entorno.getenv("MONGO_URI", "mongodb+srv://Admin:Baldur$038@oscontexttunerdb.q7nra7u.mongodb.net/")
cliente = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=Certificado.where(), serverSelectionTimeoutMS=5000)
db = cliente["saas_manager"]

estado = [
    {"status": "online", "message": "API pública y abierta funcionando correctamente."},
    {"status": "success", "message": "Perfil guardado correctamente en la base de datos."},
    {"status": "success", "message": "Perfil actualizado correctamente."},
    {"status": "success", "message": "Usuario registrado o actualizado correctamente."},
    {"status": "success"},
    {"status": "success", "message": "Dispositivo registrado correctamente."},
    {"status": "success"},
    {"status": "success", "message": "Usuario registrado exitosamente."},
    {"token_type": "bearer"}
]

# contexto para encriptar las contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(password_plano: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plano, password_hash)

def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def crear_access_token(data: dict, expires_delta: opcion[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    return estado[0]

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
    return estado[1]

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
    estado[2]["data"] = perfil
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
    return estado[3]

@app.get("/api/users/{id_usuario}")
async def obtener_usuario(id_usuario: str):
    usuario = await db.users.find_one({"id_usuario": id_usuario}, {"_id": 0})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    estado[4]["data"] = usuario
    return estado

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
    return estado[5]

@app.get("/api/users/{id_usuario}/devices")
async def listar_dispositivos_usuario(id_usuario: str):
    cursor = db.devices.find({"id_usuario": id_usuario}, {"_id": 0})
    dispositivos = await cursor.to_list(length=100)
    estado[6]["dispositivos"] = dispositivos
    return estado[6]

"""
@app.post("/validar")
async def validar_llave(llave: str):
    if llave != "12345":
        return {"error": "No autorizado"}
    return {"status": "acceso concedido"}
"""

@app.post("/api/auth/register", response_model=dict)
async def registrar_usuario(data: Objetos.UsuarioRegistro):
    # Verificar si el usuario o email ya existe en la colección 'users'
    usuario_existente = await db.users.find_one({"email": data.email})
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado."
        )

    # Hashear la contraseña antes de guardarla
    hashed_password = obtener_password_hash(data.password)

    nuevo_usuario = {
        "user_id": data.user_id,
        "nombre": data.nombre,
        "email": data.email,
        "password_hash": hashed_password,
        "rol": data.rol,
        "timestamp": datetime.now(timezone.utc),
    }

    await db.users.insert_one(nuevo_usuario)
    return estado[7]

@app.post("/api/auth/login", response_model=Objetos.Token)
async def login_usuario(data: Objetos.UsuarioLogin):
    # Buscar el usuario por email en MongoDB
    usuario = await db.users.find_one({"email": data.email})
    if not usuario or not verificar_password(data.password, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (email o contraseña inválidos).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar el token JWT incluyendo el id del usuario y su rol
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crear_access_token(
        data={"sub": usuario["user_id"], "email": usuario["email"], "rol": usuario.get("rol", "standard")},
        expires_delta=access_token_expires
    )
    estado[8]["access_token"] = access_token
    return estado[8]    

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


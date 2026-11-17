from pydantic import BaseModel as Esquema
from typing import Optional as Opcion

class SolicitudCambioPerfil(Esquema):
    id_controlador: str
    nombre_perfil: str
    receta_yaml: dict
    actualizado_por: str

class SolicitudUsuario(Esquema):
    id_usuario: str
    nombre: str
    email: str
    rol: Opcion[str] = "standard"

class SolicitudDispositivo(Esquema):
    id_dispositivo: str
    id_usuario: str
    nombre_dispositivo: str
    sistema_operativo: str = "windows 11"
    estado: Opcion[str] = "activo"

class UsuarioRegistro(Esquema):
    id_usuario_registro: str
    nombre: str
    email: str
    contraseña: str
    rol: Opcion[str] = "standard"

class UsuarioLogin(Esquema):
    email: str
    contraseña: str

class Token(Esquema):
    access_token: str
    token_type: str = "bearer"


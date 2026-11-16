from pydantic import BaseModel as esquema

class SolicitudCambioPerfil(esquema):
    id_controlador: str
    nombre_perfil: str
    receta_yaml: dict
    actualizado_por: str
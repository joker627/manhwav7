from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileResponse(BaseModel):
    id: int
    nombre_usuario: str
    correo: EmailStr
    xp: int = 0
    monedas: int = 0
    puntos_guerra: int = 0
    id_rango: int
    nombre: Optional[str] = None
    avatar_url: Optional[str] = None
    ultimo_ingreso: Optional[datetime] = None
    creado_en: datetime
    vip_expiracion: Optional[datetime] = None
    vip_activo: bool = False
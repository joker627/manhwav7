from app.core.database import get_db
from fastapi import Depends, HTTPException
from app.core.security import decode_token, oauth2_scheme
from mysql.connector import MySQLConnection
from fastapi.security import HTTPAuthorizationCredentials


# dependency to enforce role-based access control
def require_roles(*roles: str):
    def checker(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
        payload = decode_token(token.credentials)

        if not payload:
            raise HTTPException(status_code=401, detail="No autenticado")

        if roles and payload["role"] not in roles:
            raise HTTPException(status_code=403, detail="Permiso denegado")

        return payload

    return checker


# dependency to get current user info
def get_current_user(db: MySQLConnection = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="No autenticado")

    user_id = payload["sub"]  # el id del usuario lo guardaste en el token al hacer login

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT u.id, u.nombre_usuario, u.correo, u.xp, u.monedas, u.puntos_guerra, u.id_rango, r.nombre, "
        "u.avatar_url, u.ultimo_ingreso, u.creado_en, u.vip_expiracion FROM usuarios u LEFT JOIN rangos r ON u.id_rango = r.id WHERE u.id=%s",
        (user_id,)
    )
    user = cursor.fetchone()
    cursor.close()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user["role"] = "user"
    # Compute vip_activo based on vip_expiracion
    try:
        vip_ts = user.get('vip_expiracion')
        user['vip_activo'] = bool(vip_ts and vip_ts > __import__('datetime').datetime.now())
    except Exception:
        user['vip_activo'] = False

    return user
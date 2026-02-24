from fastapi import HTTPException
from app.core.security import verify_password, create_access_token


def login_user(db, email: str, password: str):
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT u.id, u.nombre_usuario, u.correo, u.clave_hash, u.id_rango, r.nombre "
            "FROM usuarios u LEFT JOIN rangos r ON u.id_rango = r.id WHERE u.correo=%s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not verify_password(password, user["clave_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        role = "user"

        token = create_access_token({
            "sub": str(user["id"]),
            "role": role,
            "id_rango": user.get("id_rango"),
            "rango_nombre": user.get("nombre")
        })

        # Update last_login
        cursor.execute(
            "UPDATE usuarios SET ultimo_ingreso = NOW() WHERE id = %s",
            (user["id"],)
        )
        db.commit()

        return token
    finally:
        cursor.close()

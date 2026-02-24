import json
from mysql.connector import Error
from app.core.database import db_pool
from fastapi import HTTPException


def get_db_connection():
    return db_pool.get_connection()


def pull_gacha(user_id: int, loteria_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # callproc returns the argument list with OUT params populated
        args = [user_id, loteria_id, None]
        result_args = cursor.callproc('pa_tirar_gacha', args)
        # OUT param is the third
        recompensa_json = result_args[2]
        conn.commit()
        if recompensa_json is None:
            return None
        # Try to parse JSON; if reward is structured, apply effects for certain types
        # Normalize recompensa to a dict when possible
        recompensa = None
        if isinstance(recompensa_json, str):
            try:
                recompensa = json.loads(recompensa_json)
            except Exception:
                recompensa = recompensa_json
        elif isinstance(recompensa_json, (bytes, bytearray)):
            try:
                recompensa = json.loads(recompensa_json.decode('utf-8'))
            except Exception:
                recompensa = recompensa_json
        else:
            recompensa = recompensa_json

        # If gacha returned a VIP reward, apply VIP expiration to user
        applied = {}
        try:
            tipo = recompensa.get('tipo') if isinstance(recompensa, dict) else None
            if tipo == 'vip':
                # valor is expected to be number of days
                dias = int(recompensa.get('valor', 0)) if recompensa.get('valor') is not None else 0
                if dias > 0:
                    # extend from current vip_expiracion if in future, else from now
                    cursor.execute(
                        "SELECT vip_expiracion FROM usuarios WHERE id = %s",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    current = row[0] if row else None
                    # Use MySQL DATE_ADD with GREATEST: update vip_expiracion = DATE_ADD(GREATEST(IFNULL(vip_expiracion, NOW()), NOW()), INTERVAL %s DAY)
                    cursor.execute(
                        "UPDATE usuarios SET vip_expiracion = DATE_ADD(GREATEST(COALESCE(vip_expiracion, NOW()), NOW()), INTERVAL %s DAY) WHERE id = %s",
                        (dias, user_id)
                    )
                    conn.commit()
            elif tipo == 'monedas':
                valor = int(recompensa.get('valor', 0)) if isinstance(recompensa, dict) and recompensa.get('valor') is not None else 0
                cantidad = int(recompensa.get('cantidad', 1)) if isinstance(recompensa, dict) and recompensa.get('cantidad') is not None else 1
                monedas_added = 0
                if valor:
                    monedas_added = valor * cantidad
                    cursor.execute("UPDATE usuarios SET monedas = monedas + %s WHERE id = %s", (monedas_added, user_id))
                    conn.commit()
                    applied['monedas_added'] = monedas_added
            elif tipo == 'xp':
                valor = int(recompensa.get('valor', 0)) if isinstance(recompensa, dict) and recompensa.get('valor') is not None else 0
                cantidad = int(recompensa.get('cantidad', 1)) if isinstance(recompensa, dict) and recompensa.get('cantidad') is not None else 1
                xp_added = 0
                if valor:
                    xp_added = valor * cantidad
                    cursor.execute("UPDATE usuarios SET xp = xp + %s WHERE id = %s", (xp_added, user_id))
                    conn.commit()
                    applied['xp_added'] = xp_added
        except Exception:
            # If applying reward fails, do not block returning the reward; rollback and return raw recompensa
            conn.rollback()
            recompensa['_applied'] = applied
            return recompensa

        # Attach a user-friendly message and current balances to the reward response
        if isinstance(recompensa, dict):
            # fetch current balances and vip expiration
            try:
                cursor.execute("SELECT monedas, xp, vip_expiracion FROM usuarios WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                # Ensure numeric balances are returned as integers (0 if NULL)
                monedas_actuales = int(row[0]) if row and row[0] is not None else 0
                xp_actuales = int(row[1]) if row and row[1] is not None else 0
                vip_exp = row[2] if row and len(row) > 2 and row[2] is not None else None
                recompensa['monedas_actuales'] = monedas_actuales
                recompensa['xp_actuales'] = xp_actuales
                recompensa['vip_expiracion'] = vip_exp.isoformat() if vip_exp is not None else None
                parts = []
                if 'monedas_added' in applied:
                    parts.append(f"Se añadieron {applied['monedas_added']} monedas")
                if 'xp_added' in applied:
                    parts.append(f"Se añadieron {applied['xp_added']} XP")
                if tipo == 'vip' and vip_exp:
                    parts.append(f"VIP activo hasta {vip_exp}")
                if not parts:
                    parts.append("Recompensa procesada")
                recompensa['message'] = '; '.join(parts)
            except Exception:
                recompensa['message'] = 'Recompensa procesada'
        return recompensa
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


def donate_to_clan(user_id: int, clan_id: int, amount: int, kind: str = 'monedas'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if kind == 'monedas':
            cursor.callproc('pa_donar_al_clan', [user_id, clan_id, amount])
            conn.commit()
            # Return updated balances: user monedas and clan tesoro
            cursor.execute("SELECT monedas FROM usuarios WHERE id = %s", (user_id,))
            user_row = cursor.fetchone()
            monedas_actuales = int(user_row[0]) if user_row and user_row[0] is not None else 0
            cursor.execute("SELECT tesoro_clan FROM clanes WHERE id = %s", (clan_id,))
            clan_row = cursor.fetchone()
            tesoro_clan = int(clan_row[0]) if clan_row and clan_row[0] is not None else 0
            return {"monedas_actuales": monedas_actuales, "tesoro_clan": tesoro_clan}
        elif kind == 'puntos':
            # Points donation handled in-app (no stored procedure). Validate membership and balance.
            # Check membership
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM miembros_clan WHERE id_clan = %s AND id_usuario = %s)",
                (clan_id, user_id)
            )
            exists = cursor.fetchone()[0]
            if not exists:
                raise HTTPException(status_code=400, detail='No eres miembro del clan')

            # Check user points
            cursor.execute("SELECT puntos_guerra FROM usuarios WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            puntos_actuales = int(row[0]) if row and row[0] is not None else 0
            if puntos_actuales < amount:
                raise HTTPException(status_code=400, detail='Puntos insuficientes')

            # Apply donation
            cursor.execute("UPDATE usuarios SET puntos_guerra = puntos_guerra - %s WHERE id = %s", (amount, user_id))
            cursor.execute("UPDATE clanes SET puntos_clan = puntos_clan + %s WHERE id = %s", (amount, clan_id))
            cursor.execute("UPDATE miembros_clan SET total_puntos_donados = total_puntos_donados + %s WHERE id_clan = %s AND id_usuario = %s", (amount, clan_id, user_id))
            conn.commit()

            # Return updated balances
            cursor.execute("SELECT puntos_guerra FROM usuarios WHERE id = %s", (user_id,))
            user_row = cursor.fetchone()
            puntos_actuales = int(user_row[0]) if user_row and user_row[0] is not None else 0
            cursor.execute("SELECT puntos_clan FROM clanes WHERE id = %s", (clan_id,))
            clan_row = cursor.fetchone()
            puntos_clan = int(clan_row[0]) if clan_row and clan_row[0] is not None else 0
            return {"puntos_actuales": puntos_actuales, "puntos_clan": puntos_clan}
        else:
            raise HTTPException(status_code=400, detail='Tipo de donación inválido')
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

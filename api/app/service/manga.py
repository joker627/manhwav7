import math
from app.core.config import settings
from app.core.database import db_pool


def get_db_connection():
    return db_pool.get_connection()


def get_manga_catalog(page=1, limit=20, search=None, status=None, format_type=None, sort_by='trending'):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Base queries
    count_query = "SELECT COUNT(*) as total FROM mangas"
    params = []

    if search:
        count_query = "SELECT COUNT(*) as total FROM mangas WHERE titulo LIKE %s"
        params = [f"%{search}%"]

    cursor.execute(count_query, params)
    total_results = cursor.fetchone()['total']

    # Build main query joining scan_groups and aggregating chapters
    query = (
        "SELECT m.id, m.titulo, NULL AS imagen_portada, c.nombre, "
        "COUNT(ch.id) AS total_capitulos, COALESCE(SUM(ch.vistas),0) AS total_vistas, MAX(ch.creado_en) AS ultima_actividad, "
        "(SELECT COUNT(*) FROM miembros_clan mc WHERE mc.id_clan = m.id_clan) AS member_count, "
        "(SELECT COUNT(*) FROM interacciones_contenido ic WHERE ic.tipo_contenido='manga' AND ic.id_contenido = m.id AND ic.accion='gusta') AS total_likes, "
        "(SELECT COUNT(*) FROM interacciones_contenido ic2 WHERE ic2.tipo_contenido='manga' AND ic2.id_contenido = m.id AND ic2.accion='seguir') AS total_follows, "
        "COALESCE((SELECT AVG(puntuacion) FROM calificaciones cal WHERE cal.id_manga = m.id), 0.0) AS avg_rating, "
        "(COALESCE(SUM(ch.vistas),0) + COALESCE((SELECT COUNT(*) FROM interacciones_contenido ic3 WHERE ic3.tipo_contenido='manga' AND ic3.id_contenido = m.id),0)) AS trending_score "
        "FROM mangas m "
        "LEFT JOIN clanes c ON m.id_clan = c.id "
        "LEFT JOIN capitulos ch ON ch.id_manga = m.id "
    )

    where_clauses = []
    q_params = []
    if search:
        where_clauses.append("m.titulo LIKE %s")
        q_params.append(f"%{search}%")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY m.id"

    sort_map = {
        'trending': 'total_vistas DESC',
        'views': 'total_vistas DESC',
        'az': 'm.titulo ASC',
        'new': 'm.id DESC'
    }

    order_clause = sort_map.get(sort_by, 'total_views DESC')
    query += f" ORDER BY {order_clause}"

    offset = (page - 1) * limit
    query += " LIMIT %s OFFSET %s"
    q_params.extend([limit, offset])

    cursor.execute(query, q_params)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = math.ceil(total_results / limit) if limit else 1

    return {
        "total": total_results,
        "pages": total_pages,
        "current_page": page,
        "results": result
    }


def get_manga_by_id(manga_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT m.id, m.titulo, NULL AS imagen_portada, m.id_clan, c.nombre, "
        "COUNT(ch.id) AS total_capitulos, COALESCE(SUM(ch.vistas),0) AS total_vistas, MAX(ch.creado_en) AS ultima_actividad, "
        "(SELECT COUNT(*) FROM miembros_clan mc WHERE mc.id_clan = m.id_clan) AS member_count, "
        "(SELECT COUNT(*) FROM interacciones_contenido ic WHERE ic.tipo_contenido='manga' AND ic.id_contenido = m.id AND ic.accion='gusta') AS total_likes, "
        "(SELECT COUNT(*) FROM interacciones_contenido ic2 WHERE ic2.tipo_contenido='manga' AND ic2.id_contenido = m.id AND ic2.accion='seguir') AS total_follows, "
        "COALESCE((SELECT AVG(puntuacion) FROM calificaciones cal WHERE cal.id_manga = m.id), 0.0) AS avg_rating, "
        "(COALESCE(SUM(ch.vistas),0) + COALESCE((SELECT COUNT(*) FROM interacciones_contenido ic3 WHERE ic3.tipo_contenido='manga' AND ic3.id_contenido = m.id),0)) AS trending_score "
        "FROM mangas m "
        "LEFT JOIN clanes c ON m.id_clan = c.id "
        "LEFT JOIN capitulos ch ON ch.id_manga = m.id "
        "WHERE m.id = %s GROUP BY m.id",
        (manga_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_chapters_by_manga(manga_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM capitulos WHERE id_manga = %s ORDER BY numero_capitulo", (manga_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_chapter_by_id(chapter_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM capitulos WHERE id = %s", (chapter_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_pages_by_chapter(chapter_id: int):
    # The current DB schema (manhwav7.sql) does not include a `pages` table.
    # Return an empty list until a pages storage/table is added.
    return []


def create_rating(user_id: int, rating):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Upsert rating (unique per user+manga)
        cursor.execute(
            """
            INSERT INTO calificaciones (id_usuario, id_manga, puntuacion)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE puntuacion = VALUES(puntuacion), creado_en = NOW()
            """,
            (user_id, rating.manga_id, rating.rating)
        )
        conn.commit()

        # Compute updated aggregate
        cursor.execute(
            "SELECT AVG(puntuacion) AS avg_rating, COUNT(*) AS total_ratings FROM calificaciones WHERE id_manga = %s",
            (rating.manga_id,)
        )
        agg = cursor.fetchone()

        return {
            "manga_id": rating.manga_id,
            "user_id": user_id,
            "puntuacion": float(rating.rating),
            "avg_rating": float(agg['avg_rating']) if agg and agg['avg_rating'] is not None else None,
            "total_ratings": int(agg['total_ratings']) if agg and agg['total_ratings'] is not None else 0
        }
    finally:
        cursor.close()
        conn.close()


def get_user_rating(user_id: int, manga_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT puntuacion AS rating, creado_en AS created_at FROM calificaciones WHERE id_usuario = %s AND id_manga = %s",
            (user_id, manga_id)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {"manga_id": manga_id, "user_id": user_id, "rating": float(row['rating']), "created_at": row['created_at']}
    finally:
        cursor.close()
        conn.close()


def like_manga(user_id: int, manga_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Toggle: if already liked -> remove; else -> insert
        cursor.execute(
            "SELECT 1 FROM interacciones_contenido WHERE id_usuario=%s AND tipo_contenido='manga' AND id_contenido=%s AND accion='gusta' LIMIT 1",
            (user_id, manga_id)
        )
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                "DELETE FROM interacciones_contenido WHERE id_usuario=%s AND tipo_contenido='manga' AND id_contenido=%s AND accion='gusta'",
                (user_id, manga_id)
            )
            conn.commit()
            action = 'unliked'
            liked = False
        else:
            cursor.execute(
                "INSERT INTO interacciones_contenido (id_usuario, tipo_contenido, id_contenido, accion) VALUES (%s, 'manga', %s, 'gusta')",
                (user_id, manga_id)
            )
            conn.commit()
            action = 'liked'
            liked = True

        cursor.execute(
            "SELECT COUNT(*) AS total_likes FROM interacciones_contenido WHERE tipo_contenido='manga' AND id_contenido=%s AND accion='gusta'",
            (manga_id,)
        )
        total = cursor.fetchone()
        return {"message": action, "liked": liked, "total_likes": int(total['total_likes'])}
    finally:
        cursor.close()
        conn.close()


def unlike_manga(user_id: int, manga_id: int):
    # kept for backward compatibility; performs explicit delete
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM interacciones_contenido WHERE id_usuario = %s AND tipo_contenido = 'manga' AND id_contenido = %s AND accion = 'gusta'",
            (user_id, manga_id)
        )
        conn.commit()
        return {"message": "Unliked"}
    finally:
        cursor.close()
        conn.close()


def follow_manga(user_id: int, manga_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Toggle follow: if already following -> unfollow; else -> follow
        cursor.execute(
            "SELECT 1 FROM interacciones_contenido WHERE id_usuario=%s AND tipo_contenido='manga' AND id_contenido=%s AND accion='seguir' LIMIT 1",
            (user_id, manga_id)
        )
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                "DELETE FROM interacciones_contenido WHERE id_usuario=%s AND tipo_contenido='manga' AND id_contenido=%s AND accion='seguir'",
                (user_id, manga_id)
            )
            conn.commit()
            action = 'unfollowed'
            following = False
        else:
            cursor.execute(
                "INSERT INTO interacciones_contenido (id_usuario, tipo_contenido, id_contenido, accion) VALUES (%s, 'manga', %s, 'seguir')",
                (user_id, manga_id)
            )
            conn.commit()
            action = 'followed'
            following = True

        cursor.execute(
            "SELECT COUNT(*) AS total_follows FROM interacciones_contenido WHERE tipo_contenido='manga' AND id_contenido=%s AND accion='seguir'",
            (manga_id,)
        )
        total = cursor.fetchone()
        return {"message": action, "following": following, "total_follows": int(total['total_follows'])}
    finally:
        cursor.close()
        conn.close()


def unfollow_manga(user_id: int, manga_id: int):
    # kept for backward compatibility; performs explicit delete
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM interacciones_contenido WHERE id_usuario = %s AND tipo_contenido = 'manga' AND id_contenido = %s AND accion = 'seguir'",
            (user_id, manga_id)
        )
        conn.commit()
        return {"message": "Unfollowed"}
    finally:
        cursor.close()
        conn.close()


def increment_views(chapter_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE capitulos SET vistas = vistas + 1 WHERE id = %s", (chapter_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "View incremented"}
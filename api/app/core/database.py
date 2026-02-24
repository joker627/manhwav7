# app/core/database.py
from mysql.connector import pooling
from app.core.config import settings

db_pool = pooling.MySQLConnectionPool(
    pool_name=settings.DB_POOL_NAME,
    pool_size=settings.DB_POOL_SIZE,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
    pool_reset_session=True,
    autocommit=True,
    connect_timeout=10
)

def get_db():
    conn = None
    try:
        conn = db_pool.get_connection()
        yield conn
    finally:
        if conn and conn.is_connected():
            conn.close()

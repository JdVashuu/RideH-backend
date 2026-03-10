import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize a connection pool
# minconn=1, maxconn=10 (adjust as needed for your traffic)
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

def get_connection():
    if connection_pool:
        return connection_pool.getconn()
    return psycopg2.connect(DATABASE_URL)

def release_connection(conn):
    if connection_pool:
        connection_pool.putconn(conn)
    else:
        conn.close()

def sqlite_execute(query, params=()):
    """Compatibility wrapper for PostgreSQL execute operations."""
    query = query.replace('?', '%s')
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)

def sqlite_query(query, params=()):
    """Compatibility wrapper for PostgreSQL fetching multiple rows."""
    query = query.replace('?', '%s')
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)

def sqlite_fetchone(query, params=()):
    """Compatibility wrapper for PostgreSQL fetching a single row."""
    query = query.replace('?', '%s')
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)

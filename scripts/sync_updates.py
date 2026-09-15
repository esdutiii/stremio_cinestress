import os
import sys
import re
import sqlite3
import requests

# Añadimos la raíz de stremio al sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.crypto import decode_p3_base64
from core.database import get_db_path

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

GITHUB_REPO_URL = "https://api.github.com/repos/Maniac2017/Mipal2025/contents"
RAW_BASE_URL = "https://raw.githubusercontent.com/Maniac2017/Mipal2025/main"

def init_tracking_table(conn, is_postgres=False):
    # Creamos una tabla para registrar los archivos .up que ya han sido aplicados
    cur = conn.cursor()
    if is_postgres:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applied_updates (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applied_updates (
                filename TEXT PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()

def is_update_applied(conn, filename, is_postgres=False):
    cur = conn.cursor()
    ph = "%s" if is_postgres else "?"
    cur.execute(f"SELECT 1 FROM applied_updates WHERE filename = {ph}", (filename,))
    return cur.fetchone() is not None

def mark_update_applied(conn, filename, is_postgres=False):
    cur = conn.cursor()
    ph = "%s" if is_postgres else "?"
    cur.execute(f"INSERT INTO applied_updates (filename) VALUES ({ph})", (filename,))
    conn.commit()

def apply_sql_to_postgres(pg_conn, sql_text):
    # Adaptamos las sentencias SQLite 'INSERT OR REPLACE INTO' para PostgreSQL
    cur = pg_conn.cursor()
    statements = sql_text.split(";\n")
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        
        # Adaptamos INSERT OR REPLACE INTO según la tabla
        if "INSERT OR REPLACE INTO pelis" in stmt:
            pg_stmt = stmt.replace("INSERT OR REPLACE INTO pelis", "INSERT INTO pelis")
            pg_stmt += " ON CONFLICT (tmdb) DO UPDATE SET titulo=EXCLUDED.titulo, plot=EXCLUDED.plot, poster=EXCLUDED.poster, rating=EXCLUDED.rating;"
        elif "INSERT OR REPLACE INTO series" in stmt:
            pg_stmt = stmt.replace("INSERT OR REPLACE INTO series", "INSERT INTO series")
            pg_stmt += " ON CONFLICT (tmdb) DO UPDATE SET titulo=EXCLUDED.titulo, plot=EXCLUDED.plot, poster=EXCLUDED.poster, rating=EXCLUDED.rating;"
        elif "INSERT OR REPLACE INTO version" in stmt:
            pg_stmt = stmt.replace("INSERT OR REPLACE INTO version", "INSERT INTO version") + " ON CONFLICT DO NOTHING;"
        else:
            pg_stmt = stmt.replace("INSERT OR REPLACE INTO", "INSERT INTO")
            if not pg_stmt.endswith(";"):
                pg_stmt += ";"
        
        try:
            cur.execute(pg_stmt)
        except Exception as err:
            pg_conn.rollback()
            continue

    pg_conn.commit()

def load_env_file():
    env_file = os.path.join(parent_dir, ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def clean_db_url(url):
    # Limpiamos espacios, comillas y parámetros incompatibles de libpq
    if not url:
        return ""
    u = url.strip().strip('"').strip("'")
    u = u.replace("&channel_binding=require", "").replace("channel_binding=require&", "").replace("channel_binding=require", "")
    return u.strip()

def sync():
    load_env_file()
    database_url = clean_db_url(os.environ.get("DATABASE_URL"))
    is_postgres = bool(database_url and POSTGRES_AVAILABLE)

    if is_postgres:
        print(f"Modo: Sincronización con PostgreSQL ({database_url.split('@')[-1]})")
        conn = psycopg2.connect(database_url)
    else:
        db_path = get_db_path()
        print(f"Modo: Sincronización con SQLite ({db_path})")
        conn = sqlite3.connect(db_path)

    init_tracking_table(conn, is_postgres)

    print("Consultando repositorio oficial de Kodi en GitHub (Maniac2017/Mipal2025)...")
    try:
        res = requests.get(GITHUB_REPO_URL, timeout=30)
        res.raise_for_status()
        items = res.json()
    except Exception as e:
        print(f"Error accediendo a GitHub: {e}")
        conn.close()
        return

    # Filtramos y ordenamos los archivos de actualización incremental .up1, .up2, etc.
    up_files = []
    for it in items:
        name = it.get("name", "")
        if ".up" in name:
            up_files.append(name)
    up_files.sort()

    print(f"Archivos de actualización encontrados en el repositorio: {up_files}")
    applied_count = 0

    for up_name in up_files:
        if is_update_applied(conn, up_name, is_postgres):
            print(f"- {up_name}: ya aplicado previamente.")
            continue

        print(f"Descargando y aplicando {up_name}...")
        try:
            url = f"{RAW_BASE_URL}/{up_name}"
            up_res = requests.get(url, timeout=30)
            if not up_res.ok:
                print(f"  Error descargando {up_name}: status {up_res.status_code}")
                continue

            # Decodificamos el SQL comprimido de Kodi
            sql_text = decode_p3_base64(up_res.text).decode("utf-8", errors="ignore")

            if is_postgres:
                apply_sql_to_postgres(conn, sql_text)
            else:
                cur = conn.cursor()
                cur.executescript(sql_text)
                conn.commit()

            mark_update_applied(conn, up_name, is_postgres)
            print(f"  [OK] {up_name} aplicado con exito.")
            applied_count += 1
        except Exception as err:
            print(f"  [ERROR] Error aplicando {up_name}: {err}")

    conn.close()
    if applied_count == 0:
        print("La base de datos ya estaba completamente al día.")
    else:
        print(f"Sincronización finalizada: se aplicaron {applied_count} actualizaciones nuevas.")

if __name__ == "__main__":
    sync()

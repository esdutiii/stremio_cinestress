import os
import sqlite3
from typing import Any

# Intentamos importar psycopg2 de manera opcional para entornos con PostgreSQL
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Cargamos variables de .env si existe en la carpeta raíz de stremio
_env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.isfile(_env_file):
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

from core.downloader import download_and_extract_moria

def get_db_path() -> str:
    # Determinamos la ubicación adecuada de moria.cm3 según el entorno
    env_path = os.environ.get("SQLITE_DB_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # Directorio stremio/data local
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_data_path = os.path.join(base_dir, "data", "moria.cm3")
    if os.path.isfile(local_data_path):
        return local_data_path

    # Directorio temporal de Vercel /tmp
    tmp_path = "/tmp/moria.cm3"
    if os.path.isfile(tmp_path):
        return tmp_path

    # Si estamos en Vercel o entorno sin BBDD local, descargamos en /tmp
    if os.path.exists("/tmp"):
        download_and_extract_moria(tmp_path)
        if os.path.isfile(tmp_path):
            return tmp_path

    # Si no existe localmente, intentamos descargar en local_data_path
    download_and_extract_moria(local_data_path)
    return local_data_path

def get_connection():
    # Conectamos a PostgreSQL si se ha definido DATABASE_URL
    database_url = os.environ.get("DATABASE_URL")
    if database_url and POSTGRES_AVAILABLE:
        return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)

    # De lo contrario conectamos a SQLite
    db_file = get_db_path()
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_movie_links(tmdb_id: int) -> list[dict[str, Any]]:
    # Obtenemos los enlaces disponibles para una película a partir de su ID de TMDB
    conn = get_connection()
    cursor = conn.cursor()
    database_url = os.environ.get("DATABASE_URL")
    
    # Adaptamos el placeholder según sea PostgreSQL (%s) o SQLite (?)
    placeholder = "%s" if database_url and POSTGRES_AVAILABLE else "?"
    query = f"SELECT link, calidad, audio, info FROM enlaces_pelis WHERE tmdb = {placeholder}"
    
    try:
        cursor.execute(query, (tmdb_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "link": r["link"],
                "calidad": r["calidad"] or "1080p",
                "audio": r["audio"] or "",
                "info": r["info"] or ""
            })
        return results
    finally:
        conn.close()

def get_series_links(tmdb_id: int, season: int, episode: int) -> list[dict[str, Any]]:
    # Obtenemos los enlaces para el capítulo específico de una serie
    conn = get_connection()
    cursor = conn.cursor()
    database_url = os.environ.get("DATABASE_URL")
    
    placeholder = "%s" if database_url and POSTGRES_AVAILABLE else "?"
    query = (
        f"SELECT link, calidad, audio, info FROM enlaces_series "
        f"WHERE tmdb = {placeholder} AND temporada = {placeholder} AND episodio = {placeholder}"
    )
    
    try:
        cursor.execute(query, (tmdb_id, season, episode))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "link": r["link"],
                "calidad": r["calidad"] or "1080p",
                "audio": r["audio"] or "",
                "info": r["info"] or ""
            })
        return results
    finally:
        conn.close()

def get_movie_title(tmdb_id: int) -> str:
    # Obtenemos el título de la película para enriquecer el nombre del stream
    conn = get_connection()
    cursor = conn.cursor()
    database_url = os.environ.get("DATABASE_URL")
    placeholder = "%s" if database_url and POSTGRES_AVAILABLE else "?"
    query = f"SELECT titulo FROM pelis WHERE tmdb = {placeholder} LIMIT 1"
    
    try:
        cursor.execute(query, (tmdb_id,))
        row = cursor.fetchone()
        return row["titulo"] if row else ""
    except Exception:
        return ""
    finally:
        conn.close()

import os
import sys
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("Error: Se requiere psycopg2-binary para migrar a PostgreSQL.")
    print("Instálalo con: pip install psycopg2-binary")
    sys.exit(1)

def load_env_file():
    # Cargamos las variables del archivo .env si existen
    env_file = os.path.join(parent_dir, ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def migrate():
    load_env_file()
    postgres_url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
    if not postgres_url:
        print("Error: Debes definir la variable de entorno DATABASE_URL.")
        print("Ejemplo: export DATABASE_URL='postgresql://usuario:pass@ep-cool.neon.tech/neondb?sslmode=require'")
        return

    sqlite_path = os.path.join(parent_dir, "data", "moria.cm3")
    if not os.path.isfile(sqlite_path):
        print(f"Error: No se encontró la base de datos SQLite en: {sqlite_path}")
        return

    print("Conectando a SQLite y PostgreSQL...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(postgres_url)
    pg_cur = pg_conn.cursor()

    print("Creando tablas en PostgreSQL si no existen...")
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS pelis (
            tmdb INTEGER PRIMARY KEY,
            titulo TEXT,
            plot TEXT,
            poster TEXT,
            fondo TEXT,
            categoria TEXT,
            genero TEXT,
            coleccion TEXT,
            duration INTEGER,
            updated TEXT,
            mpaa TEXT,
            fecha TEXT,
            trailer TEXT,
            clearlogo TEXT,
            rating TEXT
        );

        CREATE TABLE IF NOT EXISTS series (
            tmdb INTEGER PRIMARY KEY,
            titulo TEXT,
            plot TEXT,
            poster TEXT,
            fondo TEXT,
            categoria TEXT,
            genero TEXT,
            updated TEXT,
            mpaa TEXT,
            fecha TEXT,
            trailer TEXT,
            clearlogo TEXT,
            rating TEXT
        );

        CREATE TABLE IF NOT EXISTS enlaces_pelis (
            link TEXT,
            tmdb INTEGER,
            calidad TEXT,
            audio TEXT,
            info TEXT,
            updated TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_enlaces_pelis_tmdb ON enlaces_pelis(tmdb);

        CREATE TABLE IF NOT EXISTS enlaces_series (
            link TEXT,
            tmdb INTEGER,
            temporada INTEGER,
            episodio INTEGER,
            calidad TEXT,
            audio TEXT,
            info TEXT,
            updated TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_enlaces_series_tmdb ON enlaces_series(tmdb, temporada, episodio);
    """)
    pg_conn.commit()

    # Migración por lotes para tablas pesadas
    BATCH_SIZE = 5000

    tables_to_migrate = [
        ("pelis", 15, "INSERT INTO pelis VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tmdb) DO NOTHING"),
        ("series", 13, "INSERT INTO series VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tmdb) DO NOTHING"),
        ("enlaces_pelis", 6, "INSERT INTO enlaces_pelis VALUES (%s,%s,%s,%s,%s,%s)"),
        ("enlaces_series", 8, "INSERT INTO enlaces_series VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")
    ]

    for table_name, col_count, insert_sql in tables_to_migrate:
        print(f"Migrando tabla '{table_name}'...")
        sqlite_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = sqlite_cur.fetchone()[0]
        print(f"Total registros a migrar: {total}")

        sqlite_cur.execute(f"SELECT * FROM {table_name}")
        migrated = 0
        while True:
            rows = sqlite_cur.fetchmany(BATCH_SIZE)
            if not rows:
                break
            execute_batch(pg_cur, insert_sql, rows, page_size=BATCH_SIZE)
            pg_conn.commit()
            migrated += len(rows)
            print(f"  Progreso en {table_name}: {migrated}/{total}")

    print("¡Migración a PostgreSQL completada con éxito!")
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()

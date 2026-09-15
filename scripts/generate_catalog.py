import os
import sys
import json
import psycopg2
import psycopg2.extras

# Añadimos la raíz del proyecto para importar módulos si fuera necesario
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Intentamos cargar el archivo .env si existe localmente
env_file = os.path.join(parent_dir, ".env")
if os.path.isfile(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DATABASE_URL = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
DOCS_DATA_DIR = os.path.join(parent_dir, "docs", "data")

def format_poster(path):
    # Aseguramos que la URL del poster apunte a la CDN pública de TMDB
    if not path:
        return ""
    if path.startswith("http"):
        return path
    clean_path = path.lstrip("/")
    return f"https://image.tmdb.org/t/p/w500/{clean_path}"

def format_backdrop(path):
    # Formateamos la imagen de fondo en alta resolución
    if not path:
        return ""
    if path.startswith("http"):
        return path
    clean_path = path.lstrip("/")
    return f"https://image.tmdb.org/t/p/original/{clean_path}"

def clean_genres(genero_str):
    # Limpiamos los géneros separados por almohadilla
    if not genero_str:
        return []
    parts = [g.strip() for g in genero_str.replace("/", "#").split("#") if g.strip()]
    return parts

def clean_year(fecha_str):
    # Extraemos el año de la fecha
    if not fecha_str:
        return ""
    return str(fecha_str)[:4]

def process_rows(rows, default_type="movie"):
    # Procesamos los registros de la base de datos a un formato JSON limpio y ligero
    items = []
    for r in rows:
        item_type = r.get("type", default_type)
        items.append({
            "tmdb": r.get("tmdb"),
            "title": r.get("titulo") or "Sin título",
            "plot": r.get("plot") or "Sin sinopsis disponible.",
            "poster": format_poster(r.get("poster")),
            "backdrop": format_backdrop(r.get("fondo")),
            "category": r.get("categoria") or "",
            "genres": clean_genres(r.get("genero")),
            "year": clean_year(r.get("fecha")),
            "rating": str(r.get("rating") or "0")[:3],
            "updated": str(r.get("updated") or ""),
            "type": item_type
        })
    return items

def generate_catalog():
    if not DATABASE_URL:
        print("Error: No se encontró la variable DATABASE_URL.")
        sys.exit(1)

    os.makedirs(DOCS_DATA_DIR, exist_ok=True)
    print("Conectando a PostgreSQL en Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("Calculando estadísticas globales...")
    cur.execute("SELECT COUNT(*) as c FROM pelis")
    total_pelis = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM series")
    total_series = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM enlaces_pelis")
    enlaces_p = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM enlaces_series")
    enlaces_s = cur.fetchone()["c"]

    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM pelis WHERE categoria ILIKE '%anime%' OR genero ILIKE '%animación%') +
            (SELECT COUNT(*) FROM series WHERE categoria ILIKE '%anime%' OR genero ILIKE '%animación%') as c
    """)
    total_anime = cur.fetchone()["c"]

    cur.execute("SELECT MAX(updated) as max_up FROM pelis")
    row_up = cur.fetchone()
    last_update = str(row_up["max_up"] if row_up and row_up["max_up"] else "Recientemente")

    stats = {
        "total_movies": total_pelis,
        "total_series": total_series,
        "total_anime": total_anime,
        "total_links": enlaces_p + enlaces_s,
        "last_update": last_update
    }

    with open(os.path.join(DOCS_DATA_DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Estadísticas guardadas: {stats}")

    print("Obteniendo últimas películas...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
        FROM pelis
        WHERE poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC
        LIMIT 100
    """)
    movies_data = process_rows(cur.fetchall(), default_type="movie")
    with open(os.path.join(DOCS_DATA_DIR, "peliculas.json"), "w", encoding="utf-8") as f:
        json.dump(movies_data, f, ensure_ascii=False, indent=2)

    print("Obteniendo últimas series...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
        FROM series
        WHERE poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC
        LIMIT 100
    """)
    series_data = process_rows(cur.fetchall(), default_type="series")
    with open(os.path.join(DOCS_DATA_DIR, "series.json"), "w", encoding="utf-8") as f:
        json.dump(series_data, f, ensure_ascii=False, indent=2)

    print("Obteniendo contenido de anime...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis
         WHERE (categoria ILIKE '%anime%' OR genero ILIKE '%animación%' OR genero ILIKE '%animation%')
           AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series
         WHERE (categoria ILIKE '%anime%' OR genero ILIKE '%animación%' OR genero ILIKE '%animation%')
           AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC
        LIMIT 100
    """)
    anime_data = process_rows(cur.fetchall())
    with open(os.path.join(DOCS_DATA_DIR, "anime.json"), "w", encoding="utf-8") as f:
        json.dump(anime_data, f, ensure_ascii=False, indent=2)

    print("Obteniendo novedades combinadas...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis
         WHERE poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series
         WHERE poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC
        LIMIT 100
    """)
    novedades_data = process_rows(cur.fetchall())
    with open(os.path.join(DOCS_DATA_DIR, "novedades.json"), "w", encoding="utf-8") as f:
        json.dump(novedades_data, f, ensure_ascii=False, indent=2)

    conn.close()
    print("¡Catálogo generado exitosamente en docs/data/!")

if __name__ == "__main__":
    generate_catalog()

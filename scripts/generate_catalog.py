import os
import sys
import json
import hashlib
import base64
import psycopg2
import psycopg2.extras
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Añadimos la raíz del proyecto para importar módulos del core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.crypto import decrypt_link

# Intentamos cargar el archivo .env si existe localmente
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

DATABASE_URL = clean_db_url(os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL"))
DOCS_DATA_DIR = os.path.join(parent_dir, "docs", "data")

# Contraseña para cifrar los enlaces (por defecto 03Edu24 o variable de entorno)
CATALOG_PASSWORD = os.environ.get("CATALOG_PASSWORD", "03Edu24")
AES_KEY = hashlib.sha256(CATALOG_PASSWORD.encode("utf-8")).digest()
CIPHER_GCM = AESGCM(AES_KEY)

def encrypt_links_payload(links_list):
    # Ciframos la lista de enlaces en AES-GCM con la clave derivada de la contraseña
    if not links_list:
        return ""
    plaintext = json.dumps(links_list, ensure_ascii=False).encode("utf-8")
    iv = os.urandom(12)
    ciphertext = CIPHER_GCM.encrypt(iv, plaintext, None)
    return base64.b64encode(iv + ciphertext).decode("ascii")

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

def normalize_category(cat, item_type="movie"):
    # Normalizamos las categorías para corregir posibles caracteres de codificación
    if not cat:
        return "Película" if item_type == "movie" else "Serie"
    c = cat.lower()
    if "pel" in c:
        return "Película"
    if "mús" in c or "mus" in c or "ms" in c:
        return "Música"
    if "docu" in c:
        return "Documental"
    if "dibuj" in c:
        return "Dibujos"
    if "anim" in c:
        return "Anime"
    if "retro" in c:
        return "Retro"
    if "novel" in c:
        return "Telenovela"
    if "realit" in c:
        return "Reality"
    if "general" in c:
        return "Serie"
    return cat

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
            "category": normalize_category(r.get("categoria"), item_type),
            "genres": clean_genres(r.get("genero")),
            "year": clean_year(r.get("fecha")),
            "rating": str(r.get("rating") or "0")[:3],
            "updated": str(r.get("updated") or ""),
            "type": item_type,
            "links_enc": ""
        })
    return items

def attach_encrypted_links(cur, items):
    # Obtenemos y ciframos los enlaces de 1fichier para las películas y series de la lista
    if not items:
        return items

    movie_tmdbs = [it["tmdb"] for it in items if it.get("type") == "movie" and it.get("tmdb")]
    series_tmdbs = [it["tmdb"] for it in items if it.get("type") == "series" and it.get("tmdb")]
    links_by_tmdb = {}

    if movie_tmdbs:
        cur.execute("""
            SELECT tmdb, link, calidad, audio, info 
            FROM enlaces_pelis 
            WHERE tmdb = ANY(%s)
        """, (movie_tmdbs,))
        for r in cur.fetchall():
            t = r["tmdb"]
            if t not in links_by_tmdb:
                links_by_tmdb[t] = []
            try:
                dec_url = decrypt_link(r["link"])
            except Exception:
                dec_url = ""
            links_by_tmdb[t].append({
                "q": r.get("calidad") or "1080p",
                "a": r.get("audio") or "Castellano",
                "i": r.get("info") or "",
                "u": dec_url
            })

    if series_tmdbs:
        cur.execute("""
            SELECT tmdb, temporada, episodio, link, calidad, audio, info 
            FROM enlaces_series 
            WHERE tmdb = ANY(%s)
            ORDER BY temporada ASC, episodio ASC
        """, (series_tmdbs,))
        for r in cur.fetchall():
            t = r["tmdb"]
            if t not in links_by_tmdb:
                links_by_tmdb[t] = []
            try:
                dec_url = decrypt_link(r["link"])
            except Exception:
                dec_url = ""
            links_by_tmdb[t].append({
                "s": r.get("temporada") or 1,
                "e": r.get("episodio") or 1,
                "q": r.get("calidad") or "1080p",
                "a": r.get("audio") or "Castellano",
                "i": r.get("info") or "",
                "u": dec_url
            })

    for it in items:
        t = it.get("tmdb")
        it_links = links_by_tmdb.get(t, [])
        it["links_enc"] = encrypt_links_payload(it_links)

    return items

def generate_catalog():
    if not DATABASE_URL:
        print("Error: No se encontró la variable DATABASE_URL.")
        sys.exit(1)

    os.makedirs(DOCS_DATA_DIR, exist_ok=True)
    print("Conectando a PostgreSQL en Neon...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_client_encoding('UTF-8')
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("Calculando estadísticas globales por sección...")
    cur.execute("SELECT COUNT(*) as c FROM pelis WHERE categoria ILIKE '%pel%' OR categoria IS NULL OR categoria = ''")
    count_pelis = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM series WHERE categoria = 'General' OR categoria ILIKE '%serie%' OR categoria IS NULL OR categoria = ''")
    count_series = cur.fetchone()["c"]

    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM pelis WHERE categoria ILIKE '%anime%') +
            (SELECT COUNT(*) FROM series WHERE categoria ILIKE '%anime%') as c
    """)
    count_anime = cur.fetchone()["c"]

    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM pelis WHERE categoria ILIKE '%dibujo%') +
            (SELECT COUNT(*) FROM series WHERE categoria ILIKE '%dibujo%') as c
    """)
    count_dibujos = cur.fetchone()["c"]

    cur.execute("""
        SELECT 
            (SELECT COUNT(*) FROM pelis WHERE categoria ILIKE '%docu%') +
            (SELECT COUNT(*) FROM series WHERE categoria ILIKE '%docu%') as c
    """)
    count_docu = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM pelis WHERE categoria ILIKE '%mús%' OR categoria ILIKE '%mus%' OR categoria ILIKE '%ms%'")
    count_musica = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM series WHERE categoria ILIKE '%retro%' OR categoria ILIKE '%novel%' OR categoria ILIKE '%realit%'")
    count_retro = cur.fetchone()["c"]

    cur.execute("SELECT (SELECT COUNT(*) FROM enlaces_pelis) + (SELECT COUNT(*) FROM enlaces_series) as c")
    total_links = cur.fetchone()["c"]

    cur.execute("SELECT MAX(updated) as max_up FROM pelis")
    row_up = cur.fetchone()
    last_update = str(row_up["max_up"] if row_up and row_up["max_up"] else "Recientemente")

    stats = {
        "movies": count_pelis,
        "series": count_series,
        "anime": count_anime,
        "cartoons": count_dibujos,
        "documentaries": count_docu,
        "music": count_musica,
        "retro": count_retro,
        "total_links": total_links,
        "last_update": last_update
    }

    with open(os.path.join(DOCS_DATA_DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("Estadísticas guardadas con éxito.")

    # 1. Novedades globales combinadas
    print("1. Generando novedades con enlaces cifrados...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis WHERE poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series WHERE poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC LIMIT 100
    """)
    novedades = process_rows(cur.fetchall())
    attach_encrypted_links(cur, novedades)
    with open(os.path.join(DOCS_DATA_DIR, "novedades.json"), "w", encoding="utf-8") as f:
        json.dump(novedades, f, ensure_ascii=False, indent=2)

    # 2. Películas
    print("2. Generando películas con enlaces cifrados...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
        FROM pelis
        WHERE (categoria ILIKE '%pel%' OR categoria IS NULL OR categoria = '') AND poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC LIMIT 100
    """)
    pelis = process_rows(cur.fetchall(), "movie")
    attach_encrypted_links(cur, pelis)
    with open(os.path.join(DOCS_DATA_DIR, "peliculas.json"), "w", encoding="utf-8") as f:
        json.dump(pelis, f, ensure_ascii=False, indent=2)

    # 3. Series
    print("3. Generando series con enlaces cifrados...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
        FROM series
        WHERE (categoria = 'General' OR categoria ILIKE '%serie%' OR categoria IS NULL OR categoria = '') AND poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC LIMIT 100
    """)
    series = process_rows(cur.fetchall(), "series")
    attach_encrypted_links(cur, series)
    with open(os.path.join(DOCS_DATA_DIR, "series.json"), "w", encoding="utf-8") as f:
        json.dump(series, f, ensure_ascii=False, indent=2)

    # 4. Anime (Películas + Series)
    print("4. Generando anime con enlaces cifrados...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis WHERE categoria ILIKE '%anime%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series WHERE categoria ILIKE '%anime%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC LIMIT 100
    """)
    anime = process_rows(cur.fetchall())
    attach_encrypted_links(cur, anime)
    with open(os.path.join(DOCS_DATA_DIR, "anime.json"), "w", encoding="utf-8") as f:
        json.dump(anime, f, ensure_ascii=False, indent=2)

    # 5. Dibujos / Animación (Películas + Series)
    print("5. Generando dibujos animados con enlaces cifrados...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis WHERE categoria ILIKE '%dibujo%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series WHERE categoria ILIKE '%dibujo%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC LIMIT 100
    """)
    dibujos = process_rows(cur.fetchall())
    attach_encrypted_links(cur, dibujos)
    with open(os.path.join(DOCS_DATA_DIR, "dibujos.json"), "w", encoding="utf-8") as f:
        json.dump(dibujos, f, ensure_ascii=False, indent=2)

    # 6. Documentales (Películas + Series)
    print("6. Generando documentales con enlaces cifrados...")
    cur.execute("""
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
         FROM pelis WHERE categoria ILIKE '%docu%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        UNION ALL
        (SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
         FROM series WHERE categoria ILIKE '%docu%' AND poster IS NOT NULL AND poster != ''
         ORDER BY updated DESC LIMIT 50)
        ORDER BY updated DESC LIMIT 100
    """)
    docu = process_rows(cur.fetchall())
    attach_encrypted_links(cur, docu)
    with open(os.path.join(DOCS_DATA_DIR, "documentales.json"), "w", encoding="utf-8") as f:
        json.dump(docu, f, ensure_ascii=False, indent=2)

    # 7. Música (Conciertos / Películas musicales)
    print("7. Generando música con enlaces cifrados...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'movie' as type
        FROM pelis
        WHERE (categoria ILIKE '%mús%' OR categoria ILIKE '%mus%' OR categoria ILIKE '%ms%') AND poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC LIMIT 100
    """)
    musica = process_rows(cur.fetchall(), "movie")
    attach_encrypted_links(cur, musica)
    with open(os.path.join(DOCS_DATA_DIR, "musica.json"), "w", encoding="utf-8") as f:
        json.dump(musica, f, ensure_ascii=False, indent=2)

    # 8. Retro, Reality y Telenovelas
    print("8. Generando retro y telenovelas con enlaces cifrados...")
    cur.execute("""
        SELECT tmdb, titulo, plot, poster, fondo, categoria, genero, updated, fecha, rating, 'series' as type
        FROM series
        WHERE (categoria ILIKE '%retro%' OR categoria ILIKE '%novel%' OR categoria ILIKE '%realit%') AND poster IS NOT NULL AND poster != ''
        ORDER BY updated DESC LIMIT 100
    """)
    retro = process_rows(cur.fetchall(), "series")
    attach_encrypted_links(cur, retro)
    with open(os.path.join(DOCS_DATA_DIR, "retro.json"), "w", encoding="utf-8") as f:
        json.dump(retro, f, ensure_ascii=False, indent=2)

    conn.close()
    print("¡Todas las secciones generadas exitosamente con enlaces protegidos en docs/data/!")

if __name__ == "__main__":
    generate_catalog()

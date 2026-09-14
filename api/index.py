import os
import sys
import json
import base64
from flask import Flask, jsonify, request, redirect, Response, render_template_string

# Añadimos la raíz del proyecto al sys.path para importaciones relativas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.database import get_movie_links, get_series_links, get_movie_title
from core.crypto import decrypt_link
from core.id_mapper import get_tmdb_id
from core.resolvers import resolve_stream_url

app = Flask(__name__)

# Definimos el manifiesto base oficial de Stremio
ADDON_MANIFEST = {
    "id": "org.cinestress.1fichier",
    "version": "1.0.0",
    "name": "CineStress (1fichier / Debrid)",
    "description": "Enlaces 1fichier de películas y series procedentes de la BBDD de CineStress/Kodi, resueltos mediante 1fichier Premium, Real-Debrid o AllDebrid.",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": [],
    "idPrefixes": ["tt", "tmdb:"],
    "behaviorHints": {
        "configurable": True,
        "configurationRequired": False
    }
}

def parse_config(config_str: str | None) -> dict:
    # Decodificamos la configuración que Stremio envía en la URL
    if not config_str:
        return {}
    try:
        # Probamos decodificación base64 urlsafe
        padded = config_str + "=" * ((4 - len(config_str) % 4) % 4)
        raw_json = base64.urlsafe_b64decode(padded).decode("utf-8")
        return json.loads(raw_json)
    except Exception:
        # Si viene en formato clave=valor separado por comas
        cfg = {}
        parts = config_str.split(",")
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                cfg[k.strip()] = v.strip()
        return cfg

def get_effective_credentials(user_cfg: dict) -> tuple[str, dict]:
    # Determinamos el proveedor y las credenciales combinando la URL y las variables de entorno
    provider = user_cfg.get("provider") or os.environ.get("DEBRID_PROVIDER", "1fichier")
    credentials = {
        "1fichier_key": user_cfg.get("1fichier_key") or os.environ.get("ONEFICHIER_API_KEY", ""),
        "rd_token": user_cfg.get("rd_token") or os.environ.get("REALDEBRID_API_KEY", ""),
        "ad_key": user_cfg.get("ad_key") or os.environ.get("ALLDEBRID_API_KEY", ""),
        "api_key": user_cfg.get("api_key") or ""
    }
    return provider, credentials

def add_cors_headers(response: Response) -> Response:
    # Añadimos cabeceras CORS para compatibilidad con Stremio Web y aplicaciones nativas
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.after_request
def after_request(response: Response):
    return add_cors_headers(response)

@app.route("/")
@app.route("/configure")
def configure_page():
    # Servimos la interfaz gráfica de configuración
    static_file = os.path.join(parent_dir, "static", "index.html")
    if os.path.isfile(static_file):
        with open(static_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Addon CineStress activo. Visita /manifest.json para instalarlo.</h3>"

@app.route("/manifest.json")
@app.route("/<config>/manifest.json")
def manifest_endpoint(config=None):
    # Devolvemos el manifiesto del addon para que Stremio lo reconozca
    manifest = ADDON_MANIFEST.copy()
    user_cfg = parse_config(config)
    provider = user_cfg.get("provider", "1fichier")
    manifest["name"] = f"CineStress ({provider.capitalize()})"
    return jsonify(manifest)

@app.route("/stream/movie/<id_str>.json")
@app.route("/<config>/stream/movie/<id_str>.json")
def movie_stream_endpoint(id_str, config=None):
    # Atendemos la petición de streams para una película
    clean_id = id_str.replace(".json", "")
    tmdb_id = get_tmdb_id(clean_id, item_type="movie")
    if not tmdb_id:
        return jsonify({"streams": []})

    links = get_movie_links(tmdb_id)
    if not links:
        return jsonify({"streams": []})

    user_cfg = parse_config(config)
    provider, credentials = get_effective_credentials(user_cfg)
    host_url = request.host_url.rstrip("/")

    streams = []
    for i, item in enumerate(links):
        decrypted_url = decrypt_link(item["link"])
        if not decrypted_url or "1fichier" not in decrypted_url:
            continue

        # Generamos el token de reproducción diferida para resolver al hacer clic
        payload = {
            "url": decrypted_url,
            "provider": provider,
            "credentials": credentials
        }
        token = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        playback_url = f"{host_url}/playback/{token}"

        calidad = item["calidad"] or "1080p"
        audio = item["audio"] or "Castellano"
        info = item["info"] or ""
        desc_parts = [p for p in [audio, info] if p]
        details = " | ".join(desc_parts)

        streams.append({
            "name": f"CineStress [{calidad}]",
            "title": f"🎬 1fichier Servidor {i+1} ({calidad})\n🔊 Audio: {details}\n⚡ Reproducción directa vía {provider.capitalize()}",
            "url": playback_url,
            "behaviorHints": {
                "notWebReady": False
            }
        })

    return jsonify({"streams": streams})

@app.route("/stream/series/<id_str>.json")
@app.route("/<config>/stream/series/<id_str>.json")
def series_stream_endpoint(id_str, config=None):
    # Atendemos la petición de streams para series (formato id:temporada:episodio)
    clean_id = id_str.replace(".json", "")
    parts = clean_id.rsplit(":", 2)
    if len(parts) < 3:
        return jsonify({"streams": []})

    series_id = parts[0]
    try:
        season = int(parts[1])
        episode = int(parts[2])
    except ValueError:
        return jsonify({"streams": []})

    tmdb_id = get_tmdb_id(series_id, item_type="series")
    if not tmdb_id:
        return jsonify({"streams": []})

    links = get_series_links(tmdb_id, season, episode)
    if not links:
        return jsonify({"streams": []})

    user_cfg = parse_config(config)
    provider, credentials = get_effective_credentials(user_cfg)
    host_url = request.host_url.rstrip("/")

    streams = []
    for i, item in enumerate(links):
        decrypted_url = decrypt_link(item["link"])
        if not decrypted_url or "1fichier" not in decrypted_url:
            continue

        payload = {
            "url": decrypted_url,
            "provider": provider,
            "credentials": credentials
        }
        token = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        playback_url = f"{host_url}/playback/{token}"

        calidad = item["calidad"] or "1080p"
        audio = item["audio"] or "Castellano"
        info = item["info"] or ""
        desc_parts = [p for p in [audio, info] if p]
        details = " | ".join(desc_parts)

        streams.append({
            "name": f"CineStress [{calidad}]",
            "title": f"📺 T{season}xE{episode} - 1fichier Servidor {i+1} ({calidad})\n🔊 Audio: {details}\n⚡ Reproducción directa vía {provider.capitalize()}",
            "url": playback_url,
            "behaviorHints": {
                "notWebReady": False
            }
        })

    return jsonify({"streams": streams})

@app.route("/playback/<token>")
def playback_endpoint(token):
    # Endpoint invocado por el reproductor de vídeo de Stremio al pulsar Play
    try:
        padded = token + "=" * ((4 - len(token) % 4) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        raw_url = data.get("url")
        provider = data.get("provider", "1fichier")
        credentials = data.get("credentials", {})
        
        # Desrestringimos el enlace con el proveedor configurado
        result = resolve_stream_url(raw_url, provider, credentials)
        if result.get("success") and result.get("stream_url"):
            # Redirigimos el reproductor a la URL de streaming directa (HTTP 302)
            return redirect(result["stream_url"], code=302)

        error_msg = result.get("error", "No se pudo desrestringir el enlace.")
        return Response(f"Error al resolver vídeo: {error_msg}", status=502, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error interno en playback: {str(e)}", status=500, mimetype="text/plain")

@app.route("/health")
def health_endpoint():
    return jsonify({"status": "ok", "service": "CineStress Stremio Addon"})

if __name__ == "__main__":
    # Ejecución local de prueba
    port = int(os.environ.get("PORT", 7000))
    print(f"Iniciando addon de Stremio en http://localhost:{port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)

import os
import sys
import json
import base64

# Añadimos la ruta de stremio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app

def test_api_endpoints():
    client = app.test_client()
    
    print("1. Probando GET /manifest.json ...")
    res = client.get("/manifest.json")
    assert res.status_code == 200, f"Error en manifest: {res.status_code}"
    data = res.get_json()
    resource_names = [r if isinstance(r, str) else r.get("name") for r in data["resources"]]
    assert "stream" in resource_names
    assert "movie" in data["types"]
    print("   Manifest base valido.")

    print("2. Probando GET / con pagina de configuracion ...")
    res = client.get("/")
    assert res.status_code == 200
    assert "CineStress" in res.get_data(as_text=True)
    print("   Pagina de configuracion cargada correctamente.")

    print("3. Probando GET /stream/movie/tmdb:335977.json (Indiana Jones) ...")
    res = client.get("/stream/movie/tmdb:335977.json")
    assert res.status_code == 200
    stream_data = res.get_json()
    streams = stream_data.get("streams", [])
    print(f"   Streams devueltos para pelicula: {len(streams)}")
    assert len(streams) > 0, "Deberia devolver streams para la pelicula"
    first = streams[0]
    assert "url" in first
    assert "/playback/" in first["url"]
    assert "1fichier" in first["title"]
    print(f"   Ejemplo de stream: {first['name']}")

    # Probamos el endpoint /playback con el token generado
    token = first["url"].split("/playback/")[1]
    res_playback = client.get(f"/playback/{token}")
    # Con credenciales vacías o ficticias de test debe responder 502 Bad Gateway con mensaje explicativo
    assert res_playback.status_code in [302, 502]
    print(f"   Endpoint /playback respondio correctamente (status: {res_playback.status_code}).")

    print("4. Probando GET /stream/series/tmdb:1413:2:10.json (Serie T2E10) ...")
    res = client.get("/stream/series/tmdb:1413:2:10.json")
    assert res.status_code == 200
    series_streams = res.get_json().get("streams", [])
    print(f"   Streams devueltos para serie: {len(series_streams)}")
    assert len(series_streams) > 0, "Deberia devolver streams para la serie"
    print(f"   Ejemplo stream serie: {series_streams[0]['name']}")

    print("5. Probando GET /<config>/manifest.json con configuracion personalizada ...")
    cfg = {"provider": "realdebrid", "rd_token": "token_prueba"}
    cfg_b64 = base64.urlsafe_b64encode(json.dumps(cfg).encode("utf-8")).decode("utf-8").rstrip("=")
    res = client.get(f"/{cfg_b64}/manifest.json")
    assert res.status_code == 200
    custom_manifest = res.get_json()
    assert "Realdebrid" in custom_manifest["name"]
    print("   Manifiesto con configuracion personalizada verificado.")

    print("6. Probando endpoint /health ...")
    res = client.get("/health")
    assert res.status_code == 200
    print("   Health check OK.")

    print("Todas las pruebas de la API superadas exitosamente!")

if __name__ == "__main__":
    test_api_endpoints()

import requests
import json

base_url = "https://stremio-cinestress.vercel.app"

# Verificamos la configuracion
r_cfg = requests.get(f"{base_url}/debug/config", timeout=10)
print("Configuracion:", json.dumps(r_cfg.json(), indent=2))

# Obtenemos los streams
r_streams = requests.get(f"{base_url}/stream/movie/tt1375666.json", timeout=15)
data = r_streams.json()
streams = data.get("streams", [])
print(f"Streams recibidos: {len(streams)}")

if streams:
    first = streams[0]
    playback_url = first.get("url")
    print("URL de playback:", playback_url)
    
    # Probamos resolucion con allow_redirects=False
    r_play = requests.get(playback_url, allow_redirects=False, timeout=20)
    print("Codigo HTTP playback:", r_play.status_code)
    if r_play.status_code in [301, 302, 307, 308]:
        print("EXITO TOTAL: Redireccion 302 a:")
        print(r_play.headers.get("Location"))
    else:
        print("Respuesta de error:", r_play.text)

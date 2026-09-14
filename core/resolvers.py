import requests
from urllib.parse import quote_plus

def resolve_1fichier(url: str, api_key: str) -> dict:
    # Resolvemos directamente usando la API oficial de 1fichier para cuentas Premium
    if not api_key:
        return {"error": "Falta la API Key de 1fichier"}

    endpoint = "https://api.1fichier.com/v1/download/get_token.cgi"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {"url": url}

    try:
        res = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        data = res.json()
        if res.ok and data.get("status") == "OK" and "url" in data:
            return {"success": True, "stream_url": data["url"]}
        return {"error": data.get("message", "Error al resolver con 1fichier")}
    except Exception as e:
        return {"error": f"Excepción en 1fichier: {str(e)}"}

def resolve_realdebrid(url: str, api_token: str) -> dict:
    # Desrestringimos el enlace utilizando Real-Debrid
    if not api_token:
        return {"error": "Falta el token de Real-Debrid"}

    endpoint = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
    headers = {
        "Authorization": f"Bearer {api_token.strip()}"
    }
    payload = {"link": url}

    try:
        res = requests.post(endpoint, data=payload, headers=headers, timeout=15)
        data = res.json()
        if res.ok and "download" in data:
            return {"success": True, "stream_url": data["download"]}
        return {"error": data.get("message", "Error al resolver con Real-Debrid")}
    except Exception as e:
        return {"error": f"Excepción en Real-Debrid: {str(e)}"}

def resolve_alldebrid(url: str, api_key: str) -> dict:
    # Desrestringimos el enlace utilizando AllDebrid
    if not api_key:
        return {"error": "Falta la API Key de AllDebrid"}

    endpoint = f"https://api.alldebrid.com/v4/link/unlock?agent=StremioAddon&apikey={api_key.strip()}&link={quote_plus(url)}"

    try:
        res = requests.get(endpoint, timeout=15)
        data = res.json()
        if res.ok and data.get("status") == "success":
            download_url = data.get("data", {}).get("link")
            if download_url:
                return {"success": True, "stream_url": download_url}
        return {"error": data.get("error", {}).get("message", "Error al resolver con AllDebrid")}
    except Exception as e:
        return {"error": f"Excepción en AllDebrid: {str(e)}"}

def resolve_stream_url(url: str, provider: str, credentials: dict) -> dict:
    # Función unificada para seleccionar el proveedor correspondiente
    prov = (provider or "").lower().strip()
    if prov in ["1fichier", "one", "fichier"]:
        key = credentials.get("1fichier_key") or credentials.get("api_key")
        return resolve_1fichier(url, key)
    elif prov in ["realdebrid", "real-debrid", "rd"]:
        token = credentials.get("rd_token") or credentials.get("api_key")
        return resolve_realdebrid(url, token)
    elif prov in ["alldebrid", "all-debrid", "ad"]:
        key = credentials.get("ad_key") or credentials.get("api_key")
        return resolve_alldebrid(url, key)
    else:
        # Si no se especifica, intentamos según qué credenciales estén disponibles
        if credentials.get("rd_token"):
            return resolve_realdebrid(url, credentials["rd_token"])
        if credentials.get("1fichier_key"):
            return resolve_1fichier(url, credentials["1fichier_key"])
        if credentials.get("ad_key"):
            return resolve_alldebrid(url, credentials["ad_key"])
        return {"error": f"Proveedor no reconocido o sin credenciales: {provider}"}

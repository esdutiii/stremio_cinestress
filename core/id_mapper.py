import requests

# Diccionario en memoria para almacenar la equivalencia entre IMDb ID y TMDB ID
_IMDB_TO_TMDB_CACHE = {}

def get_tmdb_id(identifier: str, item_type: str = "movie") -> int | None:
    # Si el identificador ya viene con el prefijo de TMDB, lo extraemos directamente
    if identifier.startswith("tmdb:"):
        try:
            return int(identifier.split(":")[1])
        except (ValueError, IndexError):
            return None

    # Si es un número entero puro, lo interpretamos como TMDB
    if identifier.isdigit():
        return int(identifier)

    # Si es un identificador de IMDb (ej. tt0111161)
    if identifier.startswith("tt"):
        # Comprobamos si ya lo hemos consultado previamente
        if identifier in _IMDB_TO_TMDB_CACHE:
            return _IMDB_TO_TMDB_CACHE[identifier]

        # Consultamos el servicio público de metadatos de Cinemeta
        cinemeta_type = "series" if item_type in ["series", "tv"] else "movie"
        url = f"https://v3-cinemeta.strem.io/meta/{cinemeta_type}/{identifier}.json"

        try:
            res = requests.get(url, timeout=10)
            if res.ok:
                meta = res.json().get("meta", {})
                tmdb_id = meta.get("moviedb_id")
                if tmdb_id:
                    tmdb_id = int(tmdb_id)
                    _IMDB_TO_TMDB_CACHE[identifier] = tmdb_id
                    return tmdb_id
        except Exception as e:
            print(f"Error consultando Cinemeta para {identifier}: {e}")

    return None

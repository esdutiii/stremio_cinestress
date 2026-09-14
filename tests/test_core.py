import os
import sys

# Añadimos la ruta raíz de stremio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_movie_links, get_movie_title, get_series_links
from core.crypto import decrypt_link
from core.id_mapper import get_tmdb_id

def test_database_and_crypto():
    print("Probando base de datos y descifrado...")
    
    # Probamos con la película 335977 (Indiana Jones)
    tmdb_id = 335977
    links = get_movie_links(tmdb_id)
    title = get_movie_title(tmdb_id)
    print(f"Película TMDB {tmdb_id}: '{title}' - {len(links)} enlaces encontrados")
    assert len(links) > 0, "Debería haber al menos un enlace"
    
    for i, l in enumerate(links[:3]):
        dec = decrypt_link(l["link"])
        print(f"  {i+1}. [{l['calidad']}] ({l['audio']}): {dec}")
        assert "1fichier.com" in dec, f"El enlace descifrado debe contener 1fichier: {dec}"

    # Probamos con la serie TMDB 1413 (American Horror Story), Temporada 2, Episodio 10
    series_links = get_series_links(1413, 2, 10)
    print(f"Serie TMDB 1413 (T2E10) - {len(series_links)} enlaces encontrados")
    assert len(series_links) > 0, "Debería haber al menos un enlace para la serie"
    for i, l in enumerate(series_links[:3]):
        dec = decrypt_link(l["link"])
        print(f"  {i+1}. [{l['calidad']}] ({l['audio']}): {dec}")
        assert "1fichier.com" in dec, f"El enlace de la serie debe contener 1fichier: {dec}"

    # Probamos mapeo IMDb -> TMDB usando tt0111161 (Cadena perpetua -> TMDB 278)
    tmdb_from_imdb = get_tmdb_id("tt0111161", "movie")
    print(f"Mapeo IMDb tt0111161 -> TMDB ID: {tmdb_from_imdb}")
    assert tmdb_from_imdb == 278, f"Esperado 278, obtenido {tmdb_from_imdb}"

    print("¡Todas las pruebas del núcleo superadas con éxito!")

if __name__ == "__main__":
    test_database_and_crypto()

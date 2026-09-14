import os
import sys
import sqlite3

# Añadimos la raíz de stremio al sys.path para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.downloader import download_and_extract_moria

def main():
    target_path = os.path.join(parent_dir, "data", "moria.cm3")
    print(f"Ruta objetivo: {target_path}")
    
    success = download_and_extract_moria(target_path)
    if not success:
        print("No se pudo descargar la base de datos.")
        return

    print("Verificando contenido de la base de datos SQLite...")
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tablas encontradas ({len(tables)}): {tables}")

    for t in ["pelis", "series", "enlaces_pelis", "enlaces_series", "keys", "version"]:
        if t in tables:
            cursor.execute(f"PRAGMA table_info({t});")
            cols = [c[1] for c in cursor.fetchall()]
            cursor.execute(f"SELECT COUNT(*) FROM {t};")
            count = cursor.fetchone()[0]
            print(f"- {t} ({count} registros): {cols}")

    conn.close()

if __name__ == "__main__":
    main()

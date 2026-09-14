import os
import io
import base64
import zipfile
import sqlite3
import requests

from core.crypto import decode_p3_base64

GITHUB_REPO_URL = "https://api.github.com/repos/Maniac2017/Mipal2025/contents"
RAW_BASE_URL = "https://raw.githubusercontent.com/Maniac2017/Mipal2025/main"
ZIP_HEADER_B64 = b'UEsDBBQAAAAIAKJchVngR+RlsfTRAQBwSwUMAAAAc2V0dGluZ3MueG1s'

def download_and_extract_moria(target_db_path: str) -> bool:
    # Verificamos si ya existe el archivo en la ruta indicada
    if os.path.isfile(target_db_path) and os.path.getsize(target_db_path) > 1000:
        return True

    os.makedirs(os.path.dirname(target_db_path), exist_ok=True)
    print(f"Descargando base de datos moria hacia: {target_db_path} ...")

    try:
        # Obtenemos el listado de archivos del repositorio para ubicar el archivo .zm3 más reciente
        res = requests.get(GITHUB_REPO_URL, timeout=30)
        res.raise_for_status()
        contents = res.json()

        zm3_filename = None
        up_files = []
        for item in contents:
            name = item.get("name", "")
            if name.endswith(".zm3"):
                zm3_filename = name
            elif ".up" in name:
                up_files.append(name)

        if not zm3_filename:
            zm3_filename = "moria_3_3_11.zm3"

        file_url = f"{RAW_BASE_URL}/{zm3_filename}"
        print(f"Descargando paquete comprimido base desde {file_url} ...")

        download_res = requests.get(file_url, stream=True, timeout=120)
        download_res.raise_for_status()

        # Reconstruimos la cabecera zip que requiere el archivo zm3
        zip_header = base64.b64decode(ZIP_HEADER_B64)
        full_zip_bytes = zip_header + download_res.content

        # Descomprimimos el archivo 'settings.xml' que contiene la base de datos sqlite real
        with zipfile.ZipFile(io.BytesIO(full_zip_bytes), 'r') as zf:
            db_content = zf.read('settings.xml')

        with open(target_db_path, 'wb') as f:
            f.write(db_content)

        print(f"Base de datos descomprimida con éxito ({len(db_content)} bytes).")

        # Si hay archivos de actualización (.up1, .up2, etc.), los aplicamos a la base de datos
        if up_files:
            up_files.sort()
            print(f"Aplicando {len(up_files)} actualizaciones pendientes ({up_files})...")
            conn = sqlite3.connect(target_db_path)
            cur = conn.cursor()
            for up in up_files:
                try:
                    up_url = f"{RAW_BASE_URL}/{up}"
                    up_res = requests.get(up_url, timeout=30)
                    if up_res.ok:
                        sql_text = decode_p3_base64(up_res.text).decode('utf-8', errors='ignore')
                        cur.executescript(sql_text)
                        print(f"  Actualización {up} aplicada.")
                except Exception as up_err:
                    print(f"  Error aplicando {up}: {up_err}")
            conn.commit()
            conn.close()

        return True
    except Exception as e:
        print(f"Error descargando la base de datos: {e}")
        return False

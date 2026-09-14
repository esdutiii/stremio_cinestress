# Complemento de Stremio para 1fichier (BBDD CineStress / Moria)

Este complemento permite reproducir en **Stremio** el catálogo de películas y series de la base de datos de CineStress (anteriormente usada en Kodi), desencriptando al vuelo los enlaces de **1fichier** y desrestringiéndolos a través de:

- **1fichier Premium** (API oficial).
- **Real-Debrid** (API oficial / unrestrict).
- **AllDebrid** (API oficial / unlock).

---

## Estructura del Proyecto

```plaintext
stremio/
├── api/
│   └── index.py            # Servidor Flask compatible con Vercel Serverless y local
├── core/
│   ├── crypto.py           # Descifrado AES-256 (OFB) de enlaces
│   ├── database.py         # Acceso a datos (SQLite local/tmp o PostgreSQL)
│   ├── resolvers.py        # Clientes de 1fichier, Real-Debrid y AllDebrid
│   ├── id_mapper.py        # Mapeo de IMDb (tt...) a TMDB ID mediante Cinemeta
│   └── downloader.py       # Descargador automático de la base de datos moria.cm3
├── data/
│   └── moria.cm3           # Base de datos SQLite (29.000+ pelis, 8.800+ series, 1M+ enlaces)
├── static/
│   └── index.html          # Interfaz web de configuración e instalación en 1 clic
├── scripts/
│   ├── download_db.py      # Script para descargar o actualizar moria.cm3
│   └── migrate_to_postgres.py # Script para migrar datos a Neon o Supabase
├── tests/
│   └── test_core.py        # Pruebas unitarias del núcleo
├── requirements.txt        # Dependencias de Python
├── vercel.json             # Configuración para despliegue en Vercel
└── README.md               # Esta documentación
```

---

## Opción 1: Ejecución en Local (En tu ordenador)

### 1. Requisitos
- Python 3.10 o superior instalado.
- Instalar dependencias:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Base de datos
Si aún no tienes el archivo `stremio/data/moria.cm3`, descárgalo automáticamente con:
```bash
python stremio/scripts/download_db.py
```

### 3. Iniciar el servidor
```bash
python stremio/api/index.py
```
El servidor arrancará en `http://localhost:7000`.

### 4. Instalar en Stremio (en local)
1. Abre en tu navegador `http://localhost:7000`.
2. Selecciona tu proveedor (1fichier Premium, Real-Debrid o AllDebrid) e ingresa tu API Key / Token.
3. Haz clic en **"Copiar URL del Manifiesto para Stremio"** (copiará la URL `http://127.0.0.1:7000/.../manifest.json`).
4. Abre la aplicación de **Stremio**, ve a **Complementos** (icono de la pieza de puzzle 🧩 en el menú lateral).
5. Pega la URL en la **barra de búsqueda de complementos** (en la parte superior) y pulsa **Enter**.
6. Stremio mostrará la ventana del addon CineStress con un botón verde **"Instalar"**. Pulsa Instalar y ¡listo!

> **¿Por qué en local no se usa el botón directo `stremio://`?**  
> La aplicación de Stremio convierte internamente los enlaces `stremio://` en `https://` y descarta los puertos personalizados. Al estar ejecutando en tu ordenador mediante HTTP local (`http://127.0.0.1:7000`), el protocolo `stremio://` falla intentando conectar a HTTPS en el puerto 443. La forma oficial de Stremio para addons locales en desarrollo es pegar la URL `http://127.0.0.1:7000/.../manifest.json` en su buscador.  
> Al desplegar el addon en **Vercel** (que incluye certificado SSL HTTPS nativo), el botón directo `stremio://` funcionará con 1 solo clic en todos los dispositivos.

---

## Opción 2: Despliegue Gratuito en Vercel (Hobby)

Vercel permite alojar el addon de forma 100% gratuita y sin necesidad de mantener tu ordenador encendido.

### Paso 1: Subir el código a GitHub
Sube la carpeta `stremio` a un repositorio de GitHub (asegúrate de que `stremio/data/moria.cm3` está en `.gitignore` para no superar los 100 MB de GitHub).

### Paso 2: Elección de Base de Datos para Vercel
Tienes dos alternativas sencillas:

- **Opción A (SQLite en `/tmp` - Sin configurar nada)**:
  El código detecta automáticamente el entorno de Vercel y descarga `moria.cm3` en el directorio temporal `/tmp` de la función lambda la primera vez que se ejecuta.

- **Opción B (PostgreSQL Gratuito en Neon o Supabase - Recomendado para alta velocidad)**:
  1. Crea un proyecto gratuito en [Neon](https://neon.tech) o [Supabase](https://supabase.com).
  2. Obtén tu cadena de conexión `DATABASE_URL`.
  3. Ejecuta la migración desde tu ordenador:
     ```bash
     export DATABASE_URL="postgresql://usuario:pass@ep-cool.neon.tech/neondb?sslmode=require"
     python stremio/scripts/migrate_to_postgres.py
     ```
  4. En el panel de Vercel (Settings -> Environment Variables), añade la variable `DATABASE_URL`.

### Paso 3: Desplegar en Vercel
1. Conecta tu repositorio `esdutiii/stremio_cinestress` en [Vercel](https://vercel.com).
2. Root Directory: `./` (por defecto, la raíz del proyecto).
3. Añade la variable de entorno `DATABASE_URL` con tu enlace de Neon.
4. Haz clic en **Deploy**.
5. Una vez publicado, visita tu dominio de Vercel (`https://tu-addon.vercel.app`), ingresa tus claves y pulsa **Instalar en Stremio**.

---

## Cómo Funciona Internamente

1. **Consulta de Stremio**: Stremio solicita los streams de una película enviando su ID (por ejemplo `tt0111161` o `tmdb:278`).
2. **Mapeo de Identificadores**: Si el ID es de IMDb (`tt...`), el addon consulta Cinemeta para obtener el `moviedb_id` correspondiente y lo almacena en caché.
3. **Búsqueda en la Base de Datos**: Consulta `enlaces_pelis` o `enlaces_series` para obtener los enlaces cifrados asociados a ese TMDB ID.
4. **Descifrado AES**: Descifra los enlaces utilizando AES-256 en modo OFB, obteniendo la URL original de `1fichier.com`.
5. **Streams y Reproducción Inmediata**: El addon devuelve a Stremio la lista de calidades y audios con un endpoint de reproducción diferida (`/playback/{token}`). Cuando seleccionas el stream en Stremio, el servidor llama a la API del proveedor configurado (1fichier, Real-Debrid o AllDebrid) y redirige (`HTTP 302`) directamente al vídeo en el reproductor de Stremio.

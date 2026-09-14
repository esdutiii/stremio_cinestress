# CineStress Addon para Stremio (Debrid)

Este complemento permite reproducir en **Stremio** el inmenso catálogo de películas y series procedente de la base de datos de CineStress (anteriormente utilizada en Kodi), resolviendo y transmitiendo en streaming de alta velocidad mediante los servicios de:

- **AllDebrid** (API oficial).
- **Real-Debrid** (API oficial).

---

## 🚀 Instalación rápida en Stremio

Para instalar el complemento en cualquier dispositivo (PC, Android, Smart TV, iPad o iPhone):

1. Entra en la web de configuración del addon:  
   **[Web de Configuración de CineStress](https://cinestress.serveousercontent.com/?serveo-skip-browser-warning=true)** *(o mediante el despliegue en [Vercel](https://stremio-cinestress.vercel.app/))*.
2. Selecciona tu proveedor (**AllDebrid** o **Real-Debrid**) e introduce tu clave API.
3. Pulsa en **"Copiar URL del Manifiesto para Stremio"**.
4. Abre la aplicación de **Stremio**, ve a **Complementos (🧩)**, pega el enlace en la barra de búsqueda y pulsa **Instalar**.

> 📖 **¿Necesitas ayuda paso a paso?**  
> Consulta la [Guía de Instalación Detallada (GUIA_INSTALACION.md)](GUIA_INSTALACION.md), donde se explica cómo obtener las API Keys de AllDebrid (con 7 días gratis sin tarjeta) y Real-Debrid, además de instrucciones específicas para cada tipo de dispositivo.

---

## 📁 Estructura del Proyecto

```plaintext
stremio/
├── api/
│   └── index.py            # Servidor Flask compatible con túneles HTTPS y Vercel
├── core/
│   ├── crypto.py           # Descifrado AES-256 (OFB) de enlaces
│   ├── database.py         # Acceso a datos (PostgreSQL en Neon o SQLite)
│   ├── resolvers.py        # Clientes de resolución para Real-Debrid y AllDebrid
│   ├── id_mapper.py        # Mapeo de IMDb (tt...) a TMDB ID mediante Cinemeta
│   └── downloader.py       # Descargador auxiliar de base de datos
├── static/
│   └── index.html          # Interfaz web de configuración personalizada
├── scripts/
│   ├── download_db.py      # Script de descarga y sincronización
│   └── migrate_to_postgres.py # Migrador de SQLite a PostgreSQL (Neon / Supabase)
├── tests/
│   └── test_core.py        # Pruebas unitarias del motor
├── GUIA_INSTALACION.md     # Guía detallada para el usuario final
├── requirements.txt        # Dependencias del proyecto
├── vercel.json             # Configuración para despliegue en Vercel
└── README.md               # Esta documentación
```

---

## ⚙️ Opciones de Alojamiento y Despliegue

### Opción 1: Servidor 24/7 en Móvil Android (Termux + Serveo)
Esta opción es ideal porque utiliza una IP residencial (evitando restricciones de ciertos proveedores) y consume un mínimo de batería:

1. **Instalar paquetes y dependencias en Termux**:
   ```bash
   pkg update && pkg install python git openssh
   git clone https://github.com/esdutiii/stremio_cinestress.git
   cd stremio_cinestress
   pip install -r requirements.txt
   ```
2. **Configurar variables de entorno** en tu archivo `.env`:
   ```env
   DATABASE_URL=postgresql://usuario:pass@ep-cool.neon.tech/neondb?sslmode=require
   DEBRID_PROVIDER=alldebrid
   ALLDEBRID_API_KEY=tu_api_key
   PORT=7000
   ```
3. **Mantener Termux activo**:
   ```bash
   termux-wake-lock
   ```
4. **Arrancar el servidor** (Sesión 1):
   ```bash
   python api/index.py
   ```
5. **Abrir túnel permanente HTTPS** (Sesión 2):
   ```bash
   while true; do
     ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R cinestress:80:127.0.0.1:7000 serveo.net
     echo "Conexión perdida. Reconectando en 5 segundos..."
     sleep 5
   done
   ```

---

### Opción 2: Despliegue en Vercel (Serverless)

1. Conecta tu repositorio de GitHub en [Vercel](https://vercel.com).
2. Configura las variables de entorno en el panel de Vercel (Settings → Environment Variables):
   * `DATABASE_URL`: Cadena de conexión a tu base de datos PostgreSQL de Neon.
   * `DEBRID_PROVIDER`: `alldebrid` o `realdebrid`.
   * `ALLDEBRID_API_KEY` o `REALDEBRID_API_KEY`.
3. Despliega el proyecto. Vercel te proporcionará un dominio seguro con HTTPS automático (`https://tu-proyecto.vercel.app`).

---

## 🧠 Cómo Funciona Internamente

1. **Consulta de Stremio**: Stremio solicita los streams de una película o serie enviando su identificador (ejemplo: `tt0111161` o `tmdb:278`).
2. **Mapeo de IDs**: Si el identificador recibido es de IMDb (`tt...`), el addon consulta Cinemeta para obtener el `tmdb_id` equivalente.
3. **Búsqueda en Base de Datos**: Consulta las tablas de películas o episodios en PostgreSQL para obtener los enlaces almacenados.
4. **Descifrado AES**: Descifra los enlaces en memoria usando AES-256 en modo OFB.
5. **Resolución Debrid y Streaming**: El addon genera endpoints de reproducción diferida. Al pulsar Play en Stremio, el servidor conecta con la API de AllDebrid o Real-Debrid (usando la clave personalizada del usuario si la configuró en la web, o la clave por defecto del servidor) y redirige instantáneamente con un código `HTTP 302` al flujo de vídeo en máxima calidad.

---

## 💾 Descarga de Contenidos (Ver sin conexión)

Además de la reproducción directa en streaming, los contenidos resueltos por CineStress se pueden descargar al disco o dispositivo a la máxima velocidad de tu conexión:

### 1. Desde el reproductor de Stremio (PC / Escritorio)
* Durante la reproducción, hacemos clic en el icono de los **tres puntos (`...`)** en la esquina inferior derecha.
* **Descargar vídeo directamente:** Si aparece la opción **"Descargar este vídeo"**, pulsamos sobre ella para que el navegador inicie la descarga del archivo.
* **Mediante gestor de descargas:** Pulsamos en **"Copiar enlace de streaming"** (*Copy stream link*). Pegamos dicho enlace en el navegador o en programas como **JDownloader** o **Internet Download Manager (IDM)** para descargarlo a máxima velocidad.

### 2. Desde el panel web de Real-Debrid o AllDebrid (El método más cómodo)
Cada vez que abrimos un contenido en CineStress con nuestra cuenta Debrid configurada, el enlace desrestringido de alta velocidad queda guardado en el historial:
* **Real-Debrid:** Entramos en [real-debrid.com/downloads](https://real-debrid.com/downloads) y encontraremos la lista de archivos listos para descargar con un clic.
* **AllDebrid:** Accedemos a [alldebrid.com/saved-links](https://alldebrid.com/saved-links) para descargar los enlaces procesados.

### 3. En dispositivos móviles (Android)
* En los ajustes de Stremio activamos la opción de **"Reproductor externo"**.
* Al pulsar sobre el enlace, seleccionamos un gestor de descargas compatible (como **1DM** o **ADM**) para guardar la película o episodio directamente en el almacenamiento del dispositivo.

---


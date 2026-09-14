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

## 📄 Licencia

Desarrollado para la comunidad de streaming y entretenimiento.

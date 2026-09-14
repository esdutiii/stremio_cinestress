# Guía de Instalación y Configuración: CineStress Addon para Stremio

Esta guía explica paso a paso cómo obtener tu clave de acceso (API Key) en **AllDebrid** o **Real-Debrid**, cómo configurar el complemento en la web y cómo instalarlo en cualquier versión de **Stremio** (PC, Android, Android TV o iPad/iPhone).

---

## 1. Requisitos previos

Para poder utilizar este complemento necesitamos:
1. Una cuenta activa con suscripción en **AllDebrid** o **Real-Debrid**.
2. La aplicación **Stremio** instalada en tu dispositivo (o acceso a [web.stremio.com](https://web.stremio.com) si estás en iPad/iPhone).

---

## 2. Cómo obtener tu API Key

### Opción A: AllDebrid (Recomendado)
AllDebrid permite mayor flexibilidad de uso en varios dispositivos de la familia.

> 💡 **Prueba gratuita de 7 días:** Si aún no tienes cuenta, puedes registrarte en [alldebrid.com/register](https://alldebrid.com/register). Ofrecen 7 días de prueba gratis activándola simplemente mediante un código por SMS a tu móvil (**sin tener que poner tarjeta de crédito**).

1. Inicia sesión en tu cuenta en [alldebrid.com](https://alldebrid.com/).
2. Accede al apartado de claves API en: **[alldebrid.com/apikeys](https://alldebrid.com/apikeys/)**.
3. En el campo para crear una nueva clave, escribe un nombre para identificarla (por ejemplo: `Stremio`) y pulsa en **Crear**.
4. Copia la clave alfanumérica que se muestra en pantalla.

### Opción B: Real-Debrid
1. Inicia sesión en tu cuenta en [real-debrid.com](https://real-debrid.com/).
2. Entra directamente a la página de tu token: **[real-debrid.com/apitoken](https://real-debrid.com/apitoken)**.
3. Copia el código que aparece en el recuadro (una cadena larga de letras y números).

> **Aviso sobre Real-Debrid:** Real-Debrid no permite reproducir simultáneamente desde dos redes de internet distintas (dos casas diferentes a la vez). Si compartes tu cuenta con otra persona, aseguraos de no usarlo al mismo tiempo para evitar suspensiones automáticas.

---

## 3. Configuración del Addon en la Web

Una vez que tenemos nuestra API Key copiada:

1. Abrimos en el navegador de nuestro móvil, tablet o PC el enlace de configuración:
   ```text
   https://cinestress.serveousercontent.com/?serveo-skip-browser-warning=true
   ```
2. En el desplegable **Proveedor de Desrestricción**, seleccionamos nuestro servicio:
   * **AllDebrid (API Key)**
   * **Real-Debrid (Token API)**
3. Pegamos la clave que copiamos en el paso anterior en el campo correspondiente.
4. Hacemos clic en el botón azul: **"Copiar URL del Manifiesto para Stremio"**.
   *(Esto copiará al portapapeles un enlace personalizado con tu clave ya configurada).*

---

## 4. Instalación en Stremio

Con el enlace del manifiesto copiado en el portapapeles:

### En PC (Windows / Mac / Linux) o Android (Móvil / Tablet):
1. Abre la aplicación **Stremio**.
2. Ve al apartado de **Complementos** (el icono con forma de pieza de puzzle 🧩 en el menú lateral o superior).
3. En la **barra de búsqueda** situada arriba a la derecha (donde dice *"Buscar complementos"*), **pega el enlace** que acabas de copiar.
4. Pulsa la tecla `Enter` (o el icono de la lupa).
5. Aparecerá en pantalla el complemento **CineStress (Debrid)** con un botón que dice **Instalar**.
6. Haz clic en **Instalar** y confirma.

### En Smart TV (Android TV / Google TV / Fire TV):
La forma más cómoda es instalar el complemento primero en tu móvil o PC con la misma cuenta de Stremio que tienes en la tele. Al estar sincronizada la cuenta, el complemento aparecerá automáticamente instalado en tu televisión.

### En iPad o iPhone:
1. Abre Safari y entra en **[web.stremio.com](https://web.stremio.com)**.
2. Ve al menú de **Complementos (🧩)**.
3. Pega el enlace en la barra de búsqueda y pulsa **Instalar**.
4. *Nota:* Para reproducir en iOS, ve a Ajustes de Stremio Web y selecciona un reproductor externo como **VLC** o **Outplayer**.

---

## 5. Cómo reproducir contenido

1. En Stremio, busca cualquier película o serie que quieras ver.
2. En la columna lateral derecha donde se muestran los enlaces disponibles, verás los servidores de CineStress con sus calidades e idiomas:
   * `[CineStress 1080p] Servidor 1`
   * `Audio: Castellano`
3. Haz clic en cualquier enlace de la lista y el reproductor comenzará la reproducción directa a máxima velocidad sin esperas ni cortes.

---

## 6. Preguntas frecuentes y solución de problemas

* **¿Por qué me dice que el enlace no se puede resolver?**
  Comprueba que tu suscripción a AllDebrid o Real-Debrid no haya caducado y que hayas copiado la clave completa sin espacios al principio ni al final.
* **¿Puedo cambiar de cuenta o de clave más adelante?**
  Sí, simplemente vuelve a entrar en la web de configuración, introduce la nueva clave, copia el nuevo enlace e instálalo de nuevo en Stremio.
* **¿Se pueden descargar las películas o series para verlas sin conexión?**
  Sí. Puedes pulsar en los tres puntos del reproductor (`...`) y elegir *"Copiar enlace de streaming"* o *"Descargar este vídeo"*, o bien entrar directamente en el historial de tu cuenta en [Real-Debrid Downloads](https://real-debrid.com/downloads) o [AllDebrid Saved Links](https://alldebrid.com/saved-links), donde los enlaces generados quedan listos para descargar con un solo clic.
* **¿Por qué has hecho este addon, Edu?**
  Porque hay personas, inconscientes, inus, que se compran iphones y iPads y luego quieren ver pelis o series sin pagar 5 suscripciones... Y porque soy un tío majísimo.


## Made with ❤️ in Katowice by Eduardo


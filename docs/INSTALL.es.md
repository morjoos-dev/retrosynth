# Instalación de retrosynth

Esta guía explica cómo instalar y abrir **retrosynth** en Windows, macOS, Linux y otros sistemas.
No hace falta saber programar: en la mayoría de casos basta con instalar Python una vez y hacer
doble clic en un archivo.

> 🇬🇧 English version: [INSTALL.md](INSTALL.md)

## Índice

- [Lo que necesitas](#lo-que-necesitas)
- [Paso 1 · Descargar retrosynth](#paso-1--descargar-retrosynth)
- [Paso 2 · Instalar y abrir, según tu sistema](#paso-2--instalar-y-abrir-según-tu-sistema)
  - [Windows 10 y 11](#windows-10-y-11)
  - [macOS](#macos)
  - [Linux: Ubuntu, Debian, Linux Mint, Pop!_OS](#linux-ubuntu-debian-linux-mint-pop_os)
  - [Linux: Fedora](#linux-fedora)
  - [Linux: Arch, Manjaro, EndeavourOS](#linux-arch-manjaro-endeavouros)
  - [Linux: openSUSE](#linux-opensuse)
  - [Chromebook (ChromeOS)](#chromebook-chromeos)
  - [Raspberry Pi](#raspberry-pi)
  - [Windows con WSL](#windows-con-wsl)
  - [Docker (cualquier sistema)](#docker-cualquier-sistema)
- [Exportar a OGG y MP3: instalar ffmpeg](#exportar-a-ogg-y-mp3-instalar-ffmpeg)
- [Uso diario](#uso-diario)
- [Actualizar](#actualizar)
- [Desinstalar](#desinstalar)
- [Instalación para programadores](#instalación-para-programadores)
- [Solución de problemas](#solución-de-problemas)

---

## Lo que necesitas

| | |
| --- | --- |
| **Python 3.10 o más reciente** | Es gratuito. Abajo se explica cómo instalarlo en cada sistema. |
| **Un navegador** | Chrome, Edge, Firefox o Safari, en una versión reciente. |
| **Conexión a internet** | Solo la primera vez, para descargar las librerías (unos 60 MB). |
| **ffmpeg** *(opcional)* | Solo para exportar a OGG y MP3. Sin él, exporta a WAV. |

Todo funciona en tu ordenador: no se envía nada a ningún servidor.

## Paso 1 · Descargar retrosynth

**Opción fácil (sin Git):**

1. Abre la página del proyecto en GitHub: `https://github.com/morjoos-dev/retrosynth`
2. Pulsa el botón verde **Code** y después **Download ZIP**.
3. Descomprime el ZIP en una carpeta cómoda, por ejemplo `Documentos/retrosynth`.

**Con Git:**

```bash
git clone https://github.com/morjoos-dev/retrosynth.git
cd retrosynth
```

> En la carpeta verás `start-windows.bat`, `start-macos.command` y `start.sh`. Son los lanzadores:
> la primera vez preparan todo y las siguientes abren el estudio directamente.

---

## Paso 2 · Instalar y abrir, según tu sistema

### Windows 10 y 11

**1. Instala Python** (solo la primera vez). Elige una de estas dos formas:

- **Desde la web:** entra en <https://www.python.org/downloads/>, descarga la última versión y ábrela.
  En la primera pantalla del instalador **marca la casilla «Add python.exe to PATH»** y pulsa *Install Now*.
- **Con un comando:** abre PowerShell (busca «PowerShell» en el menú Inicio) y escribe:
  ```powershell
  winget install Python.Python.3.12
  ```

**2. Abre retrosynth:** en la carpeta del proyecto, haz **doble clic en `start-windows.bat`**.

- La primera vez tarda 1 o 2 minutos porque prepara todo. Las siguientes, unos segundos.
- Se abrirá el navegador con el estudio. **Deja abierta la ventana negra** mientras lo uses;
  para cerrar retrosynth, cierra esa ventana.

> Si Windows muestra «Windows protegió su PC», pulsa **Más información → Ejecutar de todas formas**.
> Pasa con cualquier archivo descargado de internet que no esté firmado.

### macOS

**1. Instala Python** (solo la primera vez). Elige una de estas dos formas:

- **Desde la web:** descarga el instalador de macOS en <https://www.python.org/downloads/> y ábrelo.
- **Con Homebrew** (si ya lo usas):
  ```bash
  brew install python
  ```

**2. Abre retrosynth:** en la carpeta del proyecto, haz **doble clic en `start-macos.command`**.

- **La primera vez**, macOS puede decir que no puede abrirlo porque es de un desarrollador no
  identificado. Haz **clic derecho sobre el archivo → Abrir → Abrir**. Solo hace falta una vez.
- Si dice que no tienes permiso, abre **Terminal**, arrastra la carpeta del proyecto a la ventana
  después de escribir `cd `, pulsa Intro y ejecuta:
  ```bash
  chmod +x start.sh start-macos.command
  ```
- Funciona en Mac con procesador Intel y con Apple Silicon (M1, M2, M3, M4…).

### Linux: Ubuntu, Debian, Linux Mint, Pop!_OS

Abre una terminal y escribe:

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg
cd ~/Descargas/retrosynth        # o la carpeta donde esté el proyecto
./start.sh
```

> `python3-venv` es necesario en estas distribuciones; si falta, el lanzador te lo recuerda.
> Ubuntu 22.04 o más reciente y Debian 12 o más reciente ya traen Python 3.10 o superior.

### Linux: Fedora

```bash
sudo dnf install python3 ffmpeg-free
cd ~/Descargas/retrosynth
./start.sh
```

### Linux: Arch, Manjaro, EndeavourOS

```bash
sudo pacman -S python ffmpeg
cd ~/Descargas/retrosynth
./start.sh
```

### Linux: openSUSE

```bash
sudo zypper install python311 ffmpeg
cd ~/Descargas/retrosynth
./start.sh
```

> En cualquier Linux, si `./start.sh` dice «Permiso denegado», ejecuta antes `chmod +x start.sh`
> (o usa `bash start.sh`).

### Chromebook (ChromeOS)

1. Activa Linux: **Configuración → Avanzado → Desarrolladores → Entorno de desarrollo de Linux → Activar**.
2. Copia la carpeta del proyecto a **Archivos de Linux** con la app *Archivos*.
3. Abre la app **Terminal** y sigue los pasos de [Ubuntu y Debian](#linux-ubuntu-debian-linux-mint-pop_os)
   (ChromeOS usa Debian).
4. Abre en Chrome la dirección que aparece en la terminal: `http://localhost:5177`.

### Raspberry Pi

Usa **Raspberry Pi OS de 64 bits** (Bookworm o más reciente) en una Raspberry Pi 4 o 5, y sigue los
pasos de [Ubuntu y Debian](#linux-ubuntu-debian-linux-mint-pop_os). La primera vez puede tardar
algo más. En la versión de 32 bits, numpy y scipy pueden tener que compilarse, lo que tarda mucho.

### Windows con WSL

Si usas WSL (el Linux integrado en Windows), dentro de WSL sigue los pasos de
[Ubuntu y Debian](#linux-ubuntu-debian-linux-mint-pop_os) y ejecuta `./start.sh --no-browser`.
Después abre `http://localhost:5177` en el navegador de Windows.

### Docker (cualquier sistema)

Si tienes [Docker](https://www.docker.com/products/docker-desktop/) instalado, no necesitas Python
ni ffmpeg. Desde la carpeta del proyecto:

```bash
docker build -t retrosynth .
docker run --rm -p 127.0.0.1:5177:5177 -v "$PWD/songs:/data/songs" -v "$PWD/output:/data/output" retrosynth
```

En PowerShell de Windows cambia `$PWD` por `${PWD}`. Después abre <http://localhost:5177>.
Tus temas se guardan en `songs/` y las exportaciones en `output/`, dentro de la carpeta del proyecto.

---

## Exportar a OGG y MP3: instalar ffmpeg

retrosynth siempre exporta a **WAV**. Para obtener también **OGG** (el formato que usan muchos
motores de juego) y **MP3**, instala ffmpeg:

| Sistema | Comando |
| --- | --- |
| Windows | `winget install Gyan.FFmpeg` (después, cierra y vuelve a abrir retrosynth) |
| macOS | `brew install ffmpeg` |
| Ubuntu / Debian / Mint | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg-free` |
| Arch / Manjaro | `sudo pacman -S ffmpeg` |
| Docker | ya viene incluido |

Si ffmpeg está instalado en un sitio poco habitual, indica su ruta en la variable de entorno
`FFMPEG` (por ejemplo, `FFMPEG=C:\ffmpeg\bin\ffmpeg.exe`).

## Uso diario

- **Abrir:** doble clic en el lanzador de tu sistema (o `./start.sh` en Linux). Se abre el navegador
  en <http://localhost:5177>.
- **Cerrar:** cierra la ventana de la terminal, o pulsa `Ctrl+C` en ella.
- **Dónde están tus archivos:** tus temas, en la carpeta `songs/`; lo exportado, en `output/`.
  Las dos están dentro de la carpeta del proyecto.
- **Usar otro puerto** (si el 5177 está ocupado): `start-windows.bat --port 8000` o `./start.sh --port 8000`.

## Actualizar

- **Si lo descargaste como ZIP:** descarga el ZIP nuevo, descomprímelo y copia dentro tus carpetas
  `songs/` y `output/`.
- **Si usas Git:** `git pull`.

Si después de actualizar algo falla, borra la carpeta oculta `.venv` y vuelve a abrir el lanzador:
reinstalará todo desde cero.

## Desinstalar

Borra la carpeta del proyecto. Todo lo que instala retrosynth está dentro de ella, en la carpeta
oculta `.venv`. Python y ffmpeg se quedan instalados en el sistema por si los usas para otras cosas;
se desinstalan como cualquier otro programa.

## Instalación para programadores

Si prefieres instalarlo como un paquete de Python normal:

```bash
pip install -e ".[dev]"     # desde la carpeta del proyecto, idealmente dentro de un venv
retrosynth studio           # abre el estudio
retrosynth render crystal_cave -f wav,ogg
retrosynth list
pytest                      # tests
```

Con [pipx](https://pipx.pypa.io/) puedes instalar la herramienta aislada sin descargar el proyecto:
`pipx install git+https://github.com/morjoos-dev/retrosynth.git`.

Si la orden `retrosynth` no se encuentra, usa `python -m retrosynth`, que funciona siempre.

---

## Solución de problemas

<details>
<summary><b>«Python 3.10 or newer was not found» aunque he instalado Python</b></summary>

- **Windows:** probablemente no marcaste «Add python.exe to PATH». Vuelve a abrir el instalador de
  Python, elige *Modify* y activa *Add Python to environment variables*, o instálalo con
  `winget install Python.Python.3.12`. Después cierra y vuelve a abrir el lanzador.
- **Linux/macOS:** comprueba la versión con `python3 --version`. Si es inferior a 3.10, instala una más
  reciente con el gestor de paquetes de tu sistema.
</details>

<details>
<summary><b>Al escribir <code>python</code>, Windows abre la Microsoft Store</b></summary>

Es un acceso directo de Windows que solo sirve para instalar Python. Instala Python como se explica
arriba o desactívalo en **Configuración → Aplicaciones → Configuración avanzada de aplicaciones →
Alias de ejecución de aplicaciones**, apagando «python.exe» y «python3.exe».
</details>

<details>
<summary><b>«ensurepip is not available» o «No module named venv» (Linux)</b></summary>

Falta el paquete de entornos virtuales: `sudo apt install python3-venv` y vuelve a ejecutar `./start.sh`.
</details>

<details>
<summary><b>La instalación falla al descargar las librerías</b></summary>

Comprueba la conexión a internet (o el proxy de tu empresa) y vuelve a abrir el lanzador:
si la instalación se interrumpe, el lanzador empieza de cero automáticamente.
</details>

<details>
<summary><b>El navegador no se abre solo</b></summary>

Abre tú mismo la dirección <http://localhost:5177>. Mientras la ventana de la terminal siga abierta,
el estudio está funcionando.
</details>

<details>
<summary><b>«Address already in use» o el puerto 5177 está ocupado</b></summary>

Probablemente retrosynth ya está abierto en otra ventana; ciérrala. O usa otro puerto:
`./start.sh --port 8000` (en Windows, `start-windows.bat --port 8000`) y abre `http://localhost:8000`.
</details>

<details>
<summary><b>No suena nada</b></summary>

- Pulsa **▶ Escuchar** al menos una vez: los navegadores no permiten reproducir sonido hasta que haces clic en la página.
- Comprueba el control **Volumen** de la barra superior y el volumen del sistema.
- Si la pestaña del navegador muestra un altavoz tachado, haz clic en él para quitar el silencio.
</details>

<details>
<summary><b>Exportar solo crea el WAV</b></summary>

Falta ffmpeg: mira [Exportar a OGG y MP3](#exportar-a-ogg-y-mp3-instalar-ffmpeg). Después de
instalarlo, cierra y vuelve a abrir retrosynth.
</details>

<details>
<summary><b>macOS: «no se puede abrir porque procede de un desarrollador no identificado»</b></summary>

Haz clic derecho sobre `start-macos.command` → **Abrir** → **Abrir**. Si aun así no deja, ve a
**Ajustes del Sistema → Privacidad y seguridad** y pulsa **Abrir igualmente**.
</details>

<details>
<summary><b>Linux/macOS: «Permiso denegado» al ejecutar <code>./start.sh</code></b></summary>

`chmod +x start.sh start-macos.command`, o ejecútalo con `bash start.sh`.
</details>

<details>
<summary><b>La página se ve en blanco o sin colores en el editor de código</b></summary>

La interfaz descarga las fuentes y el editor de código de internet. Sin conexión, el estudio sigue
funcionando, pero con un editor de texto sencillo. Recarga la página cuando vuelvas a tener conexión.
</details>

¿Sigue sin funcionar? Abre una *issue* en GitHub y pega el texto que aparece en la ventana de la terminal.

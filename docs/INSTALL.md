# Installing retrosynth

This guide shows how to install and open **retrosynth** on Windows, macOS, Linux and other systems.
No programming knowledge is needed: in most cases you install Python once and double-click a file.

> 🇪🇸 Versión en español: [INSTALL.es.md](INSTALL.es.md)

## Contents

- [What you need](#what-you-need)
- [Step 1 · Download retrosynth](#step-1--download-retrosynth)
- [Step 2 · Install and open it on your system](#step-2--install-and-open-it-on-your-system)
  - [Windows 10 and 11](#windows-10-and-11)
  - [macOS](#macos)
  - [Linux: Ubuntu, Debian, Linux Mint, Pop!_OS](#linux-ubuntu-debian-linux-mint-pop_os)
  - [Linux: Fedora](#linux-fedora)
  - [Linux: Arch, Manjaro, EndeavourOS](#linux-arch-manjaro-endeavouros)
  - [Linux: openSUSE](#linux-opensuse)
  - [Chromebook (ChromeOS)](#chromebook-chromeos)
  - [Raspberry Pi](#raspberry-pi)
  - [Windows with WSL](#windows-with-wsl)
  - [Docker (any system)](#docker-any-system)
- [Exporting OGG and MP3: install ffmpeg](#exporting-ogg-and-mp3-install-ffmpeg)
- [Everyday use](#everyday-use)
- [Updating](#updating)
- [Uninstalling](#uninstalling)
- [Developer install](#developer-install)
- [Troubleshooting](#troubleshooting)

---

## What you need

| | |
| --- | --- |
| **Python 3.10 or newer** | Free. How to install it on each system is explained below. |
| **A web browser** | A recent Chrome, Edge, Firefox or Safari. |
| **Internet access** | Only the first time, to download the libraries (about 60 MB). |
| **ffmpeg** *(optional)* | Only to export OGG and MP3. Without it you get WAV. |

Everything runs on your own computer: nothing is sent to any server.

## Step 1 · Download retrosynth

**Easy way (no Git):**

1. Open the project page on GitHub: `https://github.com/morjoos-dev/retrosynth`
2. Click the green **Code** button, then **Download ZIP**.
3. Unzip it somewhere convenient, for example `Documents/retrosynth`.

**With Git:**

```bash
git clone https://github.com/morjoos-dev/retrosynth.git
cd retrosynth
```

> The folder contains `start-windows.bat`, `start-macos.command` and `start.sh`. These are the
> launchers: the first time they set everything up, and after that they open the studio directly.

---

## Step 2 · Install and open it on your system

### Windows 10 and 11

**1. Install Python** (first time only). Choose one:

- **From the website:** go to <https://www.python.org/downloads/>, download the latest version and run it.
  On the first screen of the installer **tick "Add python.exe to PATH"**, then click *Install Now*.
- **With a command:** open PowerShell (search for "PowerShell" in the Start menu) and type:
  ```powershell
  winget install Python.Python.3.12
  ```

**2. Open retrosynth:** in the project folder, **double-click `start-windows.bat`**.

- The first time takes 1–2 minutes to set everything up; after that, a few seconds.
- Your browser opens the studio. **Keep the black window open** while you use it; close it to quit.

> If Windows shows "Windows protected your PC", click **More info → Run anyway**. This happens with
> any unsigned file downloaded from the internet.

### macOS

**1. Install Python** (first time only). Choose one:

- **From the website:** download the macOS installer from <https://www.python.org/downloads/> and run it.
- **With Homebrew** (if you already use it):
  ```bash
  brew install python
  ```

**2. Open retrosynth:** in the project folder, **double-click `start-macos.command`**.

- **The first time**, macOS may say it cannot be opened because it is from an unidentified developer.
  **Right-click the file → Open → Open**. You only need to do this once.
- If it says you don't have permission, open **Terminal**, type `cd ` (with a space), drag the
  project folder onto the window, press Enter and run:
  ```bash
  chmod +x start.sh start-macos.command
  ```
- Works on Intel Macs and on Apple Silicon (M1, M2, M3, M4…).

### Linux: Ubuntu, Debian, Linux Mint, Pop!_OS

Open a terminal and run:

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg
cd ~/Downloads/retrosynth        # or wherever the project folder is
./start.sh
```

> `python3-venv` is required on these distributions; the launcher reminds you if it is missing.
> Ubuntu 22.04+ and Debian 12+ already ship Python 3.10 or newer.

### Linux: Fedora

```bash
sudo dnf install python3 ffmpeg-free
cd ~/Downloads/retrosynth
./start.sh
```

### Linux: Arch, Manjaro, EndeavourOS

```bash
sudo pacman -S python ffmpeg
cd ~/Downloads/retrosynth
./start.sh
```

### Linux: openSUSE

```bash
sudo zypper install python311 ffmpeg
cd ~/Downloads/retrosynth
./start.sh
```

> On any Linux, if `./start.sh` says "Permission denied", run `chmod +x start.sh` first (or use `bash start.sh`).

### Chromebook (ChromeOS)

1. Turn on Linux: **Settings → Advanced → Developers → Linux development environment → Turn on**.
2. Copy the project folder to **Linux files** with the *Files* app.
3. Open the **Terminal** app and follow the [Ubuntu and Debian](#linux-ubuntu-debian-linux-mint-pop_os)
   steps (ChromeOS uses Debian).
4. Open the address shown in the terminal in Chrome: `http://localhost:5177`.

### Raspberry Pi

Use **64-bit Raspberry Pi OS** (Bookworm or newer) on a Raspberry Pi 4 or 5, and follow the
[Ubuntu and Debian](#linux-ubuntu-debian-linux-mint-pop_os) steps. The first setup can take a bit
longer. On 32-bit systems numpy and scipy may need to be compiled, which is very slow.

### Windows with WSL

If you use WSL (Linux inside Windows), follow the [Ubuntu and Debian](#linux-ubuntu-debian-linux-mint-pop_os)
steps inside WSL, run `./start.sh --no-browser`, then open `http://localhost:5177` in your Windows browser.

### Docker (any system)

With [Docker](https://www.docker.com/products/docker-desktop/) you need neither Python nor ffmpeg.
From the project folder:

```bash
docker build -t retrosynth .
docker run --rm -p 127.0.0.1:5177:5177 -v "$PWD/songs:/data/songs" -v "$PWD/output:/data/output" retrosynth
```

In Windows PowerShell use `${PWD}` instead of `$PWD`. Then open <http://localhost:5177>. Your songs are
kept in `songs/` and exports in `output/`, inside the project folder.

---

## Exporting OGG and MP3: install ffmpeg

retrosynth always exports **WAV**. To also get **OGG** (used by many game engines) and **MP3**,
install ffmpeg:

| System | Command |
| --- | --- |
| Windows | `winget install Gyan.FFmpeg` (then close and reopen retrosynth) |
| macOS | `brew install ffmpeg` |
| Ubuntu / Debian / Mint | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg-free` |
| Arch / Manjaro | `sudo pacman -S ffmpeg` |
| Docker | already included |

If ffmpeg lives somewhere unusual, set the `FFMPEG` environment variable to its full path.

## Everyday use

- **Open:** double-click your system's launcher (or `./start.sh` on Linux). The browser opens
  <http://localhost:5177>.
- **Quit:** close the terminal window, or press `Ctrl+C` in it.
- **Where your files are:** your songs are in `songs/` and exports in `output/`, both inside the project folder.
- **Use another port** (if 5177 is taken): `start-windows.bat --port 8000` or `./start.sh --port 8000`.

## Updating

- **ZIP download:** download the new ZIP, unzip it and copy your `songs/` and `output/` folders into it.
- **Git:** `git pull`.

If something fails after updating, delete the hidden `.venv` folder and open the launcher again:
it reinstalls everything from scratch.

## Uninstalling

Delete the project folder. Everything retrosynth installs lives inside it, in the hidden `.venv` folder.
Python and ffmpeg stay on your system in case you use them for other things; remove them like any
other program.

## Developer install

To install it as a regular Python package:

```bash
pip install -e ".[dev]"     # from the project folder, ideally inside a venv
retrosynth studio           # open the studio
retrosynth render crystal_cave -f wav,ogg
retrosynth list
pytest                      # run the tests
```

With [pipx](https://pipx.pypa.io/) you can install the tool in isolation without downloading the
project: `pipx install git+https://github.com/morjoos-dev/retrosynth.git`.

If the `retrosynth` command is not found, `python -m retrosynth` always works.

---

## Troubleshooting

<details>
<summary><b>"Python 3.10 or newer was not found" although Python is installed</b></summary>

- **Windows:** you probably did not tick "Add python.exe to PATH". Run the Python installer again,
  choose *Modify* and enable *Add Python to environment variables*, or install it with
  `winget install Python.Python.3.12`. Then close and reopen the launcher.
- **Linux/macOS:** check the version with `python3 --version`. If it is older than 3.10, install a newer
  one with your system's package manager.
</details>

<details>
<summary><b>Typing <code>python</code> on Windows opens the Microsoft Store</b></summary>

That is a Windows shortcut that only offers to install Python. Install Python as described above, or
turn it off in **Settings → Apps → Advanced app settings → App execution aliases** (switch off
"python.exe" and "python3.exe").
</details>

<details>
<summary><b>"ensurepip is not available" or "No module named venv" (Linux)</b></summary>

The virtual-environment package is missing: `sudo apt install python3-venv`, then run `./start.sh` again.
</details>

<details>
<summary><b>Setup fails while downloading the libraries</b></summary>

Check your internet connection (or your company proxy) and open the launcher again: if setup is
interrupted, the launcher automatically starts over.
</details>

<details>
<summary><b>The browser does not open by itself</b></summary>

Open <http://localhost:5177> yourself. As long as the terminal window is open, the studio is running.
</details>

<details>
<summary><b>"Address already in use" / port 5177 is busy</b></summary>

retrosynth is probably already open in another window; close it. Or use another port:
`./start.sh --port 8000` (Windows: `start-windows.bat --port 8000`) and open `http://localhost:8000`.
</details>

<details>
<summary><b>There is no sound</b></summary>

- Click **▶ Play** at least once: browsers only allow audio after you interact with the page.
- Check the **Volume** slider in the top bar and your system volume.
- If the browser tab shows a muted speaker icon, click it to unmute.
</details>

<details>
<summary><b>Export only creates the WAV file</b></summary>

ffmpeg is missing: see [Exporting OGG and MP3](#exporting-ogg-and-mp3-install-ffmpeg). After
installing it, close and reopen retrosynth.
</details>

<details>
<summary><b>macOS: "cannot be opened because it is from an unidentified developer"</b></summary>

Right-click `start-macos.command` → **Open** → **Open**. If that is not offered, go to
**System Settings → Privacy & Security** and click **Open Anyway**.
</details>

<details>
<summary><b>Linux/macOS: "Permission denied" when running <code>./start.sh</code></b></summary>

`chmod +x start.sh start-macos.command`, or run it with `bash start.sh`.
</details>

<details>
<summary><b>The code editor looks plain, without colours</b></summary>

The page loads its fonts and code editor from the internet. Offline, the studio still works with a
simple text editor. Reload the page once you are back online.
</details>

Still stuck? Open an issue on GitHub and paste the text shown in the terminal window.

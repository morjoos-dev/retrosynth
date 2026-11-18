#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  retrosynth studio - launcher for Linux and macOS:   ./start.sh
#  The first time it creates a private Python environment in the ".venv"
#  folder and installs retrosynth into it (needs internet, takes 1-2 minutes).
#  Extra arguments are passed on, e.g.  ./start.sh --port 8000
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"
VENV=".venv"

if [ ! -f "$VENV/.installed" ]; then
  echo
  echo "  retrosynth - first-time setup (only once, 1-2 minutes)"
  echo "  ------------------------------------------------------"
  PY=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PY="$candidate"
      break
    fi
  done
  if [ -z "$PY" ]; then
    echo
    echo "  Python 3.10 or newer was not found."
    echo "  See docs/INSTALL.md for how to install it on your system, then run this again."
    exit 1
  fi

  rm -rf "$VENV"
  echo "  Creating the Python environment..."
  if ! "$PY" -m venv "$VENV"; then
    rm -rf "$VENV"
    echo
    echo "  Could not create the Python environment."
    echo "  On Debian, Ubuntu, Mint or Raspberry Pi OS run:  sudo apt install python3-venv"
    exit 1
  fi
  echo "  Installing retrosynth and its libraries..."
  "$VENV/bin/python" -m pip install --disable-pip-version-check -q --upgrade pip
  if ! "$VENV/bin/python" -m pip install --disable-pip-version-check -q -e .; then
    rm -rf "$VENV"
    echo
    echo "  Setup failed: read the messages above. See docs/INSTALL.md (Troubleshooting)."
    exit 1
  fi
  touch "$VENV/.installed"
  echo "  Done."
fi

echo
echo "  Starting retrosynth studio in your browser..."
echo "  Keep this terminal open while you use it. Press Ctrl+C to stop."
echo
exec "$VENV/bin/python" -m retrosynth studio "$@"

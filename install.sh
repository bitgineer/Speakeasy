#!/usr/bin/env sh
# SpeakEasy bootstrap for macOS and Linux.
# Ensures uv and Python 3.12 exist, then hands off to install.py.

set -e
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  export PATH
fi

uv python install 3.12
PY="$(uv python find 3.12)"
exec "$PY" ./install.py "$@"

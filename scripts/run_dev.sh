#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PY=python3
VENV_DIR=.venv

if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] creating venv..."
  $PY -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install -U pip
pip install -r requirements.txt

echo "[versions]"
python -c "import fastapi, pydantic; print('fastapi', fastapi.__version__, 'pydantic', pydantic.__version__)"
which uvicorn

exec "$VENV_DIR/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port 8000

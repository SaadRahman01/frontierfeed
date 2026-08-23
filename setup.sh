#!/usr/bin/env bash
# One-shot local setup. Run from the repo root:  ./setup.sh
set -euo pipefail

cd "$(dirname "$0")"
echo "Setting up frontierfeed in $(pwd)"
echo

# --- Python check -----------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python not found. Install Python 3.10 or newer from https://python.org"
  exit 1
fi

VERSION=$($PY -c 'import sys; print("%d.%d" % sys.version_info[:2])')
MAJOR=${VERSION%%.*}
MINOR=${VERSION##*.}
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
  echo "Found Python $VERSION, but this needs 3.10 or newer."
  exit 1
fi
echo "Python $VERSION"

# --- Virtual environment ----------------------------------------------------
if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# --- First run --------------------------------------------------------------
echo
echo "Fetching sources. A 403 or timeout on one source is fine — the run"
echo "continues on whatever else responds."
echo
python -m src.main

# --- Open the result --------------------------------------------------------
PAGE="$(pwd)/docs/index.html"
echo
echo "Done. Site written to:"
echo "  $PAGE"
echo
echo "Next time, activate the environment first:"
echo "  source .venv/bin/activate && python -m src.main"

if command -v open >/dev/null 2>&1; then
  open "$PAGE"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$PAGE" >/dev/null 2>&1 || true
fi

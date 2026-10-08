#!/usr/bin/env bash
# Range Drill - start the server for the local Wi-Fi network (macOS / Linux).
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "First start: creating the environment, this takes a minute..."
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements-local.txt || echo "Warning: could not install/update packages. Trying to start anyway..."
exec .venv/bin/python serve.py "$@"

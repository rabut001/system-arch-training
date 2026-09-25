#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --user -r .devcontainer/requirements.txt

if [[ -f web/package.json ]]; then
  npm install --prefix web
fi

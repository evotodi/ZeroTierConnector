#!/usr/bin/env bash
set -euo pipefail

if ! command -v poetry >/dev/null 2>&1; then
  echo "poetry not found. Installing..."
  if command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="${HOME}/.local/bin:${PATH}"
  else
    echo "Cannot install poetry automatically: curl and python3 are required."
    echo "Install them and rerun."
    exit 1
  fi
fi

if ! poetry run python -c "import requests, pydantic, click" >/dev/null 2>&1; then
  echo "Installing dependencies with poetry..."
  poetry install
fi

if ! command -v sshpass >/dev/null 2>&1; then
  echo "sshpass not found. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    if [ "${EUID}" -eq 0 ]; then
      apt-get update
      apt-get install -y sshpass
    elif command -v sudo >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y sshpass
    else
      echo "Cannot install sshpass automatically: sudo is not available."
      echo "Install it manually and rerun."
      exit 1
    fi
  else
    echo "Automatic sshpass install is only implemented for apt-get systems."
    echo "Install sshpass manually and rerun."
    exit 1
  fi
fi

exec poetry run zerotier-connector "$@"

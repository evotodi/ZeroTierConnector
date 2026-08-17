#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing..."
  if command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    curl -sSL https://astral.sh/uv/install.sh | sh
  else
    echo "Cannot install uv automatically: curl and python3 are required."
    echo "Install them and rerun."
    exit 1
  fi
fi

if ! uv run python -c "import requests, pydantic, click" >/dev/null 2>&1; then
  echo "Installing dependencies with uv..."
  uv sync
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

exec uv run zerotier-connector "$@"

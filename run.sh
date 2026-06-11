#!/bin/bash

# Kairos - Run script for development mode

set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv --system-site-packages
fi

# Activate virtual environment
source .venv/bin/activate

# Instala dependências só quando requirements.txt muda (ou no 1º run).
# Evita rede + latência a cada launch; o stamp guarda o hash já instalado.
STAMP=".venv/.req-stamp"
REQ_HASH="$(sha256sum requirements.txt | cut -d' ' -f1)"
if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP" 2>/dev/null)" != "$REQ_HASH" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt || { echo "Erro: falha ao instalar dependências"; exit 1; }
    echo "$REQ_HASH" > "$STAMP"
fi

# Run the application in background
echo "Starting Kairos..."

nohup python -m kairos.main > /dev/null 2>&1 < /dev/null &

# Save PID
echo $! > kairos.pid
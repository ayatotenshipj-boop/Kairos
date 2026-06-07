#!/bin/bash
# Kairos — build standalone via Nuitka 4.1.2
# Gera: dist/kairos (binário único, sem dependências externas)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativa o venv (obrigatório — PySide6 vem do sistema via --system-site-packages)
if [ ! -d ".venv" ]; then
    echo "ERRO: .venv não encontrado."
    echo "Crie com: python -m venv .venv --system-site-packages"
    exit 1
fi

source .venv/bin/activate

# Instala dependências de build se necessário
if ! python -m nuitka --version &>/dev/null; then
    echo "Instalando dependências de build (requirements-dev.txt)..."
    pip install -r requirements-dev.txt
fi

echo "Nuitka: $(python -m nuitka --version 2>&1 | head -1)"
echo "Python: $(python --version)"
echo ""
echo "Iniciando build..."

python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-qt-plugins=sensible,styles,platforms \
    --include-data-files=kairos/ui/styles.qss:kairos/ui/styles.qss \
    --follow-imports \
    --output-filename=kairos \
    --output-dir=dist \
    kairos/main.py

echo ""
echo "Build concluído! Binário em: dist/kairos"

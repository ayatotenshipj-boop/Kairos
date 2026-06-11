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
export PATH="$HOME/.local/bin:$PATH"

# Instala dependências de build se necessário
if ! python -m nuitka --version &>/dev/null; then
    echo "Instalando dependências de build (requirements-dev.txt)..."
    pip install -r requirements-dev.txt
fi

echo "Nuitka: $(python -m nuitka --version 2>&1 | head -1)"
echo "Python: $(python --version)"
echo ""
echo "Iniciando build..."

# NOTA: yt-dlp NÃO é empacotado — é chamado como CLI (subprocess), não importado.
# O binário distribuído exige yt-dlp no PATH em runtime para baixar áudio do
# YouTube; sem ele, só funcionam legendas prontas e PDF/áudio local.
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-qt-plugins=sensible,styles,platforms,qml \
    --include-data-dir=kairos/ui/qml=kairos/ui/qml \
    --include-data-dir=kairos/images=kairos/images \
    --include-data-files=kairos/config/prompts.json=kairos/config/prompts.json \
    --linux-onefile-icon=kairos/images/kairos_linux_256x256.png \
    --follow-imports \
    --include-package=pymupdf \
    --include-package=pymupdf4llm \
    --include-package=notebooklm \
    --include-package=google.genai \
    --include-package=faster_whisper \
    --include-package=ctranslate2 \
    --include-package=av \
    --include-package=pypresence \
    --output-filename=kairos \
    --output-dir=dist \
    kairos/main.py

echo ""
echo "Build concluído! Binário em: dist/kairos"

#!/bin/bash
# Kairos — build standalone via Nuitka 4.1.2 (multi-SO)
# Detecta o SO e seleciona as flags compatíveis do Nuitka:
#   Linux   → dist/kairos        (--onefile, ícone PNG)
#   Windows → dist/kairos.exe    (--onefile, ícone ICO, sem console)
#   macOS   → dist/Kairos.app    (app bundle; --onefile não é suportado no macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Detecção de SO ─────────────────────────────────────────────────────────
case "$(uname -s)" in
    Linux*)               OS="linux" ;;
    Darwin*)              OS="macos" ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
    *) echo "ERRO: SO não suportado para build: $(uname -s)"; exit 1 ;;
esac
echo "SO detectado: $OS"

# ── Ativa o venv (layout difere no Windows) ────────────────────────────────
# Linux: criar com --system-site-packages (PySide6 vem do pacman).
# Windows/macOS: venv normal (PySide6 via pip).
if [ ! -d ".venv" ]; then
    echo "ERRO: .venv não encontrado."
    echo "  Linux:         python -m venv .venv --system-site-packages"
    echo "  Windows/macOS: python -m venv .venv"
    exit 1
fi

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate          # Linux / macOS
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate      # Windows (Git Bash / MSYS)
else
    echo "ERRO: activate do venv não encontrado (.venv/bin nem .venv/Scripts)."
    exit 1
fi

export PATH="$HOME/.local/bin:$PATH"

# Instala dependências de build se necessário
if ! python -m nuitka --version &>/dev/null; then
    echo "Instalando dependências de build (requirements-dev.txt)..."
    pip install -r requirements-dev.txt
fi

echo "Nuitka: $(python -m nuitka --version 2>&1 | head -1)"
echo "Python: $(python --version)"

# ── Flags comuns a todos os SOs ────────────────────────────────────────────
NUITKA_ARGS=(
    --standalone
    --enable-plugin=pyside6
    --include-qt-plugins=sensible,styles,platforms,qml
    --include-data-dir=kairos/ui/qml=kairos/ui/qml
    --include-data-dir=kairos/images=kairos/images
    --include-data-files=kairos/config/prompts.json=kairos/config/prompts.json
    --follow-imports
    --include-package=kairos.platform
    --include-package=pymupdf
    --include-package=pymupdf4llm
    --include-package=notebooklm
    --include-package=google.genai
    --include-package=faster_whisper
    --include-package=ctranslate2
    --include-package=av
    --include-package=pypresence
    --output-dir=dist
)

# ── Flags específicas por SO ───────────────────────────────────────────────
# Cada flag de ícone só entra se o asset existir (evita FATAL do Nuitka quando
# o arquivo não está presente — ex.: .icns ainda ausente no macOS).
OUT="dist/kairos"
case "$OS" in
    linux)
        NUITKA_ARGS+=(--onefile)
        ICON="kairos/images/kairos_linux_256x256.png"
        [ -f "$ICON" ] && NUITKA_ARGS+=("--linux-onefile-icon=$ICON")
        NUITKA_ARGS+=(--output-filename=kairos)
        OUT="dist/kairos"
        ;;
    windows)
        NUITKA_ARGS+=(--onefile)
        NUITKA_ARGS+=(--windows-console-mode=disable)   # GUI, sem janela de console
        ICON="kairos/images/kairos_windows.ico"
        [ -f "$ICON" ] && NUITKA_ARGS+=("--windows-icon-from-ico=$ICON")
        NUITKA_ARGS+=(--output-filename=kairos.exe)
        OUT="dist/kairos.exe"
        ;;
    macos)
        # No macOS o Nuitka NÃO suporta --onefile; o formato de distribuição é
        # o app bundle (.app).
        NUITKA_ARGS+=(--macos-create-app-bundle)
        NUITKA_ARGS+=(--macos-app-name=Kairos)
        ICON="kairos/images/kairos_macos.icns"
        [ -f "$ICON" ] && NUITKA_ARGS+=("--macos-app-icon=$ICON")
        OUT="dist/Kairos.app"
        ;;
esac

echo ""
echo "Iniciando build ($OS)..."

# NOTA: yt-dlp NÃO é empacotado — é chamado como CLI (subprocess), não importado.
# O binário distribuído exige yt-dlp no PATH em runtime para baixar áudio do
# YouTube; sem ele, só funcionam legendas prontas e PDF/áudio local.
python -m nuitka "${NUITKA_ARGS[@]}" kairos/main.py

echo ""
echo "Build concluído! Saída em: $OUT"

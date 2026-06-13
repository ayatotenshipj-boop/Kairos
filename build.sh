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
    # Cap de paralelismo no backend C. pymupdf.mupdf é um wrapper SWIG gigante
    # (~66k linhas) cujo .c consome muita RAM no gcc; com jobs = nº de núcleos,
    # vários cc1 pesados simultâneos estouram a RAM (cc1 OOM-killed). jobs=2
    # mantém o pico baixo e ainda paraleliza. Em build com pouca RAM (ex. 8GB),
    # considere --low-memory adicional. CI sobrescreve via NUITKA_JOBS (ex. 1).
    --jobs=${NUITKA_JOBS:-2}
    --enable-plugin=pyside6
    # Families confirmadas no PySide6 (pip do CI tem layout diferente do Qt do
    # pacman): 'styles' e 'qml' NÃO existem como plugin families no pip e fazem
    # o Nuitka abortar ('no such plugin family'). 'sensible' é meta-family que
    # adapta por SO e nunca erra em family ausente; platforms/platformthemes/
    # iconengines/imageformats são explícitas e confirmadas. QML/QtQuick não é
    # plugin family: o plugin pyside6 auto-detecta via QQmlApplicationEngine e os
    # .qml do app já entram por --include-data-dir abaixo.
    --include-qt-plugins=sensible,platforms,platformthemes,iconengines,imageformats
    --include-data-dir=kairos/ui/qml=kairos/ui/qml
    --include-data-dir=kairos/images=kairos/images
    --include-data-files=kairos/config/prompts.json=kairos/config/prompts.json
    # O qml/plugins do Qt6 (pacman) trazem arquivos que NÃO são shared libs:
    # objetos .o (ex. Qt/test/controls/.../qrc_*.cpp.o) e marcadores .version
    # (módulos org/kde). O plugin pyside6 do Nuitka só ignora .a/.la/.prl e trata
    # todo o resto como DLL; copyDllFile roda patchelf --set-rpath neles sem
    # checar se são ELF, abortando ('wrong ELF type' / 'missing ELF header').
    # Excluídos como DLL — .o e .version nunca são shared libs reais.
    # fnmatch do Nuitka casa '*' através de '/'.
    --noinclude-dlls=*.o
    --noinclude-dlls=*.version
    --follow-imports
    --include-package=kairos.platform
    --include-package=pymupdf
    --include-package=pymupdf4llm
    --include-package=notebooklm
    # Árvore google.* NÃO é compilada em C: demovida a bytecode (Python puro) no
    # standalone, mas ainda incluída e importável em runtime. Motivos: os tipos
    # autogerados de google.protobuf estouram o gcc/RAM (OOM em máquinas de build
    # com pouca RAM, ex. Windows 8GB); google.* é I/O / serialização de rede e
    # não ganha desempenho real com compilação C. Também acelera o build.
    --nofollow-import-to=google
    --include-package=faster_whisper
    --include-package=ctranslate2
    --include-package=av
    # onnxruntime (VAD) e tokenizers são importados pelo faster_whisper de forma
    # lazy; --follow-imports não captura suas C-ext/.so → --include-package
    # garante que os nativos (.so/.dll/data) sejam empacotados (sem isto a
    # transcrição Whisper falha com ImportError no binário).
    # PORÉM, compilá-los em C dispara um AssertionError no optimizeModules do
    # Nuitka 4.1.2 (micro_passes == 0) no Windows — classe de bug conhecida com
    # pacotes de typing/generics pesados (cf. pydantic, #2571/#2579). Solução:
    # --nofollow-import-to demove a bytecode (pula o pass que falha) enquanto o
    # --include-package acima mantém os nativos no bundle. Combinação evita o
    # crash do build SEM reintroduzir o ImportError de runtime.
    --include-package=onnxruntime
    --include-package=tokenizers
    --nofollow-import-to=onnxruntime
    --nofollow-import-to=tokenizers
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

# Em runner de CI com pouca RAM, NUITKA_LOW_MEMORY=1 reduz o pico do compile C.
if [ "${NUITKA_LOW_MEMORY:-0}" = "1" ]; then
    NUITKA_ARGS+=(--low-memory)
fi

echo ""
echo "Iniciando build ($OS)..."

# NOTA: yt-dlp NÃO é empacotado — é chamado como CLI (subprocess), não importado.
# O binário distribuído exige yt-dlp no PATH em runtime para baixar áudio do
# YouTube; sem ele, só funcionam legendas prontas e PDF/áudio local.
python -m nuitka "${NUITKA_ARGS[@]}" kairos/main.py

echo ""
echo "Build concluído! Saída em: $OUT"

# CLAUDE.md — Kairos

App de estudo local (perfil TDAH+TEA). Fluxo: PDF ou URL YouTube → NotebookLM → nota no Obsidian + log markdown.

---

## Ambiente

```text
OS:     CachyOS / Arch, Hyprland
Python: 3.14.5  (venv: .venv --system-site-packages)
Shell:  Zsh
Raiz:   ~/Documentos/Kairos
```

```bash
./run.sh      # executar
./build.sh    # build Nuitka
```

---

## Verificação (rodar antes de concluir qualquer tarefa)

> Ajustar aos comandos que realmente existem no repo. Substituir/remover os que não se aplicam.

```bash
ruff check kairos/        # lint  (se ruff estiver configurado)
python -m pytest -q       # testes (se houver suíte)
./build.sh                # build precisa sair com código 0
```

Regra: mostrar a saída do comando, não afirmar "feito". Uma tarefa não está concluída até a verificação passar.

---

## Prioridades (em ordem)

1. Não quebrar o que já funciona.
2. Não travar a UI.
3. Menor número de alterações possível.
4. Mínimo de contexto consumido.
5. Preservar a arquitetura abaixo.

---

## Regras invioláveis

**Aplicadas por hook (determinístico):**

* Nunca commitar API keys, credenciais ou arquivos pessoais.
* Nunca usar `os.path` — somente `pathlib.Path`.
* Nunca usar `setStyleSheet()` inline — estilização só em `styles.qss`.

**Aplicadas por convenção (este documento):**

* PySide6 vem do pacman (`extra/pyside6`), nunca via pip. Venv sempre `--system-site-packages`.
* Nuitka travado em 4.1.2 — não atualizar sem pedido explícito.
* Separação estrita: zero lógica de negócio em `ui/`, zero UI em `pipeline/`.
* Nunca caminhos hardcoded.
* UI nunca bloqueia: operações > 1s em `QThread`/`QRunnable`, com feedback visual e status em tempo real.
* Erros ao usuário em PT-BR, sem stacktrace cru.

---

## Code style (Python)

* Imports: stdlib → terceiros → local, ordenados.
* `pathlib.Path` para todo I/O de caminho.
* Type hints em assinaturas públicas.
* Sem código especulativo ou abstração prematura.

---

## Arquitetura

```text
kairos/
├── main.py          # bootstrap, QApplication, MainWindow
├── ui/              # interface — sem lógica de negócio
├── pipeline/        # processamento — sem UI
├── integrations/    # serviços externos
└── config/          # persistência
```

| Arquivo | Responsabilidade |
| --- | --- |
| `pipeline/ingestor.py` | Identificação e roteamento |
| `pipeline/pdf_extractor.py` | PDF → Markdown |
| `pipeline/youtube_extractor.py` | Transcrições |
| `pipeline/processor.py` | NotebookLM + fallback local |
| `pipeline/writer.py` | Escrita Obsidian |
| `pipeline/logger.py` | Study Log |
| `integrations/notebooklm_client.py` | Comunicação NotebookLM |
| `integrations/launcher.py` | Simpmusic |
| `config/config.py` | Persistência |

**Fluxo:** `PDF/URL → ingestor → extractor → processor → writer → logger`

**Onde mexer:** UI → `ui/` · NotebookLM → `integrations/notebooklm_client.py` + `pipeline/processor.py` · Obsidian → `pipeline/writer.py`

---

## Stack

| Componente | Tecnologia |
| --- | --- |
| GUI | PySide6 (pacman) |
| Build | Nuitka 4.1.2 |
| NotebookLM | notebooklm-py 0.7.0 |
| PDF | pymupdf4llm 0.0.17 |
| YouTube | youtube-transcript-api + yt-dlp |
| Config | config.json |

---

## Build (Nuitka)

`--follow-imports` não captura imports lazy/dinâmicos nem data files de C-extensions. Incluir explicitamente:

```bash
--include-package=pymupdf \
--include-package=pymupdf4llm \
--include-package=notebooklm \
--include-package=faster_whisper \
--include-package=ctranslate2 \
--include-package=av \
--include-package=onnxruntime \
--include-package=tokenizers \
```

> O pacote real do PyMuPDF é `pymupdf` (não `fitz` — `fitz` é alias legado e há um pacote PyPI homônimo sem relação). Se `.so` não for empacotado, avaliar `--include-package-data`.
>
> `faster-whisper` importa `onnxruntime` (VAD) e `tokenizers` de forma lazy — ambos C-ext com `.so`/`.dll` não capturados por `--follow-imports`; incluí-los explicitamente. `yt-dlp` é chamado como **CLI subprocess** (não importado), então **não** entra em `--include-package` — precisa estar no PATH em runtime.

---

## Economia de contexto

1. Identificar arquivos relevantes; ler só o necessário.
2. Nunca escanear o repo inteiro sem pedido explícito.
3. Parar a investigação quando houver informação suficiente.
4. Reutilizar contexto já obtido na sessão.

Prioridade: CLAUDE.md → sessão → arquivos específicos → exploração.

---

## Política de modificação

* Alterações cirúrgicas; menor número de arquivos.
* Não refatorar, mover, renomear ou reorganizar sem pedido.
* Não adicionar dependências sem aprovação.
* Não alterar APIs ou comportamento existente sem justificativa.

---

## Ambiguidade

Não assumir. Perguntar. Nunca alterar arquitetura ou remover funcionalidade sem confirmação.

---

## Riscos conhecidos

* **NotebookLM sessão:** reautenticar via terminal se cair.
* **YouTube:** fallback automático para yt-dlp.
* **Build:** confirmar Nuitka 4.1.2 e os `--include-package` acima.

---

## SimpMusic (Hyprland)

O `launcher.py` registra automaticamente as windowrules via `hyprctl` antes de
abrir o player, então em geral nada é preciso. Para fixá-las de forma estática no
`hyprland.conf`, use:

```conf
windowrulev2 = workspace special:kairos-music silent, class:^(com-maxrave-simpmusic-MainKt)$
windowrulev2 = float, class:^(com-maxrave-simpmusic-MainKt)$
```

> A classe real da janela é `com-maxrave-simpmusic-MainKt` (StartupWMClass do
> `.desktop`), **não** o `simpmusic` genérico. O workspace é o especial
> `kairos-music`, silencioso — o player nasce em segundo plano, sem foco e sem
> dividir a tela. Controle exclusivo pelo mini-player do Kairos.

---

## Definition of Done

* Verificação (lint/teste/build) passou — com saída mostrada.
* Arquitetura preservada, UI responsiva.
* Mensagens ao usuário em PT-BR.
* Nenhuma regra deste documento violada.
* Alteração atende exatamente ao solicitado, sem regressão.

---

## Multi-SO

> Kairos hoje é **Linux-first**. O objetivo de longo prazo é rodar em **Linux,
> Windows e macOS**. Esta seção fixa as regras que todo código novo deve seguir
> para não aprofundar o acoplamento ao Linux. Detalhamento técnico:
> `ARCHITECTURE.md`, `PLATFORM_MATRIX.md`, `DECISIONS.md`.

### Ambiente-alvo (ampliado)

```text
Linux:    CachyOS / Arch, Hyprland  (plataforma primária, única testada)
Windows:  10 / 11                    (alvo — indefinido/não testado)
macOS:    13+ (Ventura ou superior)  (alvo — indefinido/não testado)
```

### Regras invioláveis cross-platform

* `pathlib.Path` para todo caminho — `os.path` proibido (já é regra; reforçada
  aqui pelo motivo Multi-SO: separadores e raízes divergem entre SOs).
* Nenhum caminho hardcoded de raiz de SO (`~/.config`, `%APPDATA%`,
  `~/Library/...`). Resolver via camada de config (futuro `ConfigPathBackend`).
* **Nenhum código novo chama binário externo de desktop direto.** `notify-send`,
  `playerctl`, `pactl`, `hyprctl`, `gdbus` são Linux-only e hoje vivem em
  `integrations/`. Código novo que precise notificar/controlar mídia passa por
  uma interface de backend (ver `ARCHITECTURE.md` §10), nunca por `subprocess`
  direto no caminho de chamada.
* Todo `subprocess` que invoca um executável deve resolvê-lo via
  `shutil.which(...)` e degradar para no-op se ausente — padrão já usado em
  `notifier.py`, `music_mpris.py`, `launcher.py`. **Exceção a corrigir:**
  `pipeline/youtube_extractor.py:79` usa a string literal `'yt-dlp'` sem
  `shutil.which` → `FileNotFoundError` em SO sem yt-dlp no PATH.

### Política de abstração

* Integrações específicas de SO ficam isoladas em `integrations/`, atrás de uma
  interface comum, com seleção de implementação por plataforma
  (`sys.platform`). Linux = implementação atual; Windows/macOS = stubs no-op até
  serem portados.
* Backends de SO a introduzir (interface documentada em `ARCHITECTURE.md` §10):
  `NotificationBackend`, `MusicBackend`, `MusicLauncherBackend`,
  `ConfigPathBackend`, `BuildBackend`.

### Build por plataforma

* Linux: `build.sh` (Nuitka 4.1.2, `--onefile`, `--linux-onefile-icon`).
* Windows: futuro `build-windows.ps1` (ícone `.ico` já existe —
  `kairos/images/kairos_windows.ico`; falta `--windows-icon-from-ico`).
* macOS: futuro `build-macos.sh` (`--macos-create-app-bundle`; falta asset
  `.icns` — hoje inexistente).
* `systemd/` (keepalive NotebookLM) é Linux-only; Windows usaria Task Scheduler
  e macOS `launchd` — ainda indefinido.
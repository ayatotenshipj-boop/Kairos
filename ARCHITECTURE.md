# ARCHITECTURE.md — Kairos

> Documento de arquitetura para a portabilidade **Multi-SO** (Linux → +Windows
> +macOS). Estado atual: **Linux-first**, única plataforma testada. Toda
> afirmação carrega evidência `arquivo:linha`. Itens não verificados marcados
> como **indefinido**. Nenhum código foi alterado na produção deste documento.

Documentos relacionados: `CLAUDE.md` (§Multi-SO), `PROJECT_STATE.md`,
`PLATFORM_MATRIX.md`, `DECISIONS.md`.

---

## 1. Visão geral

Kairos é um app de estudo local (perfil TDAH+TEA). Recebe uma fonte (PDF, URL do
YouTube, áudio ou texto), extrai o conteúdo, processa com um backend de IA
(NotebookLM, Gemini ou Ollama/local) e grava uma nota estruturada no Obsidian
mais um registro no study log. UI em PySide6/QML; processamento pesado isolado
em `QThread`s e, no caso do NotebookLM, em subprocesso `spawn`.

Stack: PySide6 (via pacman, `CLAUDE.md` §Stack) · Nuitka 4.1.2 para build ·
pymupdf4llm (PDF) · faster-whisper + yt-dlp (áudio YouTube) · clients HTTP
urllib (Gemini/Ollama) · pypresence (Discord RPC).

---

## 2. Arquitetura atual

```text
┌──────────────────────────────────────────────────────────────┐
│  UI  (PySide6 + QML)                                          │
│  main.py · ui/backend.py (QObject ponte) · ui/workers.py     │
│  ui/qml/*  — sem lógica de negócio                           │
└───────────────┬──────────────────────────────────────────────┘
                │  Qt Signals / Slots  (QThread workers)
┌───────────────▼──────────────────────────────────────────────┐
│  PIPELINE  (sem UI)                                           │
│  ingestor → {pdf,youtube,audio,text}_extractor               │
│           → processor → writer → logger                      │
└───────────────┬───────────────────────┬──────────────────────┘
                │                        │
┌───────────────▼──────────┐  ┌──────────▼──────────────────────┐
│ INTEGRATIONS (externo)   │  │ CONFIG (persistência)           │
│ notebooklm_client (spawn)│  │ config.py  ~/.config/kairos     │
│ gemini_client (urllib)   │  │ defaults.py                     │
│ local_client (urllib)    │  └─────────────────────────────────┘
│ notifier   notify-send   │  ┌─────────────────────────────────┐
│ music_mpris playerctl…   │  │ SO / DESKTOP (Linux-only)       │
│ launcher   hyprctl/Popen │  │ notify-send playerctl pactl     │
│ discord_presence         │  │ gdbus hyprctl  · systemd timer  │
└──────────────────────────┘  └─────────────────────────────────┘
```

**Descrição por módulo:**

| Módulo | Papel | Acoplamento a SO |
| --- | --- | --- |
| `main.py` | Bootstrap QApplication, paleta, ícone, `multiprocessing.freeze_support()` | Ícone só `kairos_linux_*` (`main.py:91-94`) |
| `ui/backend.py` | Ponte QObject UI↔pipeline; QFileDialog; abre Obsidian | Portável (Qt) |
| `ui/workers.py` | `QThread`s: Extraction/Processor/Writer/Music/AuthCheck/UpdateCheck | Portável (Qt) |
| `pipeline/ingestor.py` | Identifica e roteia a fonte | Portável |
| `pipeline/pdf_extractor.py` | PDF → Markdown (pymupdf4llm) | Portável (lib) |
| `pipeline/youtube_extractor.py` | Legenda ou áudio→Whisper; chama `yt-dlp` | ⚠️ `yt-dlp` literal (`:79`) |
| `pipeline/audio_extractor.py` | Áudio local → Whisper | Portável (lib) |
| `pipeline/processor.py` | Seleciona backend de IA e processa | Portável |
| `pipeline/writer.py` | Escreve nota no vault Obsidian | Portável (`expanduser` `:203`) |
| `pipeline/logger.py` | Study log markdown | Portável (`expanduser` `:35`) |
| `integrations/notebooklm_client.py` | NotebookLM via subprocesso spawn | Portável (`spawn`), CLI `notebooklm` externa |
| `integrations/gemini_client.py` | Gemini HTTP (urllib) | Portável |
| `integrations/local_client.py` | Ollama HTTP (urllib) | Portável |
| `integrations/notifier.py` | Notificação desktop | **Linux** `notify-send` (`:18,:23`) |
| `integrations/music_mpris.py` | Controle/leitura SimpMusic + volume | **Linux** playerctl/gdbus/pactl |
| `integrations/launcher.py` | Lança SimpMusic; windowrules | **Linux** playerctl/hyprctl/Popen |
| `integrations/discord_presence.py` | Discord Rich Presence (pypresence) | Portável |
| `integrations/update_checker.py` | Consulta GitHub Releases (urllib); compara com `_version.__version__` | Portável (best-effort, nunca lança) |
| `config/config.py` | Persistência config/prompts | **Linux** `~/.config` (`:9-10`) |

---

## 3. Dependências Linux-specific (evidência `arquivo:linha`)

| # | Local | Binário/recurso | Comportamento | Quebra em Win/Mac |
| --- | --- | --- | --- | --- |
| 1 | `integrations/notifier.py:18` (which), `:23` (run) | `notify-send` | Notificação de desktop | No-op silencioso (already best-effort) |
| 2 | `integrations/music_mpris.py:46` (which), `:51` (run) | `playerctl` | Snapshot + play/pause/next/prev MPRIS | Sem controle de mídia (no-op) |
| 3 | `integrations/music_mpris.py:71` (which), `:75` (run) | `gdbus` | Lê CanGoNext/CanGoPrevious | Fallback `(True,True)` — degrada ok |
| 4 | `integrations/music_mpris.py:161` (which), `:166`/`:184` (run) | `pactl` | Volume do stream no PipeWire/Pulse | Sem controle de volume (no-op) |
| 5 | `integrations/launcher.py:28` (which), `:32` (run) | `playerctl -l` | Detecta SimpMusic já rodando | Sempre retorna False → pode duplicar |
| 6 | `integrations/launcher.py:47` | `HYPRLAND_INSTANCE_SIGNATURE` | Gate de Hyprland p/ windowrules | Var ausente → pula regras (ok) |
| 7 | `integrations/launcher.py:49` (which), `:60` (run) | `hyprctl windowrulev2` | Abre player em workspace silencioso | Sem windowrules (player em foreground) |
| 8 | `integrations/launcher.py:99` | `subprocess.Popen(cmd)` | Lança binário SimpMusic | Caminho/binário Linux; indefinido |
| 9 | `config/config.py:9-10` | `Path.home()/".config"/"kairos"` | Raiz de config/prompts | Funciona mas ignora `%APPDATA%`/`~/Library` |
| 10 | `config/defaults.py:26` | `"notebooklm_home": "~/.notebooklm"` | Home do NotebookLM (expandido em `notebooklm_client.py:194`) | `expanduser` resolve; convenção dotfile |
| 11 | `main.py:91-94` | `kairos_linux_{16..512}.png` | Ícone da app | Só PNG Linux; `.ico` existe mas não usado; `.icns` ausente |
| 12 | `pipeline/youtube_extractor.py:79` | `'yt-dlp'` (literal, sem `which`) | Baixa áudio do YouTube | ⚠️ `FileNotFoundError` se yt-dlp fora do PATH |
| 13 | `systemd/kairos-notebooklm.{service,timer}` | systemd user units | Keepalive `notebooklm auth refresh` | Linux-only; Win=Task Scheduler, Mac=launchd (indefinido) |
| 14 | `launcher.py:2` | `import os` (uso `os.environ.get`, `:47`) | Leitura de env var | Portável (`os.environ` ok; não é `os.path`) |

**Limpo / já portável (evidência do que funciona):**
* 100% `pathlib.Path`, zero `os.path` no código (regra de hook, `CLAUDE.md`).
* `expanduser()` em todos os caminhos de vault/home: `writer.py:203`,
  `logger.py:35`, `backend.py:495`, `notebooklm_client.py:194`.
* Qt: `QFileDialog` (`backend.py:475-481`), `QDesktopServices.openUrl` +
  `obsidian://` (`backend.py:484-504`).
* Extração por biblioteca, sem subprocess de SO: `pymupdf4llm` (PDF),
  `faster-whisper` (áudio).
* HTTP por urllib puro: `gemini_client.py`, `local_client.py`.
* NotebookLM em subprocesso `spawn` (`notebooklm_client.py:94-136`,
  `main.py:75-77`) — modelo de processo funciona em todos os SOs.

---

## 4. Arquitetura proposta Multi-SO

Introduzir uma fina camada de seleção por plataforma dentro de `integrations/`
(e em `config/` para caminhos). O pipeline e a UI **não mudam** — continuam
chamando a mesma API pública; só a implementação por trás varia conforme
`sys.platform`.

```text
            pipeline / ui  (inalterados)
                   │  mesma API pública
        ┌──────────▼───────────┐
        │  Backend selector    │  sys.platform → impl
        │  (factory por SO)    │
        └───┬──────────┬───────┘
   ┌────────▼───┐  ┌───▼─────────┐  ┌──────────────┐
   │  Linux     │  │  Windows    │  │  macOS       │
   │  (atual)   │  │  (a portar) │  │  (a portar)  │
   └────────────┘  └─────────────┘  └──────────────┘
```

Backends a introduzir (interface em §10): `NotificationBackend`,
`MusicBackend`, `MusicLauncherBackend`, `ConfigPathBackend`, `BuildBackend`.
Default em SO não suportado = **stub no-op** (preserva o contrato best-effort já
existente: nenhuma função levanta exceção).

---

## 5. Fluxo do pipeline atual

```text
fonte (PDF | URL YouTube | áudio | texto)
  → ui/backend.py loadSource/process
  → ExtractionWorker (QThread)  → ingestor.ingest()
        → roteia p/ pdf_extractor | youtube_extractor | audio_extractor | text
  → ProcessorWorker (QThread)   → processor.process()
        → _resolve_backend(name)  [processor.py:38]
        → backend ∈ ("notebooklm","gemini","ollama")  [processor.py:18]
  → WriterWorker (QThread)      → writer.write()  → nota no vault Obsidian
                                → logger.log_session()  → study-log.md
```

`youtube_extractor`: tenta legenda pronta (`youtube_transcript_api`, `:49-63`);
sem legenda, baixa áudio via `yt-dlp` (`:76-91`) e transcreve com
`faster-whisper` (`:66-73`).

---

## 6. Comunicação interna

* **UI ↔ pipeline:** Qt Signals/Slots. `ui/backend.py` é um `QObject` exposto ao
  QML; dispara workers e recebe sinais de progresso/resultado.
* **Workers:** `ui/workers.py` — `QThread`s Extraction / Processor / Writer /
  Music / AuthCheck, comunicação por `Signal`, limpeza no fechamento. Garante a
  regra "UI nunca bloqueia" (`CLAUDE.md` §Regras).
* **NotebookLM:** subprocesso isolado via `multiprocessing` `spawn`
  (`main.py:75-77`, `notebooklm_client.py:94-136`) — sandbox de falha + compat
  com binário Nuitka onefile (`freeze_support()`, `main.py:77`).
* **Integrações de SO:** chamadas `subprocess.run`/`Popen` síncronas e
  best-effort dentro de `integrations/`.

---

## 7. Persistência e configuração

| Item | Caminho atual | Evidência | Multi-SO |
| --- | --- | --- | --- |
| Config | `~/.config/kairos/config.json` | `config.py:9` | Win: `%APPDATA%`; Mac: `~/Library/Application Support` — indefinido |
| Prompts (usuário) | `~/.config/kairos/prompts.json` | `config.py:10` | idem |
| Prompts (template) | `kairos/config/prompts.json` (empacotado) | `config.py:13` | Portável |
| NotebookLM home | `~/.notebooklm` (default string) | `defaults.py:26` + `notebooklm_client.py:194` | `expanduser` resolve em todos os SOs |
| Vault Obsidian | configurável pelo usuário | `writer.py:203` | Portável (`expanduser`) |
| Study log | dentro do vault | `logger.py:35` | Portável |

Validação de tipos e migração de chaves legadas em `config.py:25-41`. Candidato
de abstração: `ConfigPathBackend` (centralizar a raiz por SO; hoje hardcoded em
`config.py:9-10`). `platformdirs` é uma opção (DEC-007) — **não adotado**, sem
dependências novas nesta fase.

---

## 8. Integrações externas

| Integração | Mecanismo | Cross-platform? | Evidência |
| --- | --- | --- | --- |
| NotebookLM | CLI `notebooklm` em subprocesso spawn | Sim (CLI precisa estar instalada) | `notebooklm_client.py:94-136` |
| Gemini | HTTP urllib | Sim | `gemini_client.py` |
| Ollama/local | HTTP urllib | Sim | `local_client.py` |
| Obsidian | `obsidian://` + `QDesktopServices.openUrl` | Sim | `backend.py:484-504` |
| Discord RPC | pypresence (IPC socket) | Sim | `discord_presence.py` |
| Notificação | `notify-send` | **Não** (Linux) | `notifier.py:18,23` |
| Mídia/SimpMusic | playerctl/gdbus/pactl/hyprctl | **Não** (Linux) | `music_mpris.py`, `launcher.py` |
| yt-dlp | CLI subprocess | Parcial (binário no PATH) | `youtube_extractor.py:79` |

> **Achado (caminho de dados do NotebookLM):** a lib `notebooklm-py` expõe o
> submódulo `notebooklm.paths` com API canônica de diretórios —
> `get_home_dir()`, `get_storage_path(profile=None)`, `get_profile_dir()`,
> `get_active_profile()`. No Linux, `get_storage_path()` retorna exatamente
> `~/.notebooklm/profiles/default/storage_state.json` — a **mesma estrutura que
> `notebooklm_client.py:198-201` re-deriva à mão**. Em outro SO, a lib pode
> resolver `get_home_dir()` por outra raiz/variável de ambiente, divergindo de
> `kairos.platform.paths.notebooklm_dir()` + a montagem manual do caminho.
> **Correção aplicada (`notebooklm_client.py:191-211`):** `_process_async`
> agora defere a `notebooklm.paths.get_storage_path()` quando `notebooklm_home`
> não é sobrescrito pelo usuário. Com override, aponta `NOTEBOOKLM_HOME` para a
> lib resolver o `storage_state.json` (mesma lógica da CLI). Elimina a
> divergência `~/.notebooklm` (lib, todos os SOs) vs `%APPDATA%` (antiga
> `platform.paths.notebooklm_dir()` no Windows). Ver DEC-014.

---

## 9. Estratégia de build por plataforma

| SO | Script | Ferramenta | Ícone | Estado |
| --- | --- | --- | --- | --- |
| Linux | `build.sh` | Nuitka 4.1.2 `--onefile` `--linux-onefile-icon` | `kairos_linux_256x256.png` (`build.sh:42`) | ✅ funciona |
| Windows | futuro `build-windows.ps1` | Nuitka `--windows-icon-from-ico` | `kairos_windows.ico` (existe, não usado) | 🔲 indefinido |
| macOS | futuro `build-macos.sh` | Nuitka `--macos-create-app-bundle` | `.icns` (ausente) | 🔲 indefinido |

`build.sh`: venv obrigatório `--system-site-packages` (PySide6 do pacman, nunca
pip — DEC-001); `--enable-plugin=pyside6`; `--include-qt-plugins=sensible,
styles,platforms,qml`; data-dirs `qml`/`images` + `prompts.json`. **yt-dlp NÃO é
empacotado** (chamado como CLI, `build.sh:31-33`) — exigido no PATH em runtime.
Candidato de abstração: `BuildBackend` (parametrizar flags de ícone/bundle por
SO).

> Nota: o `CLAUDE.md` §Build lista `--include-package=yt_dlp` e
> `--include-package=notebooklm_py`, mas o `build.sh` atual **não** os inclui
> (yt-dlp é CLI; pacote NotebookLM entra como `--include-package=notebooklm`,
> `build.sh:46`). Divergência registrada — **não corrigida** (sessão é
> doc-only).

---

## 10. Camadas de abstração recomendadas

Para cada backend: **interface esperada** (métodos públicos), **impl Linux
atual** (`arquivo:linha`), **falta p/ Windows / macOS**. Apenas a interface é
documentada — nenhum código é escrito.

### 10.1 NotificationBackend
* **Interface:** `notify(title: str, body: str = "") -> None` (best-effort, nunca
  lança).
* **Linux atual:** `notify-send` via `shutil.which`+`subprocess.run`
  (`notifier.py:16-29`).
* **Windows:** API de toast (ex.: WinRT/`win10toast` ou
  `QSystemTrayIcon.showMessage`) — indefinido.
* **macOS:** `osascript -e 'display notification'` ou Notification Center —
  indefinido.

### 10.2 MusicBackend
* **Interface:** `snapshot() -> dict` (`status,title,artist,artUrl,canNext,
  canPrev,available`); `play_pause()`; `next()`; `previous()`; `volume_step(delta:
  float)`.
* **Linux atual:** playerctl (`music_mpris.py:44-138`), gdbus capabilities
  (`:66-97`), pactl volume (`:155-189`).
* **Windows:** SMTC (`GlobalSystemMediaTransportControls`) — indefinido; volume
  via Core Audio.
* **macOS:** MediaRemote (privado) ou MPNowPlaying — indefinido; sub-superfície
  de Volume separada.

### 10.3 MusicLauncherBackend
* **Interface:** `start() -> None`; `stop() -> None`; (interno)
  `_already_running() -> bool`.
* **Linux atual:** `playerctl -l` (`launcher.py:23-40`), gate Hyprland +
  `hyprctl windowrulev2` (`:43-65`), `subprocess.Popen` (`:68-103`).
* **Windows/macOS:** lançar o player nativo; equivalente de "janela em segundo
  plano" (windowrules) é específico do WM — Hyprland-only hoje; indefinido.

### 10.4 ConfigPathBackend
* **Interface:** `config_dir() -> Path`; `config_file() -> Path`;
  `prompts_file() -> Path`.
* **Linux atual:** `Path.home()/".config"/"kairos"` (`config.py:9-10`).
* **Windows:** `%APPDATA%\\Kairos` — indefinido.
* **macOS:** `~/Library/Application Support/Kairos` — indefinido.
* **Opção:** `platformdirs` (DEC-007, não adotado).

### 10.5 BuildBackend
* **Interface (conceitual, scripts):** flags de empacotamento por SO — ícone,
  bundle, plugins Qt, data-dirs.
* **Linux atual:** `build.sh` (Nuitka `--onefile`, `--linux-onefile-icon`,
  `build.sh:34-54`).
* **Windows:** `--windows-icon-from-ico=kairos_windows.ico` — script ausente.
* **macOS:** `--macos-create-app-bundle` + `.icns` ausente — script ausente.

---

## 11. Versionamento, atualização e CI (release pipeline)

> Introduzido após o §9 (build por plataforma) para fechar o ciclo
> dev → release multi-SO. Portável — sem acoplamento a SO.

* **Fonte única de versão:** `kairos/_version.py` (`__version__ = "0.1.0"`).
  Reexportado por `kairos/__init__.py`; consumido por `ui/backend.py` (property
  `appVersion`, banner) e `integrations/update_checker.py` (comparação). Importam
  de `kairos._version` direto (evita ciclo via `__init__`).
* **Update checker** (`integrations/update_checker.py`): urllib puro, igual aos
  clients Gemini/Ollama; consulta `releases/latest` da API pública do GitHub,
  compara a tag (SemVer normalizado a 3 campos) com `__version__` e devolve um
  dict best-effort (nunca levanta). `html_url` só é aceito se `http(s)://` —
  schemes perigosos (`file:`, `smb:`) caem para a URL canônica da API.
* **Fluxo UI:** `UpdateCheckWorker` (`ui/workers.py`, `QThread`) roda a consulta
  fora do thread da GUI no startup; `backend.py` recebe o resultado, valida o
  `sender`, desconecta o sinal e expõe `updateAvailable`/`updateVersion`/
  `updateUrl`; `ui/qml/main.qml` mostra um banner com link para o release.
* **CI multi-SO** (`.github/workflows/build.yml`): matrix
  `ubuntu/windows/macos-latest`, Python 3.12 (wheels das C-ext), reaproveita o
  `build.sh` (detecta o SO) via `shell: bash`; instala PySide6/patchelf no
  runner (não há pacman); `--include-package` extra de `onnxruntime`/`tokenizers`
  no build.sh; pins de CI em `.github/constraints.txt`. Em push de tag `vX.Y.Z`,
  o job `release` (único com `contents: write`) publica os binários dos 3 SOs +
  `SHA256SUMS`. Actions fixadas por SHA. Atualiza o §9: Windows/macOS deixam de
  ser "script ausente" — são compilados pelo CI com o mesmo `build.sh`, embora
  ainda **não testados em uso real**.
* **Pendências (adiadas a pedido):** L5 — gate do release por contagem de
  artifacts (se 1 SO falha com `fail-fast:false`, o release sai incompleto);
  L6 — guard no CI garantindo tag `vX.Y.Z` == `__version__`. Ver
  `PROJECT_STATE.md`.

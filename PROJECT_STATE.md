# PROJECT_STATE.md — Kairos

> Estado do projeto na ótica da portabilidade **Multi-SO**. Linux é a única
> plataforma testada; Windows/macOS são **alvos**, não verificados (**indefinido**).
> Evidência `arquivo:linha` em toda afirmação. Doc-only — nenhum código alterado.
> Data do levantamento: 2026-06-12.

Relacionados: `ARCHITECTURE.md`, `PLATFORM_MATRIX.md`, `DECISIONS.md`,
`CLAUDE.md` (§Multi-SO).

---

## Funcionalidades implementadas

| Funcionalidade | Estado (Linux) | Evidência |
| --- | --- | --- |
| Ingestão PDF → Markdown | ✅ | `pipeline/pdf_extractor.py` (pymupdf4llm) |
| Ingestão YouTube (legenda) | ✅ | `youtube_extractor.py:49-63` |
| Ingestão YouTube (áudio→Whisper) | ✅ | `youtube_extractor.py:66-91` |
| Ingestão áudio local | ✅ | `pipeline/audio_extractor.py` (faster-whisper) |
| Processamento NotebookLM | ✅ | `notebooklm_client.py:94-136` (spawn) |
| Processamento Gemini | ✅ | `gemini_client.py` (urllib) |
| Processamento Ollama/local | ✅ | `local_client.py` (urllib) |
| Escrita Obsidian + abrir nota | ✅ | `writer.py:203`, `backend.py:484-504` |
| Study log | ✅ | `pipeline/logger.py:35` |
| UI QML + tema claro/escuro | ✅ | `main.py:19-71` (paletas), `ui/qml/` |
| Mini-player de mídia | ✅ Linux | `music_mpris.py`, `launcher.py` |
| Notificação desktop | ✅ Linux | `notifier.py:16-29` |
| Discord Rich Presence | ✅ | `discord_presence.py` (pypresence) |
| Keepalive auth NotebookLM | ✅ Linux | `systemd/kairos-notebooklm.{service,timer}` |

---

## Específico de Linux (precisa abstração)

| Item | Evidência | Impacto Multi-SO |
| --- | --- | --- |
| `notify-send` | `notifier.py:18,23` | Sem notificação em Win/Mac |
| `playerctl` (MPRIS) | `music_mpris.py:46,51`; `launcher.py:28` | Sem controle de mídia |
| `gdbus` (capabilities) | `music_mpris.py:71,75` | Degrada p/ `(True,True)` — ok |
| `pactl` (volume) | `music_mpris.py:161,166,184` | Sem controle de volume |
| `hyprctl` windowrules | `launcher.py:49,60` | Player não nasce em 2º plano |
| Gate Hyprland | `launcher.py:47` | Específico do WM |
| `Popen` SimpMusic | `launcher.py:99` | Binário/caminho Linux |
| `~/.config/kairos` | `config.py:9-10` | Ignora `%APPDATA%`/`~/Library` |
| Ícone `kairos_linux_*` | `main.py:91-94` | `.ico` não usado; `.icns` ausente |
| systemd units | `systemd/*` | Win=Task Scheduler, Mac=launchd |

---

## Cross-platform (já portável)

* `pathlib.Path` em 100% do código; zero `os.path` (regra de hook).
* `expanduser()` em vault/home: `writer.py:203`, `logger.py:35`,
  `backend.py:495`, `notebooklm_client.py:194`.
* Qt: `QFileDialog` (`backend.py:475-481`), `QDesktopServices.openUrl`
  (`backend.py:484-504`).
* Extração por lib (sem subprocess): pymupdf4llm, faster-whisper.
* Clients HTTP urllib: Gemini, Ollama.
* NotebookLM em `spawn` (`main.py:75-77`) — modelo de processo universal.
* Discord RPC pypresence — cross-platform por natureza.

---

## Pendências

* ✅ ~~`youtube_extractor.py:79` usa `'yt-dlp'` literal sem `shutil.which`~~ —
  **corrigido na Fase 1 da migração** (`youtube_extractor.py:77-82`): resolve via
  `shutil.which("yt-dlp")` e levanta `RuntimeError` PT-BR se ausente.
* Divergência `CLAUDE.md` §Build × `build.sh` quanto a `--include-package`
  (`yt_dlp`/`notebooklm_py`) — ver `ARCHITECTURE.md` §9 (nota).
* `kairos_windows.ico` existe mas não é referenciado em lugar nenhum
  (`main.py` só carrega PNG Linux).

---

## Bloqueadores Multi-SO

| Bloqueador | Severidade | Evidência |
| --- | --- | --- |
| Notificação acoplada a `notify-send` | Média (best-effort, degrada) | `notifier.py:18` |
| Mídia acoplada a playerctl/pactl/hyprctl | Alta p/ paridade de feature | `music_mpris.py`, `launcher.py` |
| Raiz de config hardcoded `~/.config` | Média | `config.py:9-10` |
| Sem build Windows/macOS | Alta | só `build.sh` |
| `.icns` ausente p/ macOS | Baixa | `kairos/images/` |
| Keepalive só systemd | Média | `systemd/` |
| `yt-dlp` literal sem `which` | Média (crash em vez de no-op) | `youtube_extractor.py:79` |

---

## Próximas etapas (priorizadas)

1. Corrigir `yt-dlp` literal → `shutil.which` + degradação (bug concreto, baixo
   custo). *Fora do escopo desta sessão doc-only.*
2. Introduzir seletor de backend por `sys.platform` em `integrations/`
   (`ARCHITECTURE.md` §10), com stubs no-op para Win/Mac.
3. `ConfigPathBackend` — centralizar raiz de config por SO (`config.py:9-10`).
4. `NotificationBackend` — Win toast / Mac osascript.
5. `MusicBackend` + `MusicLauncherBackend` — SMTC (Win) / MediaRemote (Mac);
   sem garantia de paridade (windowrules são Hyprland-only).
6. `build-windows.ps1` (ícone `.ico` já existe) e `build-macos.sh` (criar `.icns`).
7. Equivalente de keepalive: Task Scheduler (Win), launchd (Mac).

---

## Progresso da migração (estimativa por área)

> Percentual = quão pronto para Multi-SO está o item (100% = roda nos 3 SOs sem
> mudança). Estimativa qualitativa, não medida. Atualizado após **Fase 1**
> (backends de abstração — ver seção abaixo).

| Área | Progresso | Nota |
| --- | --- | --- |
| Pipeline (extração/processamento) | ~100% | `yt-dlp` literal corrigido (`shutil.which`) |
| UI (PySide6/QML) | ~95% | Ícone Win via `.ico` (existe); falta `.icns` Mac |
| Config paths | ~85% | `ConfigPathBackend` (`platform/paths.py`): %APPDATA% (Win), ~/.config (Linux/Mac). Não testado fora do Linux |
| Notificações | ~70% | `NotificationBackend` (`platform/notifications.py`): plyer/MessageBeep (Win), osascript (Mac), notify-send (Linux). Não testado fora do Linux |
| Música | ~30% | Stub `is_supported()` — UI degrada sem player fora do Linux; sem paridade SMTC/MediaRemote |
| Build | ~33% | Só Linux dos 3 alvos (sem mudança nesta fase) |
| Integrações de IA/Obsidian/Discord | ~95% | Já cross-platform |

---

## Migração Multi-SO — Fase 1 (backends de abstração)

> Pacote novo `kairos/platform/` isola decisões por SO via `sys.platform`.
> Nenhum `if/elif` de plataforma fora desse pacote (exceção: guards de no-op em
> `launcher.start()` e `music_mpris.snapshot()` que delegam ao backend).

| Backend | Arquivo | Estado | Linux | Windows | macOS |
| --- | --- | --- | --- | --- | --- |
| ConfigPathBackend | `platform/paths.py` | ✅ implementado | ~/.config, ~/.local/share, ~/.notebooklm | %APPDATA% | ~/.config (idem Linux) |
| NotificationBackend | `platform/notifications.py` | ✅ implementado | notify-send | plyer→MessageBeep | osascript |
| MusicBackend (stub) | `platform/music.py` | ✅ stub | playerctl (delega `music_mpris`) | 🔲 stub no-op | 🔲 stub no-op |
| MusicLauncher (guard) | `integrations/launcher.py:70-73` | ✅ guard SO | ativo | no-op | no-op |
| Ícone por SO | `main.py:91-100` | ✅ implementado | PNG | `.ico` | PNG (sem `.icns`) |
| yt-dlp resolução | `youtube_extractor.py:77-82` | ✅ corrigido | which | which | which |

**Consumidores atualizados:** `config/config.py` (raiz via `config_dir()`),
`config/defaults.py` (`notebooklm_home=""` → runtime), `notebooklm_client.py:191-194`
(default via `notebooklm_dir()`), `notifier.py` (re-export do backend).

**Verificado:** `ruff check kairos/` limpo; imports e `snapshot()`/`config_dir()`
exercitados no Linux. Win/macOS **não testados** (sem máquina-alvo) → 🔲.

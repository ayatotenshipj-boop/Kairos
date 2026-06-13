# PLATFORM_MATRIX.md — Kairos

> Matriz de compatibilidade por SO. Linux é a única plataforma testada;
> Windows/macOS marcados conforme análise estática do código — **não testados**.
> Onde não há base para afirmar, usa-se 🔲 / **indefinido** (regra: não assumir).
> Evidência `arquivo:linha` por linha. Doc-only — nenhum código alterado.

**Legenda:** ✅ funciona · ⚠️ parcial / degrada · ❌ não funciona · 🔲 indefinido (não testado)

| Funcionalidade | Linux | Windows | macOS | Status | Arquivo | Linha | Solução necessária |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Notificações desktop | ✅ | ❌ | ❌ | ⚠️ degrada p/ no-op | `integrations/notifier.py` | 18,23 | `NotificationBackend`: toast (Win), osascript (Mac) |
| Controle de mídia (play/pause/next/prev) | ✅ | ❌ | ❌ | Linux-only | `integrations/music_mpris.py` | 46,51,129-138 | `MusicBackend`: SMTC (Win), MediaRemote (Mac) |
| Metadados MPRIS (título/artista/capa) | ✅ | ❌ | ❌ | Linux-only | `integrations/music_mpris.py` | 100-126 | idem MusicBackend (snapshot) |
| Capabilities CanGoNext/Prev (gdbus) | ✅ | 🔲 | 🔲 | ⚠️ fallback `(True,True)` | `integrations/music_mpris.py` | 71,75 | Sub-superfície do MusicBackend |
| Volume do player (pactl) | ✅ | ❌ | ❌ | Linux-only | `integrations/music_mpris.py` | 161,166,184 | MusicBackend.volume_step: Core Audio (Win)/CoreAudio (Mac) |
| Detecção de player rodando | ✅ | ❌ | ❌ | Linux-only | `integrations/launcher.py` | 28,32 | `_already_running` por SO |
| Lançar SimpMusic | ✅ | 🔲 | 🔲 | binário/caminho Linux | `integrations/launcher.py` | 99 | `MusicLauncherBackend.start` por SO |
| Windowrules Hyprland (2º plano) | ✅ | ❌ | ❌ | Hyprland-only | `integrations/launcher.py` | 47,49,60 | Específico do WM; sem equivalente direto |
| Ícone da aplicação | ✅ | 🔲 | ❌ | só PNG Linux | `main.py` | 91-94 | Usar `.ico` (existe); criar `.icns` |
| Raiz de config (~/.config/kairos) | ✅ | ⚠️ | ⚠️ | funciona, não idiomático | `config/config.py` | 9-10 | `ConfigPathBackend`: %APPDATA% / ~/Library |
| NotebookLM home (~/.notebooklm) | ✅ | ✅ | ✅ | `expanduser` resolve | `config/defaults.py` + `notebooklm_client.py` | 26 / 194 | Nenhuma (portável) |
| Keepalive auth NotebookLM | ✅ | ❌ | ❌ | systemd-only | `systemd/kairos-notebooklm.timer` | — | Task Scheduler (Win) / launchd (Mac) |
| Script de execução (run) | ✅ | ❌ | ⚠️ | bash/nohup/sha256sum | `run.sh` | 1-32 | `run.ps1` (Win); bash ok no Mac mas `sha256sum`→`shasum` |
| Script de build | ✅ | 🔲 | 🔲 | `build.sh` multi-SO (detecta `uname`); CI compila os 3 via `shell:bash` — Win/macOS não testados | `build.sh` + `.github/workflows/build.yml` | — | Testar binários Win/macOS em uso real |
| Verificação de atualização (GitHub Releases) | ✅ | ✅ | ✅ | urllib best-effort; banner na UI | `integrations/update_checker.py` | — | Nenhuma (portável) |
| Download YouTube (yt-dlp CLI) | ⚠️ | ⚠️ | ⚠️ | literal sem `which` | `pipeline/youtube_extractor.py` | 79 | `shutil.which('yt-dlp')` + degradação |
| Extração PDF | ✅ | ✅ | ✅ | lib pymupdf4llm | `pipeline/pdf_extractor.py` | — | Nenhuma (portável) |
| Transcrição Whisper | ✅ | ✅ | ✅ | lib faster-whisper | `pipeline/audio_extractor.py` / `youtube_extractor.py` | 66-73 | Nenhuma (portável) |
| Backend NotebookLM (spawn) | ✅ | 🔲 | 🔲 | spawn ok; CLI externa | `integrations/notebooklm_client.py` | 94-136 | CLI `notebooklm` instalada no SO |
| Backend Gemini | ✅ | ✅ | ✅ | HTTP urllib | `integrations/gemini_client.py` | — | Nenhuma (portável) |
| Backend Ollama/local | ✅ | ✅ | ✅ | HTTP urllib | `integrations/local_client.py` | — | Nenhuma (portável) |
| Escrita no vault Obsidian | ✅ | ✅ | ✅ | `expanduser` + pathlib | `pipeline/writer.py` | 203 | Nenhuma (portável) |
| Discord Rich Presence | ✅ | ✅ | ✅ | pypresence (IPC) | `integrations/discord_presence.py` | — | Nenhuma (portável) |
| Tema claro/escuro (paleta Qt) | ✅ | ✅ | ✅ | QPalette Fusion | `main.py` | 47-71 | Nenhuma (portável) |
| Seletor de arquivo (QFileDialog) | ✅ | ✅ | ✅ | Qt nativo | `ui/backend.py` | 475-481 | Nenhuma (portável) |
| Abrir nota (obsidian:// URL) | ✅ | ✅ | ✅ | QDesktopServices | `ui/backend.py` | 484-504 | Nenhuma (portável) |

> 26 funcionalidades cobertas (≥ 23 exigidas). 🔲 = não há evidência para
> afirmar comportamento em Win/Mac sem teste real.

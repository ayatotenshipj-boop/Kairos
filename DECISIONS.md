# DECISIONS.md — Kairos

> Registro de decisões arquiteturais (ADR enxuto), com foco no impacto
> **Multi-SO**. Datas inferidas do histórico git (2026-06-05 setup inicial;
> 2026-06-09 backends plugáveis + reliability NotebookLM; 2026-06-11 migração
> QML). Evidência `arquivo:linha`. Doc-only — nenhum código alterado.

Relacionados: `ARCHITECTURE.md`, `PLATFORM_MATRIX.md`, `PROJECT_STATE.md`,
`CLAUDE.md`.

---

## DEC-001 — PySide6 via pacman, nunca pip

* **Data:** 2026-06-05 · **Status:** Aceito
* **Contexto:** PySide6 + Shiboken têm bindings nativos; o pacote do pacman
  (`extra/pyside6`) casa com o Qt do sistema.
* **Decisão:** Instalar PySide6 pelo pacman; venv sempre
  `--system-site-packages` (`run.sh:10`, `build.sh:10-17`, `CLAUDE.md` §Regras).
* **Motivação:** Evita conflito ABI entre Qt do pip e Qt do sistema; build
  Nuitka estável.
* **Trade-offs:** Amarra o dev ao gerenciador de pacotes do SO.
* **Impacto Multi-SO:** Windows/macOS não têm pacman → instalarão PySide6 por
  pip nesses SOs. Decisão é **Linux-específica**; reavaliar por plataforma.

## DEC-002 — Build standalone via Nuitka 4.1.2

* **Data:** 2026-06-05 · **Status:** Aceito (versão travada)
* **Contexto:** Distribuir binário único sem exigir Python no usuário final.
* **Decisão:** Nuitka 4.1.2 `--standalone --onefile`, versão fixa
  (`build.sh:2,34`, `CLAUDE.md` §Regras).
* **Motivação:** Compilação real (vs. bundlers), menor superfície de runtime.
* **Trade-offs:** Imports lazy/data de C-extensions exigem `--include-package`
  explícito; builds longos.
* **Impacto Multi-SO:** Nuitka suporta os 3 SOs, mas flags divergem
  (`--linux-onefile-icon` vs `--windows-icon-from-ico` vs
  `--macos-create-app-bundle`). Precisa `BuildBackend`/scripts por SO
  (`ARCHITECTURE.md` §9).

## DEC-003 — NotebookLM em subprocesso spawn isolado

* **Data:** 2026-06-09 · **Status:** Aceito
* **Contexto:** A automação NotebookLM é instável e pode travar/derrubar o
  processo.
* **Decisão:** Rodar o NotebookLM em `multiprocessing` `spawn`
  (`notebooklm_client.py:94-136`, `main.py:75-77`, `freeze_support()`).
* **Motivação:** Sandbox de falha; não trava a UI; compat com Nuitka onefile.
* **Trade-offs:** Overhead de spawn; serialização de dados entre processos.
* **Impacto Multi-SO:** `spawn` é o default em Windows e macOS — **favorável**;
  modelo funciona nos 3 SOs. Requer a CLI `notebooklm` instalada.

## DEC-004 — Controle de mídia via MPRIS/playerctl

* **Data:** 2026-06-11 · **Status:** Aceito (Linux)
* **Contexto:** Mini-player precisa ler/controlar o SimpMusic.
* **Decisão:** Usar `playerctl` (MPRIS) para snapshot e transporte
  (`music_mpris.py:44-138`); `gdbus` para capabilities (`:66-97`).
* **Motivação:** MPRIS é o padrão de fato no desktop Linux; sem dep extra.
* **Trade-offs:** Acoplamento a D-Bus/MPRIS; `playerctl -p` case-sensitive.
* **Impacto Multi-SO:** MPRIS não existe em Win/Mac. Precisa `MusicBackend`
  (SMTC no Windows, MediaRemote no macOS) — **indefinido**.

## DEC-005 — Notificação via notify-send (subprocess)

* **Data:** 2026-06-11 · **Status:** Aceito (Linux)
* **Contexto:** Avisar o usuário ao fim do processamento.
* **Decisão:** `notify-send` via `shutil.which`+`subprocess.run`, best-effort
  (`notifier.py:16-29`).
* **Motivação:** Simples, sem dependência; degrada para no-op se ausente.
* **Trade-offs:** Sem notificação fora do Linux.
* **Impacto Multi-SO:** Não funciona em Win/Mac (no-op silencioso). Precisa
  `NotificationBackend` (toast Win / osascript Mac).

## DEC-006 — Volume via pactl (PipeWire/Pulse)

* **Data:** 2026-06-11 · **Status:** Aceito (Linux)
* **Contexto:** O SimpMusic **ignora** escrita da propriedade Volume do MPRIS.
* **Decisão:** Ajustar volume no stream do app via `pactl set-sink-input-volume`
  (`music_mpris.py:155-189`).
* **Motivação:** Único caminho confiável de volume para esse player.
* **Trade-offs:** Acoplamento a PipeWire/Pulse; índices de sink voláteis
  (relidos a cada chamada, `:141-152`).
* **Impacto Multi-SO:** Sem `pactl` em Win/Mac. Controle de volume vira
  sub-superfície separada do `MusicBackend` — **indefinido**.

## DEC-007 — Config em ~/.config/kairos (XDG)

* **Data:** 2026-06-05 · **Status:** Aceito (revisar p/ Multi-SO)
* **Contexto:** Persistir config.json e prompts.json do usuário.
* **Decisão:** `Path.home()/".config"/"kairos"` hardcoded (`config.py:9-10`).
* **Motivação:** Convenção XDG do Linux; simples, sem dep.
* **Trade-offs:** Ignora `%APPDATA%` (Win) e `~/Library/Application Support`
  (Mac); não idiomático fora do Linux.
* **Impacto Multi-SO:** Precisa `ConfigPathBackend`. Opção `platformdirs`
  avaliada e **não adotada** (regra: sem dependências novas nesta fase);
  decisão de adotar fica pendente.

## DEC-008 — UI migrada para Qt Quick (QML)

* **Data:** 2026-06-11 · **Status:** Aceito
* **Contexto:** Substituir UI Widgets por QML para visual moderno e fluido.
* **Decisão:** `QQmlApplicationEngine` + `ui/qml/`; `ui/backend.py` (QObject)
  como ponte; QApplication mantida só para `QFileDialog` (`main.py:84-85,100`).
* **Motivação:** Animações, tema declarativo, separação UI/lógica.
* **Trade-offs:** Build precisa `--include-qt-plugins=...,qml` e data-dir de QML
  (`build.sh:38-39`).
* **Impacto Multi-SO:** QML é cross-platform — **favorável**. Pendência: paleta
  de diálogos nativos e ícone por SO.

## DEC-009 — Backends de IA plugáveis

* **Data:** 2026-06-09 · **Status:** Aceito
* **Contexto:** Não depender de um único provedor de IA.
* **Decisão:** Seleção em `processor.py` — `_VALID_BACKENDS =
  ("notebooklm","gemini","ollama")` (`:18`), `_resolve_backend()` (`:38`);
  default `processor_backend` (`defaults.py:30`).
* **Motivação:** Flexibilidade; fallback local (Ollama) sem rede externa.
* **Trade-offs:** Mais superfícies de manutenção/config.
* **Impacto Multi-SO:** Gemini e Ollama são HTTP urllib (portáveis); só o
  NotebookLM tem dependência de CLI externa. **Favorável** ao Multi-SO.

## DEC-010 — yt-dlp como CLI subprocess (não empacotado)

* **Data:** 2026-06-05 · **Status:** Aceito (com ressalva)
* **Contexto:** Baixar áudio do YouTube quando não há legenda pronta.
* **Decisão:** Chamar `yt-dlp` como CLI em subprocess; **não** empacotar no
  binário (`build.sh:31-33`, `youtube_extractor.py:76-91`).
* **Motivação:** yt-dlp muda rápido; CLI externa atualiza sem rebuild.
* **Trade-offs / ressalva:** Exige yt-dlp no PATH em runtime; e o invoca por
  **string literal** `'yt-dlp'` sem `shutil.which` (`:79`), divergindo do padrão
  best-effort das outras integrações.
* **Impacto Multi-SO:** Sem yt-dlp no PATH → `FileNotFoundError` (crash, não
  no-op) em qualquer SO, com risco maior em Windows. **Corrigido** na Fase 1 da
  migração (`youtube_extractor.py:79-83`): `shutil.which("yt-dlp")` + `RuntimeError`
  PT-BR. Coberto por `tests/test_platform.py::TestYtDlpFix`.

## DEC-011 — Estratégia de mock de plataforma nos testes

* **Data:** 2026-06-12 · **Status:** Ativa
* **Contexto:** `sys.platform` é constante em runtime mas precisa ser simulado
  para testar os 3 SOs numa só máquina (`tests/test_platform.py`).
* **Decisão:** `unittest.mock.patch.object(sys, "platform", ...)` +
  `importlib.reload(modulo)` por módulo, pois `paths.py`/`music.py` resolvem o SO
  no nível de função/módulo no import.
* **Trade-offs:** `reload` de módulo não é 100% equivalente a um boot real em
  outro SO (estado de import já materializado; `shutil.which` ainda usa o
  `_winapi` real do host — ver caveat de `_setup_background_rules`).
* **Impacto Multi-SO:** Testes locais validam a **lógica** de ramificação; o
  **comportamento real** por SO exige CI com matriz (Linux/Windows/macOS) como
  complemento. Sem isso, Win/macOS seguem 🔲 (não testados em runtime real).

## DEC-012 — plyer como dependência opcional (Windows)

* **Data:** 2026-06-12 · **Status:** Ativa
* **Contexto:** `NotificationBackend` usa `plyer` para toast no Windows
  (`platform/notifications.py:_notify_windows`). `plyer` não está no projeto.
* **Decisão:** `plyer` **NÃO** entra em `requirements.txt`. Import condicional em
  `try/except` com fallback silencioso (`MessageBeep`) se ausente.
* **Motivação:** Regra do `CLAUDE.md` — zero dependências novas sem aprovação
  explícita.
* **Trade-offs:** Notificação visual no Windows depende de o usuário instalar
  `plyer` manualmente; sem ele, degrada para beep não intrusivo.
* **Impacto Multi-SO:** Solução futura — `requirements-windows.txt` separado,
  fora do fluxo de deps do Linux (pacman). Mantém Linux intocado.

## DEC-013 — Diretório de config no macOS

* **Data:** 2026-06-12 · **Status:** Ativa
* **Contexto:** Convenção nativa do macOS é `~/Library/Application Support/kairos`;
  `config_dir()` (`platform/paths.py:16-22`) usa `~/.config/kairos` no ramo não-Win.
* **Decisão:** macOS usa `~/.config/kairos` (mesma lógica do Linux).
* **Motivação:** Consistência com o comportamento atual; usuários macOS do Kairos
  são devs familiarizados com XDG.
* **Trade-offs:** Não segue `~/Library/Application Support` (convenção nativa Mac).
* **Impacto Multi-SO:** Aceitável p/ MVP; revisitar se houver reclamação de
  usuário macOS. Trocar exigiria só um ramo `darwin` em `config_dir()`/`data_dir()`.

## DEC-014 — Caminho do storage NotebookLM deferido à lib

* **Data:** 2026-06-12 · **Status:** Aceito
* **Contexto:** `notebooklm_client.py` remontava à mão
  `~/.notebooklm/profiles/default/storage_state.json` a partir de
  `platform.paths.notebooklm_dir()`. A lib `notebooklm-py` usa `~/.notebooklm`
  em **todos** os SOs (sem ramo `%APPDATA%`); `notebooklm_dir()` retornava
  `AppData/Roaming/notebooklm` no Windows → o app procuraria a sessão onde a CLI
  `notebooklm login` nunca grava.
* **Decisão:** `_process_async` (`notebooklm_client.py:191-211`) defere a
  `notebooklm.paths.get_storage_path()`. Override do usuário (`notebooklm_home`):
  arquivo → usa direto; diretório → exporta `NOTEBOOKLM_HOME` e deixa a lib
  resolver.
* **Motivação:** Fonte única de verdade do caminho = a própria lib. Sem
  divergência app↔lib em nenhum SO.
* **Trade-offs:** Acopla o app à API `notebooklm.paths` (presente na 0.7.x).
  `platform.paths.notebooklm_dir()` deixa de ser usado pelo client (mantido como
  helper de SO + cobertura de teste).
* **Impacto Multi-SO:** Resolve a divergência crítica no Windows. Linux
  inalterado (`get_storage_path()` → mesmo caminho de antes, verificado).

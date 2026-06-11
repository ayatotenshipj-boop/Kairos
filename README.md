# Kairos

> *Do grego: o momento certo para agir.*

Kairos é um ambiente de estudo local e pessoal, construído para um perfil cognitivo específico — TDAH e TEA — onde teoria sem prática não fixa, informação demais de uma vez trava, e o cérebro precisa de estrutura externa para funcionar bem.

Conceitualmente, o Kairos é um **client intermediário** entre um backend de IA (o pesquisador) e o Obsidian (a memória):

```
Material (PDF / YouTube / Áudio)
   → Kairos extrai o conteúdo
   → injeta a instrução de estrutura no prompt escolhido
   → backend de IA (NotebookLM, Gemini ou Ollama) gera tema + sub-temas
   → Obsidian armazena como pasta + notas linkadas
   → Kairos projeta o mapa de conhecimento
```

Cada ferramenta no seu papel: **a IA estrutura, o Obsidian guarda, o Kairos sintetiza e visualiza.**

---

## Por que isso existe

O projeto nasceu de uma análise honesta de como o aprendizado funciona (ou não) para perfis neurodivergentes:

- **Teoria sem âncora não fixa** — conceitos abstratos sem contexto escapam antes da memória de longo prazo
- **Sobrecarga cognitiva** — muita informação de uma vez trava o entendimento
- **Dificuldade de iniciar** — a motivação não aparece sozinha antes da tarefa começar
- **Dependência de estado interno** — sem estrutura externa, estudar depende de "estar com vontade"

O Kairos ataca isso com scaffolding externo: você solta um material, escolhe *como* quer aprender, e o sistema cuida do resto — extração, síntese estruturada, arquivamento conectado e registro da sessão. Uma sessão sempre termina com saída visível: notas no vault e uma linha no study log.

---

## O que o Kairos faz

1. **Aceita três tipos de entrada**: arquivo **PDF**, **URL do YouTube** ou **arquivo de áudio** (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.opus`, `.flac`) — por drag-and-drop, seletor de arquivo ou campo de URL.
2. **Extrai o conteúdo localmente**:
   - PDF → Markdown via `pymupdf4llm`
   - YouTube → legenda pronta via `youtube-transcript-api`; sem legenda, baixa o áudio com `yt-dlp` e transcreve com `faster-whisper` (funciona em qualquer vídeo)
   - Áudio local → transcrição direta com `faster-whisper`
3. **Processa com o backend escolhido** (ver abaixo), aplicando o prompt selecionado + a instrução fixa de estrutura.
4. **Salva no Obsidian** como pasta de tema com notas linkadas (ou nota única, no fallback).
5. **Projeta o mapa de conhecimento** — grafo radial do tema recém-criado, lido do próprio vault; clicar num nó abre a nota no Obsidian.
6. **Registra a sessão** no `study-log.md` (data, fonte, prompt, status, duração, modo).
7. **Toca música em segundo plano** — lança o SimpMusic sem dividir a tela e o controla pelo mini-player embutido (MPRIS).

Se o backend de IA falhar, o sistema **não trava nem perde dados**: salva o texto bruto com a tag `#pendente-notebooklm` para reprocessar depois.

---

## Os três backends de processamento

O processamento é plugável — você escolhe nas Configurações. Todos respeitam o mesmo contrato (`process(text, prompt) -> (markdown, modo)`), e qualquer falha cai automaticamente no fallback local que preserva o texto bruto.

| Backend | Como funciona | Trade-off |
|---|---|---|
| **NotebookLM** (padrão) | `notebooklm-py` automatiza o NotebookLM do Google num subprocesso isolado | Gratuito e poderoso, mas usa APIs internas não documentadas — a sessão expira e a lib pode quebrar quando o Google mudar algo |
| **Gemini** | API oficial via `google-genai`; chave nas Configurações ou na variável `GEMINI_API_KEY` | Estável; **no free tier o Google pode usar os inputs para treinar modelos** (aviso exibido no app) |
| **Local (Ollama)** | HTTP para `http://localhost:11434`, modelo configurável (default `llama3.1:8b`) | 100% offline e privado; qualidade e velocidade dependem do hardware |

### Reliability do NotebookLM

- **Auth check no startup**: se a sessão caiu, o app avisa em PT-BR ("Sessão do NotebookLM expirada — renove os cookies no terminal: `notebooklm auth refresh --browser-cookies chrome`") e segue funcionando via fallback.
- **Keepalive opcional via systemd** (renova os cookies periodicamente):

```ini
# ~/.config/systemd/user/kairos-notebooklm.service
[Service]
Type=oneshot
ExecStart=%h/Documentos/Kairos/.venv/bin/notebooklm auth refresh

# ~/.config/systemd/user/kairos-notebooklm.timer
[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now kairos-notebooklm.timer
```

---

## Sistema de prompts com injeção de estrutura

Os prompts ("Como aprender") são editáveis: a sidebar lista os defaults (Explique como iniciante, Conceitos-chave, Perguntas de revisão, Só o prático, Entenda profundamente, Aprenda na prática, Conecte conceitos, Resumo para revisão, Aplicação em cibersegurança) e as Configurações permitem criar, editar e remover.

A todo prompt, o processor concatena **a instrução fixa de estrutura** — não editável, parte da arquitetura:

> "Estruture o conteúdo como um tema principal com sub-temas conectados. No Obsidian: o tema vira uma pasta, cada sub-tema uma nota linkada de volta ao tema central."

É essa instrução que faz qualquer backend devolver `# Tema` + `## Sub-temas`, que o writer converte em estrutura navegável e o mapa consegue projetar. O editor de prompt exibe o bloco em destaque (read-only) para deixar o contrato visível.

### Estrutura gerada no vault

```
<Vault>/kairos/<Tema>/
   ├── <Tema>.md          ← nota central, com links [[Sub-tema]]
   ├── <Sub-tema 1>.md    ← cada sub-nota linka [[<Tema>]] de volta
   ├── <Sub-tema 2>.md
   └── ...
```

No fallback (texto bruto, sem `##`), salva nota única `AAAA-MM-DD-<fonte>.md` — o comportamento original.

---

## Mapa de conhecimento

Após um processamento bem-sucedido, o Kairos lê a pasta do tema recém-criado (somente ela — nunca escaneia o vault inteiro), extrai os `[[wikilinks]]` da nota central e projeta um **grafo radial**: tema no centro, sub-temas em círculo. Clicar em qualquer nó abre a nota no Obsidian via `obsidian://open`. Read-only por princípio: o Kairos desenha o que está no vault, não inventa.

---

## Mini-player (SimpMusic via MPRIS)

- No startup, o Kairos lança o SimpMusic **em segundo plano** (no Hyprland, registra windowrules via `hyprctl` para a janela nascer num workspace especial silencioso — sem dividir a tela).
- O mini-player no rodapé da sidebar lê título/artista/status via `playerctl` (polling leve em thread) e controla play/pause/next/previous.
- Volume é ajustado por stream no PipeWire/Pulse (`pactl`), porque o SimpMusic não implementa a propriedade Volume do MPRIS.
- Ao fechar o Kairos, o SimpMusic é encerrado com graceful shutdown.

Requisitos: `playerctl` (controle/metadados) e `pactl` (volume) instalados.

---

## Interface

Qt Quick (QML) com PySide6. Design tokens centralizados em `Theme.qml` (dois temas, claro/escuro, com toggle persistido), tipografia JetBrains Mono, acento âmbar. A UI nunca bloqueia: extração, processamento e escrita rodam em `QThread`, com pipeline tracker (Extração → NotebookLM → Síntese → Obsidian), tempo decorrido e status em tempo real. Suporte a movimento reduzido (desativa pulsos e animações) nas Configurações.

---

## Arquitetura interna

```
kairos/
├── main.py                      ← bootstrap: QApplication + QQmlApplicationEngine
├── ui/                          ← interface — sem lógica de negócio
│   ├── backend.py               ← Backend(QObject): a única ponte QML↔Python
│   ├── workers.py               ← QThread workers (extração/processamento/escrita/música)
│   └── qml/
│       ├── main.qml             ← janela, sidebar, painel principal
│       ├── Theme.qml            ← design tokens (única fonte de cores/tamanhos)
│       ├── DropZone.qml         ← drag-and-drop com estados idle/dragover/accepted/invalid
│       ├── PipelineTracker.qml  ← 4 nós com estados e animações
│       ├── KnowledgeMap.qml     ← grafo radial do tema
│       ├── SettingsDialog.qml   ← caminhos, backend, prompts, interface
│       ├── PromptEditDialog.qml ← editor com bloco da instrução de estrutura
│       └── IconSvg.qml          ← ícones line-art por path SVG
├── pipeline/                    ← processamento — sem UI
│   ├── ingestor.py              ← identifica o tipo de fonte e roteia
│   ├── pdf_extractor.py         ← PDF → Markdown (pymupdf4llm)
│   ├── youtube_extractor.py     ← legenda pronta → fallback yt-dlp + faster-whisper
│   ├── audio_extractor.py       ← arquivo de áudio → faster-whisper
│   ├── processor.py             ← roteador de backends + injeção de estrutura + fallback
│   ├── writer.py                ← pasta de tema + notas linkadas no vault
│   └── logger.py                ← study-log.md (append-only)
├── integrations/                ← serviços externos
│   ├── notebooklm_client.py     ← NotebookLM em subprocesso isolado + auth check
│   ├── gemini_client.py         ← API Gemini (google-genai)
│   ├── local_client.py          ← Ollama via HTTP
│   ├── obsidian_graph.py        ← leitor read-only da pasta do tema
│   ├── music_mpris.py           ← playerctl/pactl (metadados, controles, volume)
│   └── launcher.py              ← lança/encerra o SimpMusic em segundo plano
└── config/
    ├── config.py                ← lê/escreve ~/.config/kairos/config.json
    └── defaults.py              ← DEFAULT_CONFIG + prompts + instrução de estrutura
```

**Fluxo:** `fonte → ingestor → extractor → processor → writer → logger → mapa`

---

## Stack

| Componente | Tecnologia |
|---|---|
| GUI | PySide6 / Qt Quick (pacman `extra/pyside6`, nunca pip) |
| Build | Nuitka **4.1.2** (travado) |
| NotebookLM | `notebooklm-py 0.7.0` |
| Gemini | `google-genai 2.7.0` |
| Ollama | HTTP local, sem SDK |
| PDF | `pymupdf4llm 0.0.17` |
| YouTube | `youtube-transcript-api 1.2.4` + `yt-dlp` |
| Transcrição | `faster-whisper` (CPU/int8, modelo configurável) |
| Música | SimpMusic + `playerctl` (MPRIS) + `pactl` |
| Config | `~/.config/kairos/config.json` |

---

## Configuração

`~/.config/kairos/config.json` (criado com defaults no primeiro uso):

```json
{
  "obsidian_vault_path": "/home/voce/Documentos/Obsidian Vault",
  "kairos_folder": "kairos",
  "log_filename": "study-log.md",
  "simpmusic_path": "/caminho/para/SimpMusic.AppImage",
  "simpmusic_autostart": true,
  "reduce_motion": false,
  "dark_mode": true,
  "notebooklm_home": "~/.notebooklm",
  "whisper_model": "small",
  "processor_backend": "notebooklm",
  "gemini_api_key": "",
  "gemini_model": "gemini-flash-latest",
  "ollama_host": "http://localhost:11434",
  "ollama_model": "llama3.1:8b",
  "prompts": [ { "id": "...", "label": "...", "text": "..." } ]
}
```

O essencial (vault, SimpMusic, backend, chave do Gemini, modelo do Ollama, prompts) é editável pela própria UI.

---

## Setup e execução

### Pré-requisitos (Arch / CachyOS)

```bash
sudo pacman -S python pyside6 yt-dlp playerctl
# Ollama opcional (backend local):
# sudo pacman -S ollama && ollama pull llama3.1:8b
```

### Rodar em desenvolvimento

```bash
git clone <repo> && cd Kairos
./run.sh        # cria .venv --system-site-packages, instala deps e abre o app
```

### Autenticar no NotebookLM (se for usar esse backend)

```bash
source .venv/bin/activate
notebooklm login
```

### Build standalone (Nuitka)

```bash
./build.sh      # gera dist/kairos (onefile)
```

Flags relevantes do build — imports lazy e data files que o `--follow-imports` não captura:

```
--enable-plugin=pyside6
--include-qt-plugins=sensible,styles,platforms,qml
--include-data-dir=kairos/ui/qml=kairos/ui/qml
--include-package=pymupdf --include-package=pymupdf4llm
--include-package=notebooklm
--include-package=faster_whisper --include-package=ctranslate2 --include-package=av
```

> O PyMuPDF importa como `pymupdf` (não `fitz`). O `yt-dlp` é chamado como CLI (subprocess), então **não** entra em `--include-package` — precisa estar no PATH do sistema. Nuitka fica travado em 4.1.2 (`requirements-dev.txt`).

---

## Riscos conhecidos e mitigações

| Risco | Mitigação |
|---|---|
| `notebooklm-py` quebra quando o Google muda APIs internas | Fallback local automático preserva o texto (`#pendente-notebooklm`); backends Gemini/Ollama como alternativa estrutural |
| Sessão do NotebookLM expira | Auth check no startup + aviso PT-BR + timer systemd opcional de keepalive |
| Vídeo sem legenda | Caminho principal já é áudio + Whisper — legenda pronta é só o atalho rápido |
| Nuitka regride com PySide6 | Versão travada em 4.1.2; só atualizar testando |
| SimpMusic sem MPRIS/instância duplicada | Detecção via bus antes de lançar; controles viram no-op sem `playerctl` |

---

## Licença

MIT — use, modifique, distribua.
O `pymupdf4llm` é AGPL: sem restrição para uso pessoal/open source; distribuição comercial fica sujeita à AGPL.

---

*Kairos — construído para um cérebro específico, mas com princípios que funcionam para qualquer um que aprende melhor fazendo do que lendo.*

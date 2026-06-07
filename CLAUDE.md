# CLAUDE.md — Kairos

Este arquivo é o contexto primário para o Claude Code operar neste repositório.
Leia inteiro antes de qualquer ação. Não pule seções.

---

## O que é este projeto

**Kairos** é um ambiente de estudo local, pessoal, construído para um perfil cognitivo específico (TDAH + TEA). Não é um app genérico de produtividade. Cada decisão de arquitetura tem uma razão direta ligada ao perfil do usuário.

O app é aberto quando o usuário vai estudar. Ele aceita um PDF ou URL do YouTube, processa via NotebookLM, e salva o resultado como nota estruturada no Obsidian automaticamente. Um log de sessões é mantido em markdown.

---

## Ambiente de desenvolvimento

```
OS:          Arch Linux / CachyOS com Hyprland
Python:      3.14.5
Venv:        .venv com --system-site-packages (OBRIGATÓRIO — PySide6 vem do sistema via pacman)
Shell:       Zsh
Localização: ~/Documentos/Kairos
```

### Como rodar

```bash
source .venv/bin/activate
python -m kairos.main
# ou simplesmente:
./run.sh
```

### Como buildar

```bash
./build.sh
# gera: dist/kairos (binário único, sem dependências externas)
```

O script ativa o venv automaticamente, instala o Nuitka se necessário (`requirements-dev.txt`) e chama:

```
nuitka --standalone --onefile --enable-plugin=pyside6
       --include-qt-plugins=sensible,styles,platforms
       --include-data-files=kairos/ui/styles.qss:kairos/ui/styles.qss
       --follow-imports --output-filename=kairos --output-dir=dist
       kairos/main.py
```

**Não atualizar o Nuitka** — versão travada em 4.1.2 (`requirements-dev.txt`). O Nuitka tem histórico de regressões com PySide6; só atualizar após testar o build completo.

O arquivo `kairos/ui/styles.qss` é incluído explicitamente porque é lido em tempo de execução via `Path(__file__).parent`. Sem o `--include-data-files`, o binário abre sem estilo visual.

---

## Regras absolutas — leia antes de qualquer código

**1. Nunca instalar PySide6 via pip.**
PySide6 está instalado via `pacman` no sistema (`extra/pyside6`). O venv usa `--system-site-packages` para enxergá-lo. Qualquer tentativa de instalar PySide6 via pip vai quebrar tudo porque pip não tem wheel compatível com Python 3.14.

**2. O venv sempre precisa de `--system-site-packages`.**
Se precisar recriar o venv:
```bash
python -m venv .venv --system-site-packages
```
Nunca recriar sem essa flag.

**3. Versões travadas — não atualizar sem testar.**
Nuitka tem histórico de regressões com PySide6. Só atualizar dependências se houver razão explícita e após testar o build.

**4. Sem lógica no lugar errado.**
Cada módulo tem responsabilidade única. Não colocar lógica de pipeline na UI, não colocar lógica de UI no pipeline. Se houver dúvida sobre onde algo vai, consultar a arquitetura abaixo.

**5. A janela nunca pode travar a UI.**
Todo processamento pesado (Playwright, extração de PDF, YouTube) roda em `QThread` ou via `QRunnable`. Nunca bloquear a thread principal.

**6. Nunca usar `pathlib2`.**
Python 3.14 tem `pathlib` nativo. `pathlib2` foi removido do requirements.txt.

---

## Stack técnica

| Componente | Tecnologia | Observação |
|---|---|---|
| GUI | PySide6 (via pacman) | Não instalar via pip |
| Build | Nuitka 4.1.2 | Versão travada |
| Automação NotebookLM | notebooklm-py 0.7.0 | API não-oficial, pode quebrar |
| Extração PDF | pymupdf4llm 0.0.17 | Output em markdown para LLMs |
| YouTube | youtube-transcript-api 1.2.4 + yt-dlp 2026.3.17 | Dois níveis de fallback |
| Notas | Obsidian vault (arquivos .md locais) | Sem plugin, escrita direta |
| Log | Markdown append-only | Sem banco de dados |
| Música | Simpmusic via subprocess | Player do usuário |

---

## Arquitetura de módulos

```
kairos/
├── main.py                    # Ponto de entrada. Só inicializa QApplication e MainWindow.
│
├── ui/                        # Tudo relacionado à interface. Zero lógica de negócio aqui.
│   ├── main_window.py         # Janela principal. Monta o layout, conecta signals.
│   ├── sidebar.py             # Painel esquerdo: sessão atual, log recente, config.
│   ├── drop_zone.py           # Widget de drag-and-drop para PDF/URL.
│   ├── prompt_selector.py     # QComboBox com os prompts configuráveis.
│   ├── progress_bar.py        # Barra de progresso + label de status em tempo real.
│   └── styles.qss             # Stylesheet Qt. Toda cor/fonte/borda fica aqui.
│
├── pipeline/                  # Lógica de processamento. Zero UI aqui.
│   ├── ingestor.py            # Recebe path/URL, identifica tipo, roteia.
│   ├── pdf_extractor.py       # pymupdf4llm → texto markdown.
│   ├── youtube_extractor.py   # transcript-api → fallback yt-dlp.
│   ├── processor.py           # notebooklm-py + fallback local.
│   ├── writer.py              # Gera e salva .md no vault Obsidian.
│   └── logger.py              # Append em study-log.md.
│
├── integrations/              # Wrappers de serviços externos.
│   ├── notebooklm_client.py   # Wrapper do notebooklm-py com tratamento de erro.
│   └── launcher.py            # Abre/fecha Simpmusic via subprocess.
│
└── config/
    ├── config.py              # Lê/escreve ~/.config/kairos/config.json.
    └── defaults.py            # DEFAULT_CONFIG com prompts padrão.
```

---

## Configuração do usuário

Localização em tempo de execução: `~/.config/kairos/config.json`

```json
{
  "obsidian_vault_path": "",
  "kairos_folder": "kairos",
  "log_filename": "study-log.md",
  "simpmusic_path": "",
  "simpmusic_autostart": true,
  "notebooklm_home": "~/.notebooklm",
  "prompts": [
    {
      "id": "beginner",
      "label": "Explique como iniciante",
      "text": "Explique esse conteúdo como se eu nunca tivesse visto esse assunto antes. Use exemplos práticos e evite jargão."
    },
    {
      "id": "concepts",
      "label": "Conceitos-chave",
      "text": "Quais são os conceitos-chave desse material? Liste e explique cada um brevemente."
    },
    {
      "id": "review",
      "label": "Perguntas de revisão",
      "text": "Crie 5 perguntas de revisão sobre esse conteúdo, do mais básico ao mais avançado."
    },
    {
      "id": "practical",
      "label": "Só o prático",
      "text": "Resuma apenas os pontos práticos e aplicáveis desse conteúdo. Ignore teoria pura e definições abstratas."
    },
    {
      "id": "cybersec",
      "label": "Aplicação em cibersegurança",
      "text": "Como esse conteúdo se aplica em cibersegurança? Quais são os casos de uso práticos, ferramentas relacionadas e possíveis vetores de ataque ou defesa?"
    }
  ]
}
```

---

## Tema visual

O Kairos tem estética minimalista escura, monoespaçada. Sem gradientes, sem sombras excessivas, sem cores vibrantes.

```
Fundo principal:    #0f0f0f
Fundo sidebar:      #0a0a0a
Superfícies:        #1a1a1a
Bordas:             #1e1e1e  (suaves) / #333333 (visíveis)
Texto principal:    #e0e0e0
Texto secundário:   #888888
Texto desabilitado: #555555
Fonte:              "JetBrains Mono", monospace, 13px
```

Toda estilização vai em `kairos/ui/styles.qss`. Nunca inline via `setStyleSheet()` em widgets individuais, exceto quando for absolutamente necessário e temporário.

---

## Pipeline de processamento

### Fluxo principal

```
Input (PDF path ou YouTube URL)
    ↓
ingestor.py — identifica tipo
    ├── PDF  → pdf_extractor.py (pymupdf4llm → markdown)
    └── URL  → youtube_extractor.py
                   ├── youtube-transcript-api (tentativa 1)
                   └── yt-dlp --write-auto-sub --skip-download (fallback)
    ↓
processor.py
    ├── Nível 1: notebooklm-py disponível e autenticado
    │   → cria notebook, sobe conteúdo, aplica prompt, captura resposta
    └── Nível 2: fallback local (notebooklm inacessível)
        → salva texto bruto, adiciona tag #pendente-notebooklm
    ↓
writer.py — gera .md com template fixo, salva no vault Obsidian
    ↓
logger.py — append em study-log.md
```

### Template da nota gerada

```markdown
---
date: YYYY-MM-DD
time: HH:MM
source: nome-do-arquivo.pdf
source_type: pdf
prompt: "label do prompt usado"
processed_by: notebooklm | local
tags: [kairos, pendente-revisao]
session_duration: Xm Ys
---

# nome-do-arquivo — label do prompt

## Resposta

[conteúdo aqui]

---

## Contexto da sessão

> Objetivo: [texto livre do usuário]

---

*Gerado pelo Kairos em YYYY-MM-DD às HH:MM*
*Fonte original: /caminho/completo/arquivo.pdf*
```

### Formato do log de sessões (`study-log.md`)

```markdown
| Data | Hora | Fonte | Prompt | Status | Duração |
|------|------|-------|--------|--------|---------|
| 2026-06-05 | 14:32 | redes-basicas.pdf | Conceitos-chave | ✓ | 2m14s |
| 2026-06-05 | 15:10 | https://youtu.be/xxx | Só o prático | ⚠ local | 0m43s |
```

---

## Riscos conhecidos e como lidar

### `notebooklm-py` quebrou após update do Google
**Sintoma:** erro de autenticação, `TargetClosedError`, ou timeout no Playwright.
**Ação:** `pip install --upgrade notebooklm-py` dentro do venv e testar.
**Fallback:** o `processor.py` já trata isso — salva texto bruto com tag `#pendente-notebooklm`.

### Sessão do NotebookLM expirou
**Sintoma:** erro 401 ou redirecionamento para login.
**Ação:** `notebooklm login` no terminal (menos de 1 minuto).

### `youtube-transcript-api` falhou
**Sintoma:** `TranscriptsDisabled` ou `NoTranscriptFound`.
**Ação:** o `youtube_extractor.py` já faz fallback automático para `yt-dlp`.

### Nuitka falhou no build
**Sintoma:** erro de compilação ou binário que não abre.
**Ação:** não atualizar Nuitka. Verificar se a versão travada (4.1.2) está sendo usada.
```bash
python -m nuitka --version  # deve retornar 4.1.2
```

---

## Estado de implementação

| Etapa | Descrição | Status |
|---|---|---|
| 1 | GUI base: janela vazia abrindo | ✅ concluída |
| 2 | Layout visual: sidebar + drop zone + prompt selector + botão | ✅ concluída |
| 3 | Drop de PDF funcionando + feedback visual | ✅ concluída |
| 4 | pymupdf4llm extraindo texto + preview | ✅ concluída |
| 5 | Playwright conectando no NotebookLM | ✅ concluída |
| 6 | writer.py salvando nota no Obsidian | ✅ concluída |
| 7 | logger.py registrando sessões | ✅ concluída |
| 8 | Fallback local quando NotebookLM falha | ✅ concluída |
| 9 | Suporte a YouTube | ✅ concluída |
| 10 | Prompts configuráveis pela interface | ✅ concluída |
| 11 | Simpmusic abrindo/fechando com o app | ✅ concluída |
| 12 | Build standalone via Nuitka | ✅ concluída |

---

## O que não fazer

- Não criar arquivos fora da estrutura definida sem justificativa
- Não adicionar dependências sem atualizar `requirements.txt` ou `requirements-dev.txt`
- Não usar `asyncio` diretamente na thread da UI — usar `QThread`
- Não usar `time.sleep()` na thread principal
- Não printar para stdout em produção — usar o sistema de log do Python (`logging`)
- Não hardcodar caminhos — tudo vem de `config.json` via `config.py`
- Não usar `os.path` — usar `pathlib.Path`
- Não instalar PySide6 via pip (já dito, mas vale repetir)

---

## Contexto do usuário (relevante para decisões de UX)

O usuário tem TDAH e TEA. Isso afeta diretamente decisões de interface:

- **Feedback imediato é obrigatório** — qualquer ação que demorar mais de 1 segundo precisa de indicador visual de progresso
- **Fricção zero no início** — o app abre pronto para uso, sem configuração inicial obrigatória
- **Uma coisa por vez** — a interface não deve mostrar múltiplas ações possíveis simultaneamente
- **Estado visível** — o usuário sempre sabe o que está acontecendo (status label atualizado em tempo real)
- **Sem surpresas** — erros mostram mensagem clara em PT-BR, nunca stacktrace cru

---

*Este arquivo deve ser atualizado a cada etapa concluída — especialmente a tabela de estado de implementação.*

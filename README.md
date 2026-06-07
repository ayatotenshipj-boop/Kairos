# Kairos

> *Do grego: o momento certo para agir.*

Kairos é um ambiente de estudo local, pessoal e automatizado, construído para um perfil cognitivo específico — TDAH e TEA — onde teoria sem prática não fixa, informação demais de uma vez trava, e o cérebro precisa de estrutura externa para funcionar bem.

Não é um app genérico de produtividade. É um ecossistema desenhado como um conjunto de engrenagens que se encaixam no funcionamento real de quem vai usar.

---

## Por que isso existe

O projeto nasceu de uma análise honesta de como o aprendizado funciona (ou não funciona) para perfis neurodivergentes. As dificuldades mapeadas foram:

- **Teoria sem âncora não fixa** — conceitos abstratos sem contexto prático escapam antes de chegar à memória de longo prazo
- **Sobrecarga cognitiva** — muita informação de uma vez trava o entendimento, especialmente conteúdo teórico denso
- **Dificuldade de iniciar** — o cérebro com TDAH tem baixa *antecipação* de recompensa, não baixa sensibilidade a ela — a motivação não aparece sozinha antes da tarefa começar
- **Aprendizado não-linear** — explorar, quebrar, testar e voltar preencher lacunas é o método natural, não um defeito
- **Dependência de estado interno** — sem estrutura externa, a sessão de estudo depende de "estar com vontade", o que raramente acontece

Cada componente do Kairos foi escolhido para atacar um desses pontos diretamente, com base em métodos com respaldo em evidências:

| Dificuldade | Mecanismo | Evidência |
|---|---|---|
| Teoria sem âncora | Prática primeiro, teoria depois (inductive learning) | Estudos de retenção em memória de trabalho |
| Sobrecarga cognitiva | Chunking — uma coisa por sessão, saída visível obrigatória | Neurociência da memória de trabalho |
| Dificuldade de iniciar | Estrutura de missão com desfecho claro antes da sessão | PINCH framework (dopamine-based motivation) |
| Esquecimento | Revisão espaçada via Anki integrado ao Obsidian | Spaced repetition — Ebbinghaus / FSRS algorithm |
| Dependência de estado | Scaffolding externo — ambiente carrega parte da carga cognitiva | External scaffolding para TDAH |
| Aprendizado não-linear | Mapa de território — registra o que foi explorado, não o que "deveria" ter sido | Autodidactic learning research |

---

## O que o Kairos faz

Kairos é um ambiente de estudo que você abre quando vai estudar. Ele:

1. **Lança o Simpmusic** automaticamente com sua playlist de foco ao abrir
2. **Aceita um PDF ou URL do YouTube** via interface gráfica simples
3. **Extrai o conteúdo localmente** — sem depender de internet para a parte local
4. **Processa via NotebookLM** (quando disponível) — manda o conteúdo, aplica um prompt escolhido por você, captura a resposta
5. **Salva uma nota estruturada no Obsidian** automaticamente, com template fixo
6. **Registra a sessão no log de progresso** — data, fonte, prompt, status
7. **Fecha o Simpmusic** junto quando você fecha o Kairos

Se o NotebookLM estiver inacessível (sessão expirada, Google fora do ar), o sistema não trava — salva o texto bruto localmente e marca a nota como `#pendente-notebooklm` para reprocessar depois.

---

## Stack técnica

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Interface gráfica | **PySide6** | Bindings Qt6 oficiais, LGPL, pacote nativo no Arch (`extra/pyside6 6.11.1`) |
| Compilação para executável | **Nuitka** (versão travada) | Recomendado pelo próprio Qt para deploy PySide6 em Linux |
| Automação NotebookLM | **`notebooklm-py`** | Abstrai o Playwright, mantido pela comunidade, API programática completa |
| Extração de PDF | **`pymupdf4llm`** | Output em Markdown otimizado para LLMs, 8-12x mais rápido que alternativas, AGPL (ok para uso pessoal/open source) |
| Transcrição YouTube | **`youtube-transcript-api`** + **`yt-dlp`** | Dois níveis de fallback — API direta primeiro, download de legenda depois |
| Notas | **Obsidian vault local** | Markdown puro, sem cloud, sem dependência externa |
| Log de sessões | **Markdown append-only** | Simples, legível, rastreável, sem banco de dados |
| Player de música | **Simpmusic** (subprocess) | Client YouTube do usuário, integrado via processo externo |
| Revisão espaçada | **Anki** (futuro) | Integração via plugin Obsidian → Anki |

### Por que não Tauri

Tauri foi avaliado e descartado por bugs ativos e confirmados no tracker oficial onde sidecars (processos externos Python) falham silenciosamente ao gerar AppImage no Linux. O app funciona em modo desenvolvimento mas quebra no build final — exatamente o caso de uso do Kairos.

### Por que não GTK4/libadwaita diretamente

Já foi usado em projetos anteriores (SimpleCustomizer). É viável para desenvolvimento, mas os bindings Python para GTK4 têm empacotamento instável com PyInstaller/Nuitka para distribuição. PySide6 tem pipeline de distribuição mais testado e documentado no Linux.

### Sobre o `notebooklm-py`

É uma biblioteca não-oficial que usa APIs internas não documentadas do Google. **Vai quebrar eventualmente** quando o Google atualizar algo. Isso é documentado pelo próprio mantenedor e aceito como trade-off. O sistema tem fallback local para lidar com isso sem interromper o fluxo de estudo.

---

## Ecossistema externo integrado

### Obsidian
Vault local em Markdown. O Kairos escreve notas diretamente nos arquivos `.md` — sem plugin, sem API, só escrita de arquivo. Plugins recomendados para usar junto:

- **Spaced Repetition** — flashcards diretamente nas notas, algoritmo FSRS
- **Dataview** — painéis dinâmicos de progresso
- **Templater** — template de sessão que elimina a decisão de como começar
- **Canvas** — mapa visual de território (o que já foi explorado)

### Anki
Software de flashcards open source com repetição espaçada. Integração futura via plugin Obsidian → Anki: cards criados nas notas são exportados automaticamente. Decks prontos de cibersegurança disponíveis no AnkiWeb.

### NotebookLM (Google)
Ferramenta de IA do Google que processa documentos e gera resumos, explicações, perguntas de revisão e Audio Overviews (áudio estilo podcast). Usado como serviço externo pontual — não é dependência central. Requer login com conta Google.

### Simpmusic
Client YouTube do usuário. Lançado automaticamente ao abrir o Kairos, encerrado junto. Fornece o áudio ambiente de foco (lo-fi, brown noise, trilhas de jogos) que estudos mostram melhorar memória de trabalho vs. silêncio.

---

## Arquitetura interna

```
┌─────────────────────────────────────────────────────┐
│                  KAIROS (PySide6)                   │
│              Janela nativa Linux                    │
│           Compilada com Nuitka standalone           │
│                                                     │
│  ┌──────────────┐      ┌──────────────────────────┐ │
│  │   Sidebar    │      │     Área Principal       │ │
│  │              │      │                          │ │
│  │  • Sessão    │      │  ┌──────────────────┐    │ │
│  │    atual     │      │  │   Drop Zone      │    │ │
│  │              │      │  │  PDF / YouTube   │    │ │
│  │  • Log de    │      │  └──────────────────┘    │ │
│  │    sessões   │      │                          │ │
│  │              │      │  Seletor de Prompt       │ │
│  │  • Config    │      │  ┌──────────────────┐    │ │
│  │              │      │  │ • Como iniciante │    │ │
│  └──────────────┘      │  │ • Conceitos-chave│    │ │
│                         │  │ • Perguntas rev. │    │ │
│                         │  │ • Só prático     │    │ │
│                         │  │ • Cybersecurity  │    │ │
│                         │  └──────────────────┘    │ │
│                         │                          │ │
│                         │  [▶ Processar]           │ │
│                         │                          │ │
│                         │  Status em tempo real    │ │
│                         │  ████████░░ Extraindo... │ │
│                         └──────────────────────────┘ │
└──────────────────────────┬──────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │    PIPELINE INTERNO     │
              │      (Python puro)      │
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ingestor.py        launcher.py        config.py
   Identifica o       Abre/fecha         Lê ~/.config/
   tipo de input      Simpmusic          kairos/config.json
   (PDF ou YouTube)   via subprocess
        │
        ├── PDF ──────────────────────────────────────┐
        │                                             │
        │   pymupdf4llm                               │
        │   Extrai texto → Markdown estruturado       │
        │   local, sem internet, sem dependência      │
        │                                             │
        └── YouTube ──────────────────────────────────┤
                                                      │
            youtube-transcript-api                    │
            Tenta pegar transcrição diretamente       │
                 │                                    │
                 └─ falhou? ──► yt-dlp               │
                               Baixa só legenda       │
                               (--skip-download)      │
                                         │            │
                                         ▼            ▼
                                    processor.py ◄────┘
                                    Recebe o texto extraído
                                              │
                              ┌───────────────┴────────────────┐
                              │                                │
                        NÍVEL 1                          NÍVEL 2
                    notebooklm-py                    Fallback local
                    disponível?                      (sessão expirada
                         │                           / Google fora)
                         │ sim                             │
                         ▼                                 ▼
                  Cria notebook               Salva texto bruto
                  Sobe conteúdo              Tag: #pendente-notebooklm
                  Aplica prompt              Anotação no log
                  Captura resposta
                         │
                         └────────────────────┐
                                              │
                                              ▼
                                        writer.py
                                  Gera arquivo .md
                                  com template fixo
                                  Salva no vault do
                                  Obsidian
                                              │
                                              ▼
                                        logger.py
                                  Append em study-log.md
                                  Data | Fonte | Prompt
                                  Duração | Status
```

---

## Fluxo completo de uma sessão

```
01. Usuário abre o Kairos
        │
02.     └─► launcher.py inicia o Simpmusic
               Playlist de foco começa automaticamente

03. Interface carrega
        Template de sessão pré-preenchido:
        data atual + objetivo (campo editável)

04. Usuário arrasta um PDF ou cola URL do YouTube
        Drop zone aceita ambos
        Identificação automática do tipo

05. Usuário escolhe o prompt:
        "Explique como se eu nunca tivesse visto esse assunto"
        "Quais são os conceitos-chave?"
        "Crie perguntas de revisão"
        "Resuma só os pontos práticos, ignore teoria pura"
        "Como isso se aplica em cibersegurança?"
        [+ prompts customizados que você adiciona]

06. Clica em [▶ Processar]
        Barra de progresso aparece
        Status atualiza em tempo real:
        "Extraindo texto..."
        "Conectando ao NotebookLM..."
        "Processando..."
        "Salvando nota..."

07. Pipeline executa (em background, sem travar a UI):
        PDF → pymupdf4llm → texto markdown
        YouTube → transcript-api / yt-dlp → texto
        texto → notebooklm-py → resposta processada
            └─ falhou? → texto bruto com tag #pendente

08. writer.py salva no Obsidian:
        ~/obsidian-vault/kairos/2026-06-05-nome-do-arquivo.md

09. logger.py registra no log:
        | 2026-06-05 | 14:32 | redes-basicas.pdf | Conceitos-chave | ✓ | 2m14s |

10. Interface mostra: "Nota salva em Obsidian ✓"
        Link clicável para abrir no Obsidian

11. Usuário fecha o Kairos
        └─► launcher.py encerra o Simpmusic
```

---

## Template da nota gerada no Obsidian

```markdown
---
date: 2026-06-05
time: 14:32
source: redes-basicas.pdf
source_type: pdf
prompt: "Quais são os conceitos-chave?"
processed_by: notebooklm
tags: [kairos, pendente-revisao]
session_duration: 2m14s
---

# redes-basicas — Conceitos-chave

## Resposta do NotebookLM

[conteúdo processado aqui]

---

## Contexto da sessão

> Objetivo da sessão: entender o básico de endereçamento IP

---

*Gerado pelo Kairos em 2026-06-05 às 14:32*
*Fonte original: `/home/user/downloads/redes-basicas.pdf`*
```

---

## Estrutura de arquivos do projeto

```
kairos/
│
├── README.md                        ← este arquivo
│
├── requirements.txt                 ← dependências Python com versões travadas
├── requirements-dev.txt             ← dependências de desenvolvimento (Nuitka, etc)
│
├── build.sh                         ← script de build do executável via Nuitka
├── run.sh                           ← atalho para rodar em modo desenvolvimento
│
├── kairos/                          ← pacote principal
│   ├── __init__.py
│   ├── main.py                      ← ponto de entrada, inicializa a aplicação
│   │
│   ├── ui/                          ← interface gráfica PySide6
│   │   ├── __init__.py
│   │   ├── main_window.py           ← janela principal
│   │   ├── sidebar.py               ← sidebar com log e config
│   │   ├── drop_zone.py             ← widget de arrastar/soltar arquivo
│   │   ├── prompt_selector.py       ← seletor de prompts
│   │   ├── progress_bar.py          ← barra de progresso com status
│   │   └── styles.qss               ← stylesheet Qt (tema visual)
│   │
│   ├── pipeline/                    ← lógica de processamento
│   │   ├── __init__.py
│   │   ├── ingestor.py              ← identifica o tipo de input e roteia
│   │   ├── pdf_extractor.py         ← pymupdf4llm → texto markdown
│   │   ├── youtube_extractor.py     ← transcript-api + yt-dlp fallback
│   │   ├── processor.py             ← notebooklm-py + fallback local
│   │   ├── writer.py                ← gera e salva .md no vault Obsidian
│   │   └── logger.py                ← append no study-log.md
│   │
│   ├── integrations/                ← integrações externas
│   │   ├── __init__.py
│   │   ├── notebooklm_client.py     ← wrapper do notebooklm-py
│   │   └── launcher.py              ← abre/fecha Simpmusic via subprocess
│   │
│   └── config/                      ← configuração
│       ├── __init__.py
│       ├── config.py                ← lê/escreve ~/.config/kairos/config.json
│       └── defaults.py              ← valores padrão (prompts, caminhos, etc)
│
├── assets/
│   ├── icon.png                     ← ícone do app
│   └── icon.svg
│
└── tests/                           ← testes unitários (futuro)
    ├── test_pdf_extractor.py
    ├── test_youtube_extractor.py
    └── test_writer.py
```

---

## Arquivo de configuração

Localização: `~/.config/kairos/config.json`

```json
{
  "obsidian_vault_path": "/home/user/obsidian-vault",
  "kairos_folder": "kairos",
  "log_filename": "study-log.md",
  "simpmusic_path": "/usr/bin/simpmusic",
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

## Configuração do ambiente de desenvolvimento

### Pré-requisitos

```bash
# Arch Linux / CachyOS
sudo pacman -S python pyside6 pyside6-tools

# Dependências do sistema para Playwright (notebooklm-py)
sudo pacman -S chromium

# yt-dlp
sudo pacman -S yt-dlp
```

### Setup do projeto

```bash
git clone https://github.com/seu-usuario/kairos.git
cd kairos

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright browsers (necessário para notebooklm-py)
playwright install chromium

# Fazer login no NotebookLM (único passo manual, salva sessão)
notebooklm login

# Rodar em modo desenvolvimento
./run.sh
```

### Build do executável

```bash
# Ativar venv
source .venv/bin/activate

# Build standalone (gera kairos.dist/)
./build.sh

# Executar o binário gerado
./kairos.dist/kairos
```

O `build.sh` usa as flags:
```bash
python -m nuitka \
  --standalone \
  --enable-plugin=pyside6 \
  --include-qt-plugins=sensible,styles,platforms \
  --follow-imports \
  --output-dir=dist \
  kairos/main.py
```

---

## Dependências (requirements.txt)

```
# Interface
PySide6==6.11.1

# Extração de PDF
pymupdf4llm==0.0.17

# YouTube
youtube-transcript-api==0.6.3
yt-dlp==2026.5.1

# Automação NotebookLM
notebooklm-py[browser]==0.9.0

# Utilitários
pathlib2==2.3.7
```

> **Importante:** versões travadas intencionalmente.
> `notebooklm-py` e `yt-dlp` mudam com frequência para acompanhar mudanças no Google/YouTube.
> Atualize um de cada vez e teste antes de commitar.

---

## Ordem de implementação

O projeto foi planejado para que cada etapa entregue algo funcional — você nunca fica com código pela metade sem poder testar.

```
Etapa 1  →  GUI base rodando: janela, sidebar, drop zone, botão
Etapa 2  →  Simpmusic abrindo e fechando com o app
Etapa 3  →  Drop de PDF funcionando + feedback visual de progresso
Etapa 4  →  pymupdf4llm extraindo texto e mostrando preview
Etapa 5  →  Playwright conectando no NotebookLM + processamento
Etapa 6  →  writer.py salvando nota no vault Obsidian
Etapa 7  →  logger.py registrando sessões no study-log.md
Etapa 8  →  Fallback local quando NotebookLM falha
Etapa 9  →  Suporte a YouTube (transcript-api + yt-dlp)
Etapa 10 →  Prompts configuráveis pela interface
Etapa 11 →  Build .standalone via Nuitka
```

---

## Riscos conhecidos e mitigações

### `notebooklm-py` pode quebrar
**Causa:** usa APIs internas não documentadas do Google.
**Frequência:** imprevisível — a cada update do NotebookLM.
**Mitigação:** fallback local implementado no `processor.py`. Quando falha, salva texto bruto com tag `#pendente-notebooklm`. Você reprocessa quando a biblioteca for atualizada.
**Ação quando quebrar:** `pip install --upgrade notebooklm-py` e testar.

### `youtube-transcript-api` pode falhar em alguns vídeos
**Causa:** YouTube muda endpoints internamente; alguns vídeos não têm transcrição.
**Mitigação:** `yt-dlp` como segunda camada (`--write-auto-sub --skip-download`). Se ambos falharem, o Kairos informa e não processa.

### Nuitka pode regredir com PySide6
**Causa:** histórico de incompatibilidades entre versões do Nuitka e PySide6.
**Mitigação:** versão do Nuitka travada no `requirements-dev.txt`. Só atualizar após testar.

### Sessão do NotebookLM expira
**Causa:** tokens Google têm validade.
**Mitigação:** `notebooklm-py` tem renovação automática de CSRF em 5 camadas. Se expirar completamente, roda `notebooklm login` — processo de menos de 1 minuto.

---

## Contexto de aprendizado

O Kairos é parte de um sistema maior de estudo, não apenas um app isolado. O ecossistema completo inclui:

**Obsidian** como segundo cérebro — notas conectadas, mapa de território do que foi aprendido, progresso visível acumulado.

**Anki** para revisão espaçada — flashcards gerados a partir das notas do Obsidian, revisados em ciclos que aumentam progressivamente.

**NotebookLM** como processador de material denso — teoria que entra pelo ouvido (Audio Overview) enquanto você pratica no terminal.

**Simpmusic** como ambiente sonoro — lo-fi beats ou brown noise que estudos mostram melhorar memória de trabalho vs. silêncio.

O sistema foi desenhado em torno de sete princípios derivados da neurociência do aprendizado para TDAH/TEA:

1. **Prática primeiro** — experimento antes da teoria
2. **Chunking** — uma unidade por sessão, saída visível obrigatória
3. **Dopamina estruturada** — antecipação antes da sessão, não só recompensa depois
4. **Revisão espaçada** — micro-tarefas práticas, não flashcards abstratos
5. **Scaffolding externo** — o ambiente carrega parte da carga cognitiva
6. **Ciclos curtos** — sessões de 25 minutos, uma linha de log ao fim
7. **Exploração legitimada** — mapa de território, não currículo linear

---

## Licença

MIT — use, modifique, distribua.
Se você usar `pymupdf4llm`, seu projeto também fica sujeito à AGPL para distribuição comercial. Para uso pessoal e open source, sem restrição.

---

*Kairos — construído para um cérebro específico, mas com princípios que funcionam para qualquer um que aprende melhor fazendo do que lendo.*

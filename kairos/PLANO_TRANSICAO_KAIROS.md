# Plano de Transição Profunda — Kairos

Documento de trabalho para execução incremental no Claude Code.
Cada fase é independente, com escopo fechado, verificação e checkpoint
de aprovação. Adapte o que faltar conforme avança.

---

## Como usar este plano

1. Antes de cada fase: `Shift+Tab` até **plan mode**. Deixe o Claude ler
   e propor antes de escrever.
2. Aprove o plano da fase. Só então `Shift+Tab` → **accept edits**.
3. `/compact` entre fases para liberar contexto.
4. Uma fase por sessão sempre que possível. Não pule a verificação.
5. Leia o `CLAUDE.md` no início de toda sessão — ele tem as regras
   invioláveis (pathlib only, sem os.path, UI nunca bloqueia, erros PT-BR,
   PySide6 via pacman, separação estrita de camadas).

### Setup obrigatório antes da Fase 6

Salve o protótipo aprovado dentro do repositório, versionado, para o
Claude Code ler os valores exatos (não reinterpretar):

```bash
mkdir -p ~/Documentos/Kairos/docs
cp kairos_ui_prototype_v2.html ~/Documentos/Kairos/docs/ui_reference.html
```

Esse arquivo é a **fonte da verdade visual**. A Fase 6 extrai dele os
tokens exatos. Sem ele no repo, o resultado vai divergir do aprovado.

---

## Contexto do projeto

Kairos é um **client intermediário** entre NotebookLM (pesquisador) e
Obsidian (memória). Fluxo conceitual:

```
Material (PDF / YouTube / Áudio)
   → Kairos extrai o conteúdo
   → injeta instrução de estrutura no prompt
   → NotebookLM (ou backend alternativo) gera tema + sub-temas
   → Obsidian armazena como pasta + notas linkadas
   → Kairos projeta o mapa de conhecimento
```

Cada ferramenta no seu papel: NotebookLM estrutura, Obsidian guarda,
Kairos sintetiza e visualiza.

Arquitetura de pastas (não reorganizar):
```
kairos/
├── main.py            # bootstrap, QQmlApplicationEngine
├── ui/                # QML + backend bridge (sem lógica de negócio)
│   ├── backend.py
│   ├── workers.py
│   └── qml/
├── pipeline/          # processamento (sem UI)
├── integrations/      # serviços externos
└── config/            # persistência
```

---

## Estado atual (já concluído)

> A Fase 0 vai confirmar o estado real no disco. Esta lista é o que foi
> decidido/executado em sessões anteriores — trate como referência, não
> como verdade absoluta.

- **Migração para QML concluída.** Camada `ui/` em Qt Quick: `Theme.qml`,
  `DropZone.qml`, `PipelineTracker.qml`, `main.qml`, `SettingsDialog.qml`,
  backend QObject em `backend.py`, workers em `workers.py`. `main.py` carrega
  via `QQmlApplicationEngine`. Arquivos de widget antigos + `styles.qss`
  removidos.
- **Gaps de UX corrigidos:** suporte a `prefers-reduced-motion`, tempo
  decorrido por fase no pipeline tracker, controles do SimpMusic no rodapé
  da sidebar.
- **Correções de build/scripts (confirmar se aplicadas na Fase 0):**
  - `run.sh`: `pip install -q` (sem ruído de "Requirement already satisfied")
  - `.gitignore`: `kairos.pid` adicionado
  - `launcher.py`: graceful shutdown com `process.wait(timeout=5)` +
    `except TimeoutExpired → kill()`
  - `build.sh`: ver Fase 6 — `--include-package=yt_dlp` é **redundante**
    (yt-dlp é chamado como subprocess CLI, não importado como módulo)

---

## Visão da transição (o que vamos construir)

1. **Backends de processamento plugáveis** — NotebookLM / Gemini API /
   Local (Ollama), selecionáveis. Resolve a fragilidade do NotebookLM.
2. **Sistema de prompts** — defaults + customizados editáveis, com injeção
   automática da instrução de estrutura (tema + sub-temas).
3. **Mapa de conhecimento** — lê a estrutura do vault Obsidian e projeta
   grafo radial após o processamento.
4. **Integração SimpMusic via MPRIS** — música em segundo plano + mini-player
   funcional, sem dividir a tela.
5. **Redesign visual** — aplicar a estética do protótipo (âmbar sobre tinta,
   hierarquia clara, animações com propósito).
6. **Atualização de README e build.**

Referência visual e funcional: o protótipo, salvo no repo como
`docs/ui_reference.html` (ver Setup acima). Os tokens CSS no topo dele
mapeiam 1:1 para `Theme.qml`.

---

# FASE 0 — Auditoria do estado real

**Objetivo:** estabelecer o que existe de fato antes de qualquer mudança.

Rodar (plan mode, sem editar):
```bash
find kairos/ -name "*.py" -o -name "*.qml" | sort
cat kairos/ui/qml/Theme.qml
ruff check kairos/
qmllint kairos/ui/qml/*.qml
python -m py_compile kairos/main.py kairos/ui/backend.py kairos/ui/workers.py
grep -n "include-package" build.sh
grep -n "pip install" run.sh
grep -n "kairos.pid" .gitignore
```

Confirmar contra "Estado atual" acima. Reportar divergências.
**Checkpoint:** alinhar o que está feito vs pendente antes de prosseguir.

---

# FASE 1 — Backends de processamento plugáveis

**Por quê:** o NotebookLM (via `notebooklm-py`) é estruturalmente frágil —
usa APIs internas não documentadas do Google e cookies de sessão que expiram.
Para um projeto open-source, a arquitetura honesta é dar ao usuário a escolha
do backend, com o fallback local deixando de ser "plano B envergonhado".

**Arquivos:**
- `kairos/pipeline/processor.py` (refatorar para roteador)
- `kairos/integrations/notebooklm_client.py` (existente)
- `kairos/integrations/gemini_client.py` (novo)
- `kairos/integrations/local_client.py` (novo — Ollama)
- `kairos/config/defaults.py` (adicionar chave `processor_backend`)

**Implementação:**

1. Definir um protocolo comum. Todos os clients expõem a mesma interface:
   ```python
   def process(text: str, prompt: str) -> tuple[str, str]:
       """Retorna (markdown_resultado, modo). modo ∈ {'remoto','local'}."""
   ```
2. `processor.py` vira roteador: lê `config['processor_backend']`
   ('notebooklm' | 'gemini' | 'local') e delega ao client certo.
   Mantém o fallback automático para local se o backend remoto falhar
   (preserva o comportamento atual com tag `#pendente-notebooklm`).
3. **Gemini** (`gemini_client.py`): usa `google-generativeai`, modelo
   `gemini-flash` (free tier). API key via config ou variável de ambiente
   `GEMINI_API_KEY`. Documentar no app que o free tier usa inputs para
   treino do Google (privacidade).
4. **Local** (`local_client.py`): chama Ollama local via HTTP
   (`http://localhost:11434`). Modelo configurável (default sugerido para
   geração de notas, não coder). Zero auth, offline.
5. **Settings (QML):** adicionar seletor de backend. Campo de API key do
   Gemini (oculto). Aviso de privacidade do free tier.

**Dependências novas:** `google-generativeai` no `requirements.txt`.
Ollama já está no sistema. (Aprovar antes de adicionar — regra do CLAUDE.md.)

**Verificação:**
```bash
python -c "from kairos.integrations.gemini_client import process; print('OK')"
python -c "from kairos.integrations.local_client import process; print('OK')"
./run.sh   # trocar backend nas Settings e processar com cada um
```

**Checkpoint:** confirmar que os três backends respeitam o mesmo contrato e
o fallback funciona.

---

# FASE 2 — Reliability do NotebookLM

**Objetivo:** reduzir ao máximo a quebra do NotebookLM quando ele for o
backend escolhido. Não elimina o risco estrutural, mas trata expiração.

**Arquivos:**
- `kairos/integrations/notebooklm_client.py`
- `requirements.txt` (verificar pin de versão)
- Novo: arquivo de unit systemd do usuário (fora do pacote Python)

**Implementação:**

1. **Verificar versão:** confirmar a versão de `notebooklm-py` realmente
   instalada vs a pinada no `requirements.txt`. Se houver mismatch (ex.
   pin em versão inexistente no PyPI), corrigir o pin para a instalada.
2. **Auth check no startup:** ao iniciar com backend NotebookLM, rodar
   `notebooklm auth check --test`. Se falhar, mostrar aviso PT-BR claro
   na UI ("Sessão do NotebookLM expirada — rode: notebooklm auth refresh")
   e cair para fallback, sem travar.
3. **Keepalive systemd (documentar, não embutir no app):**
   ```ini
   # ~/.config/systemd/user/kairos-notebooklm.service
   [Service]
   Type=oneshot
   ExecStart=notebooklm auth refresh --quiet

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
4. Usar `keepalive=<segundos>` no `NotebookLMClient` se a versão suportar
   (long-lived worker, sem agendador externo).

**Verificação:**
```bash
notebooklm auth check --test
./run.sh   # com backend NotebookLM, processar; simular expiração → fallback
```

**Checkpoint:** auth check no startup + mensagem PT-BR + fallback funcionando.

---

# FASE 3 — Sistema de prompts com injeção de estrutura

**Objetivo:** prompts default + customizados editáveis. Todo prompt recebe,
por trás, a instrução fixa de estruturar em tema + sub-temas. É isso que
alimenta o mapa de conhecimento na Fase 4.

**Arquivos:**
- `kairos/config/defaults.py` (prompts default)
- `kairos/config/config.py` (CRUD de prompts já existe — revisar)
- `kairos/pipeline/processor.py` (montagem do prompt final)
- `kairos/ui/qml/SettingsDialog.qml` ou modal de prompt (editor)
- `kairos/ui/backend.py` (expor prompts + CRUD à QML)

**Implementação:**

1. **Estrutura de cada prompt:**
   ```python
   {"id": "...", "name": "...", "desc": "...", "text": "..."}
   ```
2. **Prompts default** (editáveis pelo usuário):
   - Explique como criança — simplifica, sem jargão
   - Entenda profundamente — causas, consequências, contexto
   - Aprenda na prática — exemplos e aplicações
   - Conecte conceitos — relaciona com o que já se sabe
   - Resumo para revisão — síntese densa
3. **Injeção automática:** o `processor` sempre concatena ao texto do prompt
   escolhido a instrução fixa:
   > "Estruture o conteúdo como um tema principal com sub-temas conectados.
   > No Obsidian: o tema vira uma pasta, cada sub-tema uma nota linkada de
   > volta ao tema central."
   Essa instrução **não é editável** pelo usuário — é parte da arquitetura.
4. **Editor de prompt (QML):** abrir via ícone de lápis no item / botão
   "Novo". Campos: nome, descrição, texto. Exibir bloco destacado mostrando
   a instrução de estrutura sempre adicionada (read-only). Validação PT-BR
   (nome e texto obrigatórios; mínimo 1 prompt).
   Referência visual: o modal do protótipo v2.

**Verificação:**
```bash
./run.sh   # criar/editar/remover prompt, salvar, reabrir, conferir persistência
# processar e inspecionar o prompt final montado (log em DEBUG)
```

**Checkpoint:** prompt final = texto do usuário + instrução de estrutura,
persistência ok.

---

# FASE 4 — Mapa de conhecimento (projeção do Obsidian)

**Objetivo:** após processar, projetar o tema recém-criado como grafo radial
(nó central + sub-temas), lendo a estrutura real do vault. Read-only — o
Kairos desenha, não gera.

**Arquivos:**
- `kairos/integrations/obsidian_graph.py` (novo — leitor de vault)
- `kairos/pipeline/writer.py` (garantir estrutura pasta + wikilinks)
- `kairos/ui/qml/KnowledgeMap.qml` (novo — visualização)
- `kairos/ui/backend.py` (expor dados do grafo à QML)

**Implementação:**

1. **Writer (estrutura no Obsidian):** ao salvar, criar:
   ```
   <Vault>/<Tema>/
      ├── <Tema>.md            (nota central)
      ├── <Sub-tema 1>.md
      ├── <Sub-tema 2>.md
      └── ...
   ```
   Cada sub-nota com `[[<Tema>]]` linkando de volta à central.
   Usar `pathlib.Path` (regra do CLAUDE.md). Nada de os.path.
2. **Leitor de grafo** (`obsidian_graph.py`): dado o caminho da pasta do
   tema, ler a nota central + os arquivos `.md` da pasta, extrair os
   `[[wikilinks]]`, e devolver uma estrutura:
   ```python
   {"central": "O que é IP", "nodes": ["IP público", "NAT", ...]}
   ```
   Não escanear o vault inteiro — só a pasta do tema processado.
3. **Visualização** (`KnowledgeMap.qml`): grafo radial — nó central no meio,
   sub-nós distribuídos em círculo, linhas conectando. Aparece logo após o
   pipeline concluir (estado `success`). Clicar num nó abre a nota no
   Obsidian via URI `obsidian://open?path=...` ou abertura de arquivo.
   Animação de surgimento (linhas desenhando, nós escalonados), respeitando
   reduced-motion. Referência visual: seção brain map do protótipo v2.

**Nota de escopo:** layout radial cobre 1 tema com poucos sub-temas. Para
muitos nós ou múltiplos níveis no futuro, considerar layout force-directed
(como o grafo nativo do Obsidian). Não implementar isso agora.

**Verificação:**
```bash
python -c "from kairos.integrations.obsidian_graph import read_theme; print('OK')"
./run.sh   # processar um tema → mapa aparece → clicar nó abre no Obsidian
```

**Checkpoint:** estrutura criada no vault corretamente + mapa projeta + clique
abre no Obsidian.

---

# FASE 5 — Integração SimpMusic via MPRIS

**Objetivo:** música em segundo plano sem dividir a tela; mini-player no
Kairos lendo metadados e controlando playback via D-Bus/MPRIS.

> **VERIFICAR PRIMEIRO (em casa, antes de codar):**
> ```bash
> playerctl -l                          # SimpMusic aparece na lista?
> playerctl -p simpmusic metadata       # retorna título/artista?
> playerctl -p simpmusic play-pause     # controla?
> ```
> - Se listar e controlar → seguir esta fase.
> - Se vazio → SimpMusic não expõe MPRIS no Linux. Alternativa: backend de
>   música headless (ex. `mpd`), perdendo YouTube Music. Reavaliar.

**Arquivos:**
- `kairos/integrations/launcher.py` (refatorar de "abrir app" para MPRIS)
- `kairos/integrations/music_mpris.py` (novo — controle MPRIS)
- `kairos/ui/qml/MiniPlayer.qml` (novo ou evoluir o rodapé existente)
- `kairos/ui/backend.py` (expor estado do player + comandos)
- Config do Hyprland (fora do projeto — documentar)

**Implementação:**

1. **Hyprland — abrir em segundo plano (documentar):**
   ```
   # ~/.config/hypr/hyprland.conf
   windowrulev2 = workspace special:music silent, class:^(simpmusic)$
   windowrulev2 = float, class:^(simpmusic)$
   ```
   O SimpMusic abre tocando, vai para workspace especial silencioso, não
   rouba a tela.
2. **Controle MPRIS** (`music_mpris.py`): via `playerctl` (subprocess, encaixa
   no padrão atual) ou binding D-Bus Python. Funções:
   - `metadata()` → título, artista, capa, posição, duração
   - `play_pause()`, `next()`, `previous()`
   - `volume(level)`
   - `status()` → playing / paused / stopped
3. **Launcher:** iniciar o SimpMusic em background no startup do Kairos (ou
   sob demanda). Manter o graceful shutdown no fechamento.
4. **Mini-player (QML):** ler metadados em tempo real (polling leve, sem
   travar a UI — worker/timer), exibir capa + título + artista, botões
   play/pause/next/prev + volume. Referência visual: o player do rodapé no
   protótipo v2.

**Verificação:**
```bash
./run.sh   # música toca em background, mini-player mostra faixa e controla
# confirmar que a janela do SimpMusic não aparece na tela principal
```

**Checkpoint:** background sem split + metadados + controles funcionando.

---

# FASE 6 — Redesign visual (replicar o protótipo aprovado)

**Objetivo:** reproduzir em QML, com fidelidade, o protótipo aprovado em
`docs/ui_reference.html`. Não é "se inspirar" — é **extrair os valores
exatos** (cores, espaçamentos, tamanhos, durações, animações) do arquivo de
referência e replicar componente por componente. O resultado deve ser
visualmente indistinguível do protótipo, adaptado às limitações do QML.

**Pré-requisito:** `docs/ui_reference.html` existe no repo (ver Setup no topo
do plano). Se não existir, **parar** e pedir o arquivo antes de prosseguir.

**Arquivos:**
- `kairos/ui/qml/Theme.qml` (tokens — extraídos do CSS da referência)
- Todos os componentes QML (replicar layout e estados da referência)
- `kairos/ui/backend.py` (estado de tema, se o toggle for persistido)

**Passo 1 — Extrair os tokens do arquivo de referência**

Abrir e ler `docs/ui_reference.html`. Localizar os blocos
`[data-theme="dark"]` e `[data-theme="light"]` no `<style>` e transcrever
**cada variável CSS** para propriedades `readonly` no `Theme.qml`, sem
arredondar nem "melhorar" valores. Lista a transcrever:

```
--bg-base, --bg-surface, --bg-elevated
--border, --border-strong
--text-1, --text-2, --text-3
--accent, --accent-hover, --accent-dim, --accent-glow, --on-accent
--success, --success-dim
--error, --error-dim
--warning, --warning-dim
```

Também extrair da referência: a família tipográfica (JetBrains Mono), os
tamanhos de fonte e letter-spacing usados, a escala de espaçamento
(paddings/margins recorrentes), os border-radius, e as durações/curvas das
animações (`heartbeat`, `breathe`, `nodepulse`, `drawLine`, `popIn`,
`revealUp`).

O `Theme.qml` deve suportar os dois temas — uma propriedade de modo
(claro/escuro) que troca o conjunto de tokens, espelhando o
`data-theme` do protótipo.

**Passo 2 — Replicar componente por componente, contra a referência**

Para cada componente, abrir a seção correspondente no HTML, replicar o
layout/estados em QML usando só tokens do `Theme.qml`, e comparar lado a
lado. Ordem:

1. **Sidebar** — wordmark KAIROS (dot pulsante + letter-spacing 7px), tagline,
   bloco de conexões NotebookLM⇄Obsidian, seletor de prompts ("Como aprender"),
   sessões recentes, rodapé com mini-player + Config.
2. **DropZone** — estados idle (pulso `breathe`), drag-over, accepted, invalid;
   ícone, título, subtítulo, tags de tipo (PDF/YouTube/Áudio).
3. **PipelineTracker** — 4 fases (Extração → NotebookLM → Síntese → Obsidian),
   nós com estados pending/active/done/error, linhas que preenchem, tempo
   decorrido, label uppercase.
4. **Botão Processar** — ação primária; estados normal/hover/disabled/running
   (spinner + texto "PROCESSANDO").
5. **Linha de status** — estados idle/running/success/error/warning com as
   cores semânticas exatas.
6. **KnowledgeMap** (já criado na Fase 4) — aplicar os tokens e o estilo de
   nós/linhas da referência (dot central âmbar com glow, sub-nós outline,
   labels, hover destacando a conexão).
7. **Modal de prompt** (Fase 3) — aplicar o visual do modal da referência,
   incluindo o bloco âmbar "Sempre adicionado automaticamente".
8. **Toggle de tema** — botão flutuante claro/escuro; persistir o modo em
   config.

**Passo 3 — Hierarquia e fluxo (conforme a referência)**

- "KAIROS" com presença real (não um label secundário).
- DropZone como elemento mais chamativo do painel.
- Botão Processar como ação primária inconfundível.
- Estrutura organizada nas duas perguntas: "O que aprender?" (DropZone) e
  "Como aprender?" (seletor de prompt).
- Bloco de conexões reforçando o conceito de ponte.

**Adaptações QML esperadas (limitações vs CSS):**
- Transições suaves: `Behavior on <prop>` + `ColorAnimation`/`NumberAnimation`
  no lugar das CSS transitions.
- Estados da DropZone: `states` + `transitions` no lugar das classes CSS.
- Glow: `layer.effect` + efeito de Glow/Shadow (QtQuick.Effects) aproximando o
  `box-shadow`/`accent-glow` da referência.
- Pulsos e reveal: `SequentialAnimation`/`NumberAnimation`.
- Tudo respeitando `prefers-reduced-motion` (já tratado em fase anterior):
  com reduced-motion, transições instantâneas e sem pulso/reveal.

**Verificação:**
```bash
qmllint kairos/ui/qml/*.qml
./run.sh
```
Abrir `docs/ui_reference.html` no navegador e comparar lado a lado com o app:
- [ ] Paleta idêntica nos dois temas (conferir alguns hex contra o CSS)
- [ ] Tipografia, espaçamento e radius batendo com a referência
- [ ] Cada componente reconhecível como o do protótipo
- [ ] Toggle claro/escuro funcionando e persistindo
- [ ] Animações presentes e respeitando reduced-motion
- [ ] Nenhum valor hardcoded fora do `Theme.qml`

**Checkpoint:** app visualmente fiel ao `docs/ui_reference.html`, sem
regressão funcional.

---

# FASE 7 — README e build

**Objetivo:** documentação refletindo a arquitetura real; build empacotando
o runtime QML.

**Arquivos:**
- `README.md`
- `build.sh`

**Implementação:**

1. **README:** atualizar para o fluxo real (intermediário NotebookLM↔Obsidian),
   os três backends, os tipos de entrada (PDF / YouTube / Áudio), o sistema
   de prompts com injeção de estrutura, o mapa de conhecimento, e o
   mini-player MPRIS. Remover o que estiver obsoleto.
2. **build.sh (Nuitka):**
   - **Remover** `--include-package=yt_dlp` (yt-dlp é subprocess CLI, não
     módulo importado — flag redundante que infla o binário).
   - Garantir `--include-package=pymupdf pymupdf4llm` (PyMuPDF importa como
     `pymupdf`, não `fitz`).
   - Adicionar runtime QML: `--include-qt-plugins=qml` e inclusão dos
     arquivos `.qml` no pacote.
   - Manter Nuitka travado em 4.1.2.

**Verificação:**
```bash
./build.sh
./<binário gerado>   # app abre standalone, QML renderiza, fluxo completo roda
```

**Checkpoint:** build standalone funcional com QML empacotado.

---

## Regras transversais (todas as fases)

- `pathlib.Path` apenas. Nunca `os.path`.
- Lógica de negócio nunca no QML — sempre em `backend.py` / `pipeline/` /
  `integrations/`.
- Tokens de design só em `Theme.qml`. Componentes referenciam, não hardcodam.
- UI nunca bloqueia. Operações pesadas em QThread.
- Erros ao usuário em PT-BR, com padrão: o quê + por quê + o que fazer.
- Sem features não solicitadas, sem refatoração fora do escopo da fase.
- Não adicionar dependência sem aprovação explícita.
- PySide6 sempre via pacman. Nuitka travado em 4.1.2.

---

## Contingências / verificar em casa

1. **SimpMusic MPRIS** (Fase 5): rodar `playerctl -l` com música tocando.
   Define se a Fase 5 segue por MPRIS ou por backend headless alternativo.
2. **Versão notebooklm-py** (Fase 2): conferir versão instalada vs pin no
   `requirements.txt` e corrigir o mismatch.
3. **Gemini API** (Fase 1): gerar API key no Google AI Studio. Free tier
   usa inputs para treino — decidir se aceitável para conteúdo de estudo.
4. **Modelo Ollama** (Fase 1): escolher um modelo bom para geração de notas
   (não coder). Confirmar que roda no hardware (16GB RAM, sem GPU dedicada).

---

## Ordem recomendada

Fase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7

Fundação (backends + reliability) primeiro, features (prompts + mapa) no meio,
integração (SimpMusic) e polimento visual depois, docs + build por último.
As fases 5 e 6 são relativamente independentes — podem ser reordenadas se
preferir ver o visual antes do áudio.

---

## Pendências registradas (revisão pós-Fase 7)

Itens identificados na revisão profunda e **adiados** por decisão explícita —
implementar quando houver janela, fora do escopo da revisão atual.

7. **Editar `gemini_model` no Settings** (`SettingsDialog.qml`, `backend.py`).
   Hoje o modelo do Gemini é carregado e salvo, mas não é editável na UI (só a
   chave de API e o modelo do Ollama aparecem). Expor um campo de texto análogo
   ao do Ollama, com default `gemini-flash-latest`.

8. **Clamp de `selectedPromptIndex` ao recarregar prompts** (`main.qml`).
   Após remover prompts, o índice selecionado pode ficar fora de faixa; hoje o
   `process()` valida e devolve "Erro: prompt não encontrado" (PT-BR,
   recuperável). Re-clampar o índice em `reloadPrompts`/mudança de
   `promptLabels` evita o erro.

9. **`config.py` com `Path.read_text/write_text`** (`config/config.py`).
   Trocar os `open(_CONFIG_PATH, ...)` por `Path.read_text`/`write_text` para
   consistência com o resto do repo (cosmético; não é violação da regra de
   `os.path`).

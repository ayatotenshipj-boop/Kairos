# CLAUDE.md — Kairos

App de estudo local para perfil TDAH+TEA.

Aceita PDF ou URL YouTube → processa via NotebookLM → salva nota no Obsidian + log em markdown.

---

## Ambiente

```text
OS: CachyOS / Arch, Hyprland
Python: 3.14.5
Shell: Zsh

Venv: .venv --system-site-packages
Raiz: ~/Documentos/Kairos
```

```bash
./run.sh
./build.sh
```

---

## Objetivo Principal

Manter o Kairos simples, responsivo e confiável.

Prioridades:

1. Não quebrar funcionalidades existentes.
2. Não travar a UI.
3. Resolver a tarefa com o menor número de alterações possível.
4. Consumir o mínimo de contexto necessário.
5. Preservar a arquitetura definida neste documento.

---

## REGRAS — Nunca Violar

### Dependências

* PySide6 nunca via pip.
* PySide6 vem do pacman (`extra/pyside6`).
* Venv sempre com `--system-site-packages`.

### Build

* Nuitka travado em 4.1.2.
* Não atualizar Nuitka sem solicitação explícita.

### Arquitetura

* Zero lógica de negócio em `ui/`.
* Zero UI em `pipeline/`.
* Separação estrita entre camadas.

### Caminhos

* Usar apenas `pathlib.Path`.
* Nunca usar `os.path`.
* Nunca usar caminhos hardcoded.

### UX

* UI nunca pode travar.
* Operações pesadas sempre em `QThread` ou `QRunnable`.
* Feedback visual obrigatório para ações > 1 segundo.
* Status sempre atualizado em tempo real.
* Uma ação visível por vez.

### Erros

* Mensagens em PT-BR.
* Nunca exibir stacktrace cru ao usuário.

### Estilo

* Toda estilização em `styles.qss`.
* Nunca usar `setStyleSheet()` inline.

---

## Context Economy

Objetivo: minimizar consumo de tokens.

Antes de qualquer alteração:

1. Identificar arquivos relevantes.
2. Ler apenas os arquivos necessários.
3. Nunca escanear o repositório inteiro sem necessidade explícita.
4. Nunca abrir arquivos não relacionados.
5. Parar a investigação assim que houver informação suficiente.
6. Reutilizar contexto já obtido na sessão.
7. Preferir leitura direcionada a exploração ampla.

Prioridade de contexto:

1. CLAUDE.md
2. Contexto da sessão
3. Arquivos específicos
4. Exploração adicional

---

## Modification Policy

Alterações devem ser cirúrgicas.

* Modificar o menor número possível de arquivos.
* Não realizar refatorações não solicitadas.
* Não reorganizar diretórios.
* Não mover arquivos.
* Não renomear arquivos.
* Não alterar APIs sem necessidade.
* Não introduzir dependências sem aprovação explícita.
* Não alterar comportamento existente sem justificativa.

Se um problema puder ser resolvido em um arquivo, preferir um arquivo.

---

## Simplicity First

Sempre preferir:

* Solução simples.
* Menor implementação possível.
* Menor superfície de mudança.

Evitar:

* Overengineering.
* Abstrações prematuras.
* Flexibilidade futura não solicitada.
* Código especulativo.

---

## Clarification Policy

Se houver ambiguidade:

* Não assumir.
* Perguntar.
* Não alterar arquitetura sem confirmação.
* Não remover funcionalidades sem confirmação.

---

## Stack

| Componente | Tecnologia                      |
| ---------- | ------------------------------- |
| GUI        | PySide6                         |
| Build      | Nuitka 4.1.2                    |
| NotebookLM | notebooklm-py 0.7.0             |
| PDF        | pymupdf4llm 0.0.17              |
| YouTube    | youtube-transcript-api + yt-dlp |
| Config     | config.json                     |
| Notas      | Obsidian                        |
| Música     | Simpmusic                       |

---

## Arquitetura

```text
kairos/
├── main.py
├── ui/
├── pipeline/
├── integrations/
└── config/
```

---

## Quick Responsibility Map

main.py

* Bootstrap
* QApplication
* MainWindow

ui/

* Interface gráfica
* Nenhuma lógica de negócio

pipeline/ingestor.py

* Identificação e roteamento

pipeline/pdf_extractor.py

* PDF → Markdown

pipeline/youtube_extractor.py

* Transcrições

pipeline/processor.py

* NotebookLM
* Fallback local

pipeline/writer.py

* Escrita Obsidian

pipeline/logger.py

* Study Log

integrations/notebooklm_client.py

* Comunicação NotebookLM

integrations/launcher.py

* Simpmusic

config/config.py

* Persistência

---

## Entry Points

Mudança de UI:

```text
ui/
```

Mudança NotebookLM:

```text
integrations/notebooklm_client.py
pipeline/processor.py
```

Mudança Obsidian:

```text
pipeline/writer.py
```

Fluxo principal:

```text
main.py
 → MainWindow
 → Pipeline
 → Integrations
```

---

## Pipeline

```text
PDF/URL
 → ingestor
 → extractor
 → processor
 → writer
 → logger
```

---

## Investigation Strategy

Ao corrigir bugs:

1. Formular hipótese.
2. Identificar arquivos envolvidos.
3. Ler apenas esses arquivos.
4. Validar hipótese.
5. Corrigir.
6. Encerrar investigação.

Evitar leituras em cascata.

---

## Validation

Antes de concluir:

* Verificar imports.
* Verificar regras deste documento.
* Confirmar que a UI permanece responsiva.
* Confirmar que nenhuma arquitetura foi violada.
* Confirmar mensagens em PT-BR.

---

## Performance Policy

Evitar:

* Processamento duplicado.
* Releituras desnecessárias.
* Loops redundantes.
* Operações síncronas pesadas.
* Bloqueios da thread principal.

Preferir:

* QThread
* QRunnable
* Lazy loading
* Cache local

---

## Never Do

* Nunca commitar API Keys.
* Nunca commitar credenciais.
* Nunca commitar arquivos pessoais.
* Nunca bloquear a UI.
* Nunca misturar UI com lógica de negócio.
* Nunca usar os.path.
* Nunca usar setStyleSheet inline.
* Nunca atualizar Nuitka sem solicitação.

---

## Errors Corrected

Erros conhecidos e já corrigidos:

* PySide6 nunca via pip.
* Não usar os.path.
* Não usar setStyleSheet inline.
* Nuitka permanece em 4.1.2.
* UI nunca pode bloquear.

Adicionar novas ocorrências conforme forem identificadas.

---

## Riscos Conhecidos

NotebookLM:

* Executar atualização do pacote se necessário.

Sessão NotebookLM:

* Reautenticar via terminal.

YouTube:

* Fallback automático para yt-dlp.

Build:

* Confirmar Nuitka 4.1.2.

---

## Definition of Done

Uma tarefa só está concluída quando:

* Código consistente.
* Arquitetura preservada.
* UI responsiva.
* Nenhuma regra deste documento foi violada.
* Não há regressão evidente.
* Mensagens continuam em PT-BR.
* Alteração atende exatamente ao solicitado.

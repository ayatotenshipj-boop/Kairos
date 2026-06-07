# CLAUDE.md — Kairos

App de estudo local para perfil TDAH+TEA. Aceita PDF ou URL YouTube → processa via NotebookLM → salva nota no Obsidian + log em markdown.

---

## Ambiente

```
OS: CachyOS / Arch, Hyprland | Python: 3.14.5 | Shell: Zsh
Venv: .venv --system-site-packages | Raiz: ~/Documentos/Kairos
```

```bash
./run.sh        # roda o app
./build.sh      # gera dist/kairos (binário standalone)
```

---

## REGRAS — nunca violar

1. **PySide6 nunca via pip** — vem do pacman (`extra/pyside6`). pip não tem wheel para Python 3.14. Venv sempre com `--system-site-packages`.
2. **Nuitka travado em 4.1.2** — histórico de regressões com PySide6. Não atualizar.
3. **UI nunca trava** — todo processamento pesado em `QThread`/`QRunnable`. Nunca bloquear thread principal.
4. **Separação estrita** — zero lógica de negócio em `ui/`, zero UI em `pipeline/`.
5. **Sem `os.path`** — usar `pathlib.Path`. Sem `pathlib2`. Sem caminhos hardcoded.
6. **Erros em PT-BR** — nunca expor stacktrace cru ao usuário.
7. **Estilo só em `styles.qss`** — nunca `setStyleSheet()` inline em widget individual.

---

## Stack

| Componente | Tecnologia |
|---|---|
| GUI | PySide6 via pacman |
| Build | Nuitka 4.1.2 |
| NotebookLM | notebooklm-py 0.7.0 (API não-oficial) |
| PDF | pymupdf4llm 0.0.17 |
| YouTube | youtube-transcript-api 1.2.4 + yt-dlp 2026.3.17 |
| Config | `~/.config/kairos/config.json` |
| Notas | Obsidian vault (.md direto, sem plugin) |
| Música | Simpmusic via subprocess |

---

## Arquitetura

```
kairos/
├── main.py                  # QApplication + MainWindow only
├── ui/                      # Zero lógica de negócio
│   ├── main_window.py
│   ├── sidebar.py
│   ├── drop_zone.py
│   ├── prompt_selector.py
│   ├── progress_bar.py
│   └── styles.qss           # toda estilização aqui
├── pipeline/                # Zero UI
│   ├── ingestor.py          # identifica tipo, roteia
│   ├── pdf_extractor.py     # pymupdf4llm → markdown
│   ├── youtube_extractor.py # transcript-api → fallback yt-dlp
│   ├── processor.py         # notebooklm-py → fallback local
│   ├── writer.py            # salva .md no vault
│   └── logger.py            # append study-log.md
├── integrations/
│   ├── notebooklm_client.py
│   └── launcher.py          # Simpmusic subprocess
└── config/
    ├── config.py            # lê/escreve config.json
    └── defaults.py          # DEFAULT_CONFIG + prompts padrão
```

---

## Pipeline

```
PDF/URL → ingestor → pdf_extractor | youtube_extractor
        → processor (notebooklm → fallback: salva bruto + #pendente-notebooklm)
        → writer (nota .md no vault)
        → logger (append study-log.md)
```

---

## Tema visual

Minimalista escuro, monoespaçado. Sem gradientes, sem sombras excessivas.

```
#0f0f0f  fundo principal   | #0a0a0a  sidebar
#1a1a1a  superfícies        | #1e1e1e / #333333  bordas
#e0e0e0  texto              | #888888  secundário | #555555  desabilitado
Font: "JetBrains Mono", 13px
```

---

## Riscos conhecidos

- **notebooklm-py quebrou**: `pip install --upgrade notebooklm-py`. Fallback já implementado em `processor.py`.
- **Sessão expirou**: `notebooklm login` no terminal.
- **YouTube falhou**: fallback automático para yt-dlp já em `youtube_extractor.py`.
- **Build Nuitka falhou**: confirmar `python -m nuitka --version` == 4.1.2.

---

## UX (TDAH+TEA)

- Feedback visual obrigatório em qualquer ação > 1s
- App abre pronto para uso, sem setup inicial obrigatório
- Uma ação visível por vez
- Status label atualizado em tempo real
- Erros sempre em PT-BR, nunca stacktrace
# Keepalive da sessão do NotebookLM (systemd user timer)

A sessão do NotebookLM depende de cookies do Google. O **CSRF** é renovado
automaticamente pelo cliente, mas o **cookie base** (`__Secure-1PSIDTS`) estala
("stale out") se o perfil ficar ocioso por muito tempo — e aí o processamento
cai para o fallback local ("salvo localmente").

`notebooklm auth refresh` faz um *keepalive poke* que rotaciona esse cookie e
persiste o `storage_state.json`. A própria CLI recomenda cadência de **15-20
min**. Agendamos isso com um timer systemd de usuário (não embutido no app).

> **Diagnóstico rápido:** `notebooklm auth check --test` (faz requisição real e
> valida o token). Se falhar, é cookie base expirado.

---

## 1. Service (oneshot)

`~/.config/systemd/user/kairos-notebooklm.service`

```ini
[Unit]
Description=Kairos — keepalive da sessão do NotebookLM

[Service]
Type=oneshot
# Caminho absoluto da CLI dentro do venv do Kairos — ajuste se o seu repo
# estiver em outro lugar.
ExecStart=/home/andrey/Documentos/Kairos/.venv/bin/notebooklm auth refresh
```

## 2. Timer

`~/.config/systemd/user/kairos-notebooklm.timer`

```ini
[Unit]
Description=Kairos — agenda o keepalive do NotebookLM

[Timer]
OnBootSec=5min
OnUnitActiveSec=20min
Persistent=true

[Install]
WantedBy=timers.target
```

## 3. Ativar

```bash
systemctl --user daemon-reload
systemctl --user enable --now kairos-notebooklm.timer

# conferir
systemctl --user list-timers kairos-notebooklm.timer
journalctl --user -u kairos-notebooklm.service -n 20 --no-pager
```

---

## Recuperação manual (cookie base já expirou de vez)

O timer mantém viva uma sessão **válida**; ele não ressuscita uma já morta. Se
`notebooklm auth check --test` falhar mesmo com o timer ativo, re-extraia os
cookies do navegador (com o Chrome logado na conta certa):

```bash
notebooklm auth refresh --browser-cookies chrome
```

Outros navegadores: `firefox`, `brave`, `edge`. Para um perfil específico do
Chrome: `--browser-cookies 'chrome::<perfil>'`.

> O `--browser-cookies` é recuperação manual — **não** o use no timer (é mais
> pesado e pressupõe navegador aberto/logado). O timer usa `auth refresh` puro.

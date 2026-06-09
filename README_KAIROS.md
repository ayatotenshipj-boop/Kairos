# Kairos — Guia de Design de Interface

## Visão Geral

Kairos é uma camada de integração entre NotebookLM e Obsidian.

Não substitui nenhuma das ferramentas. Cria uma experiência de aprendizagem
guiada, organizada e conectada.

**Fluxo principal:**
```
Usuário → Kairos → NotebookLM → Kairos → Obsidian
```

---

## Missão

Transformar informação dispersa em conhecimento conectado, organizado e
reutilizável, reduzindo a carga cognitiva necessária para aprender.

O usuário deve responder apenas:
1. O que quero aprender?
2. Como quero aprender isso?

Todo o restante acontece automaticamente.

---

## O Que o Kairos É e Não É

**É:**
- Camada de integração entre NotebookLM e Obsidian
- Organizador automático de conhecimento
- Sistema de aprendizagem guiada
- Biblioteca de prompts estruturados

**Não é:**
- IDE
- Dashboard corporativo
- Ferramenta de produtividade genérica
- Sistema de gamificação
- Substituto do Obsidian ou do NotebookLM

---

## Regra Máxima

> Toda decisão deve responder:
> "Isso ajuda o usuário a aprender com menos esforço cognitivo?"
>
> Se a resposta for não, a funcionalidade deve ser reconsiderada.

---

## Princípios de Interface

### Uma ação primária por contexto

Cada tela tem exatamente um elemento que compete por atenção.
Nunca dois botões com o mesmo peso visual. Nunca duas áreas interativas
disputando foco. O usuário nunca deve hesitar sobre o que fazer.

### Hierarquia visual obrigatória (do mais para o menos chamativo)

1. Zona de entrada (DropZone) — elemento principal do painel
2. Botão de ação primária (Processar)
3. Seletor de prompt
4. Sidebar e elementos secundários

### Espaçamento generoso

Elementos próximos demais aumentam carga cognitiva.
Usar espaçamento mínimo de 16px entre grupos, 8px entre itens relacionados.
Área clicável mínima de 44×44px em qualquer elemento interativo.

### Consistência absoluta

O mesmo elemento sempre se comporta da mesma forma.
Padrões familiares reduzem carga de memória.
Hover, active, disabled têm comportamento previsível e idêntico
em todos os componentes.

---

## Design para Neurodivergentes (TDAH + TEA)

### Carga cognitiva

- Máximo de 3 ações visíveis por tela simultaneamente
- Nenhuma decisão implícita — tudo que requer ação do usuário deve
  ser explícito e rotulado
- Navegação sem profundidade: tudo acessível em no máximo 2 cliques
- Sem modais empilhados

### Foco e atenção

- Elemento com foco deve ter contorno visível e inconfundível
- Quando uma operação começa, o foco se move para o indicador de progresso
- Depois de concluir, o foco retorna à DropZone (pronto para próxima entrada)
- Sem notificações que interrompem operações em andamento

### Feedback imediato

Todo estado tem confirmação visual, icônica e textual — nunca só cor.
O usuário não deve adivinhar se algo funcionou.

| Evento | Feedback |
|---|---|
| Arquivo aceito | Ícone ✓ + nome do arquivo + borda ativa |
| Arquivo inválido | Ícone ✗ + mensagem PT-BR + reset em 2s |
| Pipeline iniciado | Tracker de progresso aparece, botão desabilitado |
| Fase concluída | Fase acende permanentemente no tracker |
| Nota salva | Mensagem de sucesso + link clicável para a nota |
| Erro | Mensagem PT-BR clara: o que aconteceu + o que fazer |
| Modo local (fallback) | Aviso amarelo: "Salvo localmente — NotebookLM indisponível" |

### Recuperação de erros

Mensagens de erro seguem sempre o padrão:
**O que aconteceu** + **Por quê** + **O que fazer agora**

Exemplos:
- "Vault do Obsidian não configurado. Configure nas Configurações."
- "NotebookLM indisponível. Nota salva localmente."
- "Arquivo inválido. Selecione um PDF."

Nunca exibir stacktrace ou mensagem técnica ao usuário.

---

## Animações

### Princípio

Animações servem ao usuário, não ao design.
Animações de estado (hover, active, progresso) reduzem carga cognitiva
ao comunicar mudança. Animações decorativas aumentam carga cognitiva
e devem ser evitadas.

### O que animar

- Transições de estado do DropZone (idle → accepted → invalid)
- Progresso do pipeline (fases acendendo sequencialmente)
- Hover em elementos interativos (resposta perceptível, não brusca)
- Reveal da janela no load (escalonado, máximo 300ms total)

### O que não animar

- Conteúdo estático (labels, textos, ícones informativos)
- Elementos fora do foco do usuário
- Qualquer coisa que se repita indefinidamente sem interação

### Controle de movimento

A interface deve respeitar `prefers-reduced-motion`.
Com essa preferência ativa: transições instantâneas, sem pulso na DropZone,
sem reveal escalonado.

---

## Visibilidade do Pipeline

O pipeline é o coração do Kairos. O usuário precisa saber
exatamente o que está acontecendo em tempo real.

**Tracker de 4 fases:**
```
[ Extração ] → [ Processamento ] → [ Escrita ] → [ Concluído ]
```

Comportamento por estado:
- **Aguardando:** fase apagada, sem destaque
- **Ativa:** indicador de progresso animado + label descritivo + tempo decorrido
- **Concluída:** ícone de sucesso permanente
- **Erro:** ícone de erro + mensagem PT-BR inline na fase

O tracker substitui o status label único.
Nunca esconder o tracker durante o processamento.
Após conclusão, o tracker permanece visível até o usuário iniciar
uma nova entrada.

---

## Empty State e Onboarding

A primeira tela que o usuário vê deve comunicar imediatamente
o que fazer, sem necessidade de leitura de documentação.

**Estado inicial (sem nada carregado):**
- DropZone grande, convidativa, com instrução clara
- Botão Processar desabilitado e visivelmente inativo
- Prompt selecionado por padrão (não vazio)
- Nenhuma mensagem de erro ou aviso sem contexto

**Primeira configuração (vault não configurado):**
- Aviso discreto na sidebar: "Configure o Obsidian para salvar notas"
- Link direto para Configurações
- Não bloquear o uso — apenas avisar

---

## Tipografia

**Typeface base:** JetBrains Mono — não substituir.
Comunica precisão e caráter técnico sem parecer corporativo.

**Escala mínima:**
- Títulos de seção: 13px, letter-spacing 2–4px, uppercase
- Corpo: 13px, line-height 1.6
- Labels secundários: 11px, color secundário
- Mensagens de status: 12px

**Contraste mínimo:**
- Texto primário sobre fundo: 7:1 (WCAG AAA)
- Texto secundário sobre fundo: 4.5:1 (WCAG AA)
- Nunca usar cor como único diferenciador de estado

---

## Prompts Estruturados

Cada prompt tem:
- Nome curto (até 3 palavras)
- Descrição pedagógica em uma linha
- Texto completo editável pelo usuário

Prompts padrão:
- **Explique como criança** — Simplifica ao máximo, sem jargão
- **Entenda profundamente** — Explora causas, consequências e contexto
- **Aprenda na prática** — Exemplos, exercícios e aplicações reais
- **Conecte conceitos** — Relaciona com o que você já sabe
- **Resumo para revisão** — Síntese densa para revisitar depois

---

## Player de Música (Simpmusic)

Discreto e opcional.

- Sempre no rodapé da sidebar, nunca no painel principal
- Controles mínimos: play/pause + volume
- Não competir visualmente com nada
- Inicializar silenciosamente

---

## Personalização

Opções disponíveis via Settings:
- Tema (claro / escuro / sistema)
- Paleta de acento (cor principal da interface)
- Reduzir movimento (desativa animações não essenciais)
- Tipografia (tamanho base)
- Vault do Obsidian (caminho)
- Prompts (CRUD completo)

Padrões sensatos para todos os campos.
Nenhuma configuração obrigatória para o primeiro uso,
exceto o vault do Obsidian (avisado, não bloqueante).

---

## Critérios de Sucesso

- O usuário entende o que fazer sem ler nada
- O pipeline comunica cada fase visualmente
- Erros têm ação de recuperação clara
- A UI permanece responsiva durante todo o processamento
- Configurações não são necessárias para o primeiro uso
- A personalização não quebra a hierarquia visual

---

## Confiabilidade da sessão do NotebookLM

O NotebookLM depende de cookies de sessão do Google que expiram. O Kairos lida
com isso em duas frentes:

1. **Verificação no startup.** Quando o backend ativo é o NotebookLM, o Kairos
   roda uma checagem local de sessão ao abrir (sem rede, não bloqueia a UI). Se
   a sessão caiu, exibe um aviso PT-BR na linha de status:
   *"Sessão do NotebookLM expirada — rode no terminal: notebooklm auth refresh"*.
   O processamento nunca trava: se o NotebookLM estiver indisponível, o pipeline
   cai automaticamente no fallback local.

2. **Keepalive via systemd (opcional, recomendado).** Para evitar que a sessão
   estale enquanto ociosa, instale o timer de usuário que renova os cookies a
   cada ~20 min:

   ```bash
   cp systemd/kairos-notebooklm.* ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now kairos-notebooklm.timer
   # status:  systemctl --user list-timers kairos-notebooklm.timer
   ```

   O `ExecStart` do `.service` usa caminho absoluto para o venv
   (`%h/Documentos/Kairos/.venv/bin/notebooklm`); ajuste se o repositório
   estiver em outro local. O Kairos **não** instala nem habilita esses units
   automaticamente — é uma ação consciente do usuário.

   Se a sessão cair completamente, reautentique:
   ```bash
   notebooklm login
   ```
import QtQuick

// Design tokens — instanciar localmente com: Theme { id: th; darkMode: backend.darkMode }
// Valores transcritos 1:1 dos blocos [data-theme="dark"] / [data-theme="light"]
// de docs/ui_reference.html. Não arredondar nem alterar os hex.
QtObject {
    // Modo claro/escuro — espelha data-theme do protótipo.
    // O estado real vive no backend (backend.darkMode); cada instância faz o bind.
    property bool darkMode: true

    // ── Backgrounds ────────────────────────────────────────────────────────
    readonly property color bgBase:     darkMode ? "#0c0c0e" : "#f4f1ea"  // --bg-base
    readonly property color bgSurface:  darkMode ? "#141418" : "#fdfbf7"  // --bg-surface
    readonly property color bgElevated: darkMode ? "#1c1c21" : "#ffffff"  // --bg-elevated
    readonly property color bgOverlay:  darkMode ? "#1c1c21" : "#ffffff"  // = elevated
    readonly property color bgInput:    darkMode ? "#1c1c21" : "#ffffff"  // campos usam --bg-elevated

    // ── Accent — Âmbar ─────────────────────────────────────────────────────
    readonly property color accentDefault: darkMode ? "#f2a03d" : "#cc7a14"  // --accent
    readonly property color accentHover:   darkMode ? "#f7b35e" : "#b06709"  // --accent-hover
    readonly property color accentActive:  darkMode ? "#f7b35e" : "#b06709"  // ref. não tem 'active'
    // --accent-dim
    readonly property color accentSubtle:  darkMode ? Qt.rgba(242/255, 160/255, 61/255, 0.12)
                                                     : Qt.rgba(204/255, 122/255, 20/255, 0.10)
    // --accent-glow
    readonly property color accentGlow:    darkMode ? Qt.rgba(242/255, 160/255, 61/255, 0.22)
                                                     : Qt.rgba(204/255, 122/255, 20/255, 0.18)
    // foco/borda de bloco usam --accent cheio no protótipo
    readonly property color accentMuted:   darkMode ? "#f2a03d" : "#cc7a14"

    // ── Text ───────────────────────────────────────────────────────────────
    readonly property color textPrimary:   darkMode ? "#ece9e3" : "#2a2823"  // --text-1
    readonly property color textSecondary: darkMode ? "#8c8c94" : "#6b6760"  // --text-2
    readonly property color textTertiary:  darkMode ? "#56565d" : "#9b968c"  // --text-3
    readonly property color textDisabled:  darkMode ? "#56565d" : "#9b968c"  // = --text-3
    readonly property color textOnAccent:  darkMode ? "#0c0c0e" : "#fffdf9"  // --on-accent

    // ── Borders ────────────────────────────────────────────────────────────
    // O protótipo só tem dois níveis: --border e --border-strong.
    readonly property color borderSubtle:  darkMode ? "#26262c" : "#e4ded2"  // --border
    readonly property color borderDefault: darkMode ? "#26262c" : "#e4ded2"  // --border
    readonly property color borderStrong:  darkMode ? "#34343c" : "#d0c8b8"  // --border-strong
    readonly property color borderFocus:   darkMode ? "#f2a03d" : "#cc7a14"  // foco = --accent

    // ── Estados semânticos (Fg / Bg-dim / Glow) ────────────────────────────
    // 'running' = âmbar (o protótipo não usa azul; o nó ativo e o status running
    // usam --accent).
    readonly property color stateIdleFg:      darkMode ? "#56565d" : "#9b968c"
    readonly property color stateIdleBg:      bgSurface
    readonly property color stateRunningFg:   accentDefault
    readonly property color stateRunningBg:   accentSubtle
    readonly property color stateRunningGlow: accentGlow

    readonly property color stateSuccessFg:   darkMode ? "#4fd1a0" : "#1f9e72"  // --success
    readonly property color stateSuccessBg:   darkMode ? Qt.rgba(79/255, 209/255, 160/255, 0.12)
                                                        : Qt.rgba(31/255, 158/255, 114/255, 0.10)
    readonly property color stateSuccessGlow: stateSuccessBg

    readonly property color stateErrorFg:     darkMode ? "#f06a5a" : "#d4503e"  // --error
    readonly property color stateErrorBg:     darkMode ? Qt.rgba(240/255, 106/255, 90/255, 0.12)
                                                        : Qt.rgba(212/255, 80/255, 62/255, 0.10)
    readonly property color stateErrorGlow:   stateErrorBg

    readonly property color stateWarningFg:   darkMode ? "#f2c14e" : "#b8870f"  // --warning
    readonly property color stateWarningBg:   darkMode ? Qt.rgba(242/255, 193/255, 78/255, 0.12)
                                                        : Qt.rgba(184/255, 135/255, 15/255, 0.10)
    readonly property color stateWarningGlow: stateWarningBg

    // ── Tipografia — JetBrains Mono ────────────────────────────────────────
    // Protótipo importa 'JetBrains Mono'; no ambiente só há a variante Nerd Font
    // (mesmo tipo, superset). Usar a instalada para não cair em monospace genérico.
    readonly property string fontFamily: "JetBrainsMono Nerd Font"

    // Escala extraída do protótipo (px). pixelSize é inteiro no QML: os .5
    // da referência caem no inteiro mais próximo (limitação da plataforma).
    readonly property int sizeDisplay:  24  // .main-header .question
    readonly property int sizeH1:        18  // wordmark KAIROS / modal h2 ~16
    readonly property int sizeH2:        16  // .modal h2
    readonly property int sizeH3:        15  // .dz-title
    readonly property int sizeButton:    14  // .process-btn (13.5)
    readonly property int sizeBody:      13  // corpo / inputs (12.5–13)
    readonly property int sizeSmall:     12  // .status / .hint / .bm-note
    readonly property int sizeCaption:   11  // .conn-row / .step-label / labels
    readonly property int sizeMicro:     10  // .prompt .desc / .tagline (10.5)
    readonly property int sizeLabel:     10  // .section-label uppercase (9.5)
    readonly property int sizeTag:        9  // .step-sub (9) / .bm-tag (8.5)

    readonly property int weightExtra:    800  // wordmark
    readonly property int weightBold:     700
    readonly property int weightSemiBold: 600
    readonly property int weightMedium:   500
    readonly property int weightRegular:  400

    // ── Spacing (base 4px) ─────────────────────────────────────────────────
    readonly property int spacingXxs: 2
    readonly property int spacingXs:  4
    readonly property int spacingSm:  8
    readonly property int spacingMd:  12
    readonly property int spacingLg:  16
    readonly property int spacingXl:  24
    readonly property int spacing2xl: 32
    readonly property int spacing3xl: 48

    // ── Border radius (valores do protótipo) ───────────────────────────────
    readonly property int radiusSharp: 9   // inputs / pequenos (era square; ref. é arredondado)
    readonly property int radiusSm:    9
    readonly property int radiusMd:    13  // botão primário
    readonly property int radiusLg:    16  // cards / modal
    readonly property int radiusPill:  20  // pílulas (dz-type)

    // ── Durações de animação (ms — do protótipo) ───────────────────────────
    readonly property int durationFast:   180  // transições .18s
    readonly property int durationNormal: 300  // .3s
    readonly property int durationSlow:   500  // revealUp .5s
    readonly property int durationPulse:  1500 // nodepulse 1.5s
    readonly property int durationBreathe: 4000 // breathe 4s
    readonly property int durationBeat:   3200 // heartbeat 3.2s
    readonly property int durationDraw:    700 // drawLine .7s

    // ── Escalas de interação (micro-interações) ────────────────────────────
    readonly property real scalePress: 0.99   // .process-btn:active
    readonly property real scaleHover: 1.005  // .dropzone.dragover
    readonly property real scalePop:   1.25   // .bm-node:hover .bm-dot

    // Entrada escalonada (ms entre elementos)
    readonly property int staggerStep: 70
}

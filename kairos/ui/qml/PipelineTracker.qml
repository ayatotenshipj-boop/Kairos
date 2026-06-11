import QtQuick
import "."

// Réplica de .pipeline: card com head (label + elapsed) e 4 nós com ícones.
// Os 4 nós visuais (Extração → NotebookLM → Síntese → Obsidian) mapeiam para as
// 3 fases reais do backend: 'processing' acende NotebookLM e Síntese juntos.
Item {
    id: root

    implicitHeight: card.implicitHeight

    Theme { id: th; darkMode: backend.darkMode }

    readonly property bool isRunning:
        ["extracting", "processing", "writing"].indexOf(backend.pipelinePhase) !== -1

    readonly property bool hasError: backend.pipelinePhase.indexOf("error") === 0

    readonly property var _labels: ["Extração", backend.backendLabel, "Síntese", "Obsidian"]
    readonly property var _subs:   ["texto", "pesquisa", "nota", "memória"]
    readonly property var _icons: [
        "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6",
        "M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0M12 7v5l3 2",
        "M12 2v4M12 18v4M2 12h4M18 12h4M16 12a4 4 0 1 0 -8 0a4 4 0 1 0 8 0",
        "M4 4h16v16H4zM9 9h6v6H9z"
    ]

    // "inactive" | "active" | "done" | "error" para o nó idx (0–3)
    function stepStatus(idx) {
        let ph = backend.pipelinePhase
        if (ph === "done") return "done"

        if (ph === "error_extraction") return idx === 0 ? "error" : "inactive"
        if (ph === "error_processing") {
            if (idx === 0) return "done"
            if (idx === 1 || idx === 2) return "error"
            return "inactive"
        }
        if (ph === "error_writing") return idx < 3 ? "done" : "error"

        if (ph === "extracting") return idx === 0 ? "active" : "inactive"
        if (ph === "processing") {
            if (idx === 0) return "done"
            if (idx === 1 || idx === 2) return "active"
            return "inactive"
        }
        if (ph === "writing") return idx < 3 ? "done" : "active"

        return "inactive"  // idle
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: th.radiusLg
        color: th.bgSurface
        border.width: 1
        border.color: th.borderSubtle
        implicitHeight: cardCol.implicitHeight + 2 * th.spacingXl

        Column {
            id: cardCol
            anchors.fill: parent
            anchors.margins: th.spacingXl
            spacing: th.spacingXl

            // ── Head: label + elapsed ──────────────────────────────────────
            Item {
                width: parent.width
                height: headLabel.implicitHeight

                Text {
                    id: headLabel
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: "PIPELINE"
                    color: th.textTertiary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeLabel
                    font.weight: th.weightSemiBold
                    font.letterSpacing: 2.5
                }
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    visible: root.isRunning || root.hasError || backend.pipelinePhase === "done"
                    text: backend.progress + "%"
                    color: root.hasError ? th.stateErrorFg : th.accentDefault
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeCaption
                }
            }

            // ── Barra de progresso (% das 4 fases) ─────────────────────────
            Rectangle {
                width: parent.width
                height: 4
                radius: 2
                color: th.bgInput

                Rectangle {
                    height: parent.height
                    radius: parent.radius
                    width: parent.width * Math.max(0, Math.min(100, backend.progress)) / 100
                    color: root.hasError ? th.stateErrorFg : th.accentDefault
                    Behavior on width {
                        enabled: !backend.reduceMotion
                        NumberAnimation { duration: th.durationNormal; easing.type: Easing.OutCubic }
                    }
                    Behavior on color {
                        enabled: !backend.reduceMotion
                        ColorAnimation { duration: th.durationFast }
                    }
                }
            }

            // ── Steps ──────────────────────────────────────────────────────
            Item {
                id: steps
                width: parent.width
                height: 72
                property real cellW: width / 4

                // Connectors (atrás dos nós)
                Repeater {
                    model: 3
                    delegate: Rectangle {
                        readonly property int k: index
                        x: steps.cellW * (k + 0.5)
                        y: 18
                        width: steps.cellW
                        height: 2
                        color: {
                            let ps = root.stepStatus(k)
                            return (ps === "done") ? th.stateSuccessFg : th.borderStrong
                        }
                        Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                    }
                }

                // Nós + label + sub
                Repeater {
                    model: 4
                    delegate: Column {
                        readonly property int idx: index
                        readonly property string ss: root.stepStatus(idx)
                        x: steps.cellW * idx
                        width: steps.cellW
                        spacing: th.spacingSm

                        onSsChanged: if (ss === "done" && !backend.reduceMotion) donePop.restart()

                        // Círculo 38px com pulse ring
                        Item {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 38; height: 38

                            // Pulse ring (nodepulse) — só no ativo
                            Rectangle {
                                id: pulseRing
                                anchors.centerIn: parent
                                width: 46; height: 46; radius: 23
                                color: "transparent"
                                border.color: th.accentDefault
                                border.width: 1
                                opacity: 0
                                SequentialAnimation on opacity {
                                    running: ss === "active" && !backend.reduceMotion
                                    loops: Animation.Infinite
                                    NumberAnimation { to: 0.5; duration: th.durationPulse / 2; easing.type: Easing.InOutSine }
                                    NumberAnimation { to: 0;   duration: th.durationPulse / 2; easing.type: Easing.InOutSine }
                                    onStopped: pulseRing.opacity = 0
                                }
                            }

                            // Pulse de erro (nodepulse vermelho) — só no estado de erro
                            Rectangle {
                                id: errorRing
                                anchors.centerIn: parent
                                width: 46; height: 46; radius: 23
                                color: "transparent"
                                border.color: th.stateErrorFg
                                border.width: 1
                                opacity: 0
                                SequentialAnimation on opacity {
                                    running: ss === "error" && !backend.reduceMotion
                                    loops: Animation.Infinite
                                    NumberAnimation { to: 0.6; duration: th.durationPulse / 2; easing.type: Easing.InOutSine }
                                    NumberAnimation { to: 0;   duration: th.durationPulse / 2; easing.type: Easing.InOutSine }
                                    onStopped: errorRing.opacity = 0
                                }
                            }

                            Rectangle {
                                id: nodeCircle
                                anchors.fill: parent
                                radius: 19
                                transformOrigin: Item.Center
                                color: {
                                    if (ss === "active") return th.accentSubtle
                                    if (ss === "done")   return th.stateSuccessFg
                                    if (ss === "error")  return th.stateErrorBg
                                    return th.bgElevated
                                }
                                border.width: 2
                                border.color: {
                                    if (ss === "active") return th.accentDefault
                                    if (ss === "done")   return th.stateSuccessFg
                                    if (ss === "error")  return th.stateErrorFg
                                    return th.borderStrong
                                }
                                Behavior on color        { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                                Behavior on border.color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }

                                SequentialAnimation {
                                    id: donePop
                                    NumberAnimation { target: nodeCircle; property: "scale"; to: th.scalePop; duration: th.durationFast; easing.type: Easing.OutCubic }
                                    NumberAnimation { target: nodeCircle; property: "scale"; to: 1.0; duration: th.durationNormal; easing.type: Easing.OutBack }
                                }

                                IconSvg {
                                    anchors.centerIn: parent
                                    width: 17; height: 17
                                    d: root._icons[idx]
                                    strokeWidth: 2
                                    stroke: {
                                        if (ss === "active") return th.accentDefault
                                        if (ss === "done")   return th.textOnAccent
                                        if (ss === "error")  return th.stateErrorFg
                                        return th.textTertiary
                                    }
                                }
                            }
                        }

                        // Label
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root._labels[idx]
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeCaption
                            font.weight: th.weightMedium
                            color: {
                                if (ss === "active") return th.accentDefault
                                if (ss === "done")   return th.textSecondary
                                if (ss === "error")  return th.stateErrorFg
                                return th.textTertiary
                            }
                            Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                        }

                        // Sub — visível só no ativo (como na referência)
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root._subs[idx]
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeTag
                            color: th.accentDefault
                            opacity: ss === "active" ? 1 : 0
                            Behavior on opacity { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationNormal } }
                        }
                    }
                }
            }
        }
    }
}

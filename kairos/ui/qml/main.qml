import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

ApplicationWindow {
    id: root

    title: "Kairos"
    width: 1040
    height: 680
    minimumWidth: 880
    minimumHeight: 540
    visible: true

    // Índice do prompt selecionado na sidebar (compartilhado com o botão Processar)
    property int selectedPromptIndex: 0

    opacity: 0
    Component.onCompleted: backend.reduceMotion ? root.opacity = 1 : revealAnim.start()

    NumberAnimation {
        id: revealAnim
        target: root
        property: "opacity"
        to: 1
        duration: 400
        easing.type: Easing.OutCubic
    }

    background: Rectangle { color: th.bgBase }

    Theme { id: th; darkMode: backend.darkMode }

    // ── Layout principal ───────────────────────────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ── Sidebar ────────────────────────────────────────────────────────
        Rectangle {
            Layout.preferredWidth: 280
            Layout.fillHeight: true
            color: th.bgSurface

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: th.borderSubtle
            }

            ColumnLayout {
                id: sidebarCol
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                anchors.topMargin: 24
                anchors.bottomMargin: 16
                spacing: th.spacingLg

                opacity: 0
                Component.onCompleted: backend.reduceMotion ? sidebarCol.opacity = 1 : sidebarReveal.start()
                NumberAnimation { id: sidebarReveal; target: sidebarCol; property: "opacity"; to: 1; duration: th.durationNormal; easing.type: Easing.OutCubic }

                // ── Wordmark: dot pulsante + KAIROS ────────────────────────
                RowLayout {
                    spacing: th.spacingSm

                    Rectangle {
                        id: pulseDot
                        width: 9; height: 9; radius: 4.5
                        color: th.accentDefault
                        transformOrigin: Item.Center

                        SequentialAnimation on scale {
                            running: !backend.reduceMotion
                            loops: Animation.Infinite
                            NumberAnimation { to: 1.25; duration: th.durationBeat / 2; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0;  duration: th.durationBeat / 2; easing.type: Easing.InOutSine }
                        }
                        SequentialAnimation on opacity {
                            running: !backend.reduceMotion
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.7; duration: th.durationBeat / 2; easing.type: Easing.InOutSine }
                            NumberAnimation { to: 1.0; duration: th.durationBeat / 2; easing.type: Easing.InOutSine }
                        }
                    }

                    Text {
                        text: "KAIROS"
                        color: th.textPrimary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeH1
                        font.letterSpacing: 7
                        font.weight: th.weightExtra
                    }
                }

                Text {
                    text: "o momento de aprender"
                    color: th.textTertiary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeMicro
                    font.letterSpacing: 1
                    Layout.leftMargin: 19
                    Layout.topMargin: -th.spacingSm
                }

                // ── Bloco de conexões (NotebookLM ⇄ Obsidian) ──────────────
                Rectangle {
                    Layout.fillWidth: true
                    radius: 10
                    color: th.bgElevated
                    border.width: 1
                    border.color: th.borderSubtle
                    implicitHeight: connCol.implicitHeight + 2 * th.spacingMd

                    Column {
                        id: connCol
                        anchors.fill: parent
                        anchors.margins: th.spacingMd
                        spacing: th.spacingSm

                        component ConnRow: Item {
                            width: connCol.width
                            height: 16
                            property string icon: ""
                            property string label: ""
                            property string state: ""
                            Row {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: th.spacingSm
                                IconSvg {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 14; height: 14
                                    d: icon; stroke: th.textSecondary; strokeWidth: 2
                                    opacity: 0.7
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: label
                                    color: th.textSecondary
                                    font.family: th.fontFamily
                                    font.pixelSize: th.sizeCaption
                                }
                            }
                            Row {
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: th.spacingXs
                                Rectangle {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 6; height: 6; radius: 3
                                    color: th.stateSuccessFg
                                }
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: state
                                    color: th.stateSuccessFg
                                    font.family: th.fontFamily
                                    font.pixelSize: th.sizeMicro
                                }
                            }
                        }

                        ConnRow {
                            icon: "M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0M12 6v6l4 2"
                            label: "NotebookLM"; state: "pesquisa"
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "↑ síntese ↓"
                            color: th.textTertiary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeTag
                            font.letterSpacing: 1
                        }
                        ConnRow {
                            icon: "M4 4h16v16H4zM9 9h6v6H9z"
                            label: "Obsidian"; state: "memória"
                        }
                    }
                }

                // ── "Como aprender" — seletor de prompt ────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: th.spacingSm

                    Item {
                        Layout.fillWidth: true
                        implicitHeight: comoLabel.implicitHeight

                        Text {
                            id: comoLabel
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: "COMO APRENDER"
                            color: th.textTertiary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeLabel
                            font.weight: th.weightSemiBold
                            font.letterSpacing: 2.5
                        }
                        Text {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: "＋ Novo"
                            color: newPromptArea.containsMouse ? th.accentHover : th.accentDefault
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeLabel
                            font.letterSpacing: 1
                            MouseArea {
                                id: newPromptArea
                                anchors.fill: parent
                                anchors.margins: -4
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: settingsDlg.open()
                            }
                        }
                    }

                    Column {
                        id: promptCol
                        Layout.fillWidth: true
                        spacing: th.spacingXs

                        Repeater {
                            model: backend.promptLabels
                            delegate: Rectangle {
                                width: promptCol.width
                                implicitHeight: 38
                                radius: th.radiusSm
                                readonly property bool active: root.selectedPromptIndex === index
                                color: active ? th.accentSubtle
                                     : promptItemArea.containsMouse ? th.bgElevated : "transparent"
                                border.width: 1
                                border.color: active ? th.accentDefault : "transparent"
                                Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                                Row {
                                    anchors.left: parent.left
                                    anchors.leftMargin: th.spacingMd
                                    anchors.right: parent.right
                                    anchors.rightMargin: th.spacingSm
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: th.spacingMd

                                    // Radio
                                    Rectangle {
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 14; height: 14; radius: 7
                                        color: "transparent"
                                        border.width: 1.5
                                        border.color: active ? th.accentDefault : th.textTertiary
                                        Rectangle {
                                            anchors.centerIn: parent
                                            width: 7; height: 7; radius: 3.5
                                            color: th.accentDefault
                                            visible: active
                                        }
                                    }

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: parent.width - 14 - 13 - 2 * th.spacingMd
                                        text: modelData
                                        color: th.textPrimary
                                        font.family: th.fontFamily
                                        font.pixelSize: th.sizeSmall
                                        font.weight: th.weightMedium
                                        elide: Text.ElideRight
                                    }

                                    // Lápis (edição) — abre o gerenciamento de prompts
                                    IconSvg {
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: 13; height: 13
                                        d: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"
                                        stroke: pencilArea.containsMouse ? th.accentDefault : th.textTertiary
                                        strokeWidth: 2
                                        opacity: promptItemArea.containsMouse ? 1 : 0
                                        Behavior on opacity { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationFast } }
                                        MouseArea {
                                            id: pencilArea
                                            anchors.fill: parent
                                            anchors.margins: -4
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: settingsDlg.open()
                                        }
                                    }
                                }

                                MouseArea {
                                    id: promptItemArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.selectedPromptIndex = index
                                    z: -1
                                }
                            }
                        }
                    }
                }

                // ── Sessões recentes ───────────────────────────────────────
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: th.spacingXs
                    Text {
                        text: "SESSÕES RECENTES"
                        color: th.textTertiary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeLabel
                        font.weight: th.weightSemiBold
                        font.letterSpacing: 2.5
                    }
                    Text {
                        text: "—"
                        color: th.textTertiary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeCaption
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

                // ── Footer: mini-player + Config ───────────────────────────
                // Mini-player só aparece se o SimpMusic for detectado via MPRIS.
                Rectangle {
                    Layout.fillWidth: true
                    visible: backend.musicAvailable
                    radius: th.radiusSm
                    color: th.bgElevated
                    border.width: 1
                    border.color: th.borderSubtle
                    implicitHeight: playerCol.implicitHeight + 2 * th.spacingSm

                    Column {
                        id: playerCol
                        anchors.fill: parent
                        anchors.margins: th.spacingSm
                        spacing: th.spacingSm

                        // Faixa atual: capa + título
                        Row {
                            width: parent.width
                            spacing: th.spacingSm

                            // Capa do álbum (MPRIS artUrl). Carrega assíncrono —
                            // nunca bloqueia a GUI. Fallback: ícone de nota.
                            Rectangle {
                                width: 40; height: 40
                                radius: th.radiusSm
                                color: th.bgInput
                                clip: true

                                Image {
                                    id: albumArt
                                    anchors.fill: parent
                                    source: backend.musicArtUrl
                                    asynchronous: true
                                    cache: true
                                    fillMode: Image.PreserveAspectCrop
                                    visible: backend.musicArtUrl !== "" && status === Image.Ready
                                }
                                IconSvg {
                                    anchors.centerIn: parent
                                    width: 18; height: 18
                                    visible: !albumArt.visible
                                    d: "M9 18V5l12-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0M21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0"
                                    stroke: th.textTertiary
                                    strokeWidth: 2
                                }
                            }

                            Text {
                                width: parent.width - 40 - th.spacingSm
                                anchors.verticalCenter: parent.verticalCenter
                                readonly property bool playing: backend.musicTitle.length > 0
                                text: playing
                                    ? backend.musicTitle + (backend.musicArtist.length > 0 ? "  —  " + backend.musicArtist : "")
                                    : "Nada tocando"
                                color: playing ? th.textSecondary : th.textTertiary
                                font.family: th.fontFamily
                                font.pixelSize: th.sizeMicro
                                elide: Text.ElideRight
                            }
                        }

                        // Controles
                        Row {
                            width: parent.width
                            spacing: th.spacingXs

                            Repeater {
                                model: [
                                    { glyph: "⏮", tip: "Anterior",       action: "prev"   },
                                    { glyph: "▶", tip: "Tocar / Pausar",  action: "toggle" },
                                    { glyph: "⏭", tip: "Próxima",         action: "next"   },
                                    { glyph: "−", tip: "Diminuir volume", action: "down"   },
                                    { glyph: "+", tip: "Aumentar volume", action: "up"     },
                                ]
                                delegate: Rectangle {
                                    width: 28; height: 28; radius: 7
                                    readonly property bool primary: modelData.action === "toggle"
                                    readonly property bool isEnabled: modelData.action === "prev" ? backend.musicCanPrev
                                                                    : modelData.action === "next" ? backend.musicCanNext
                                                                    : true
                                    color: primary
                                        ? (ctrlArea.containsMouse ? th.accentDefault : th.accentSubtle)
                                        : (ctrlArea.containsMouse ? th.bgSurface : "transparent")
                                    opacity: isEnabled ? 1.0 : 0.35
                                    Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.action === "toggle"
                                            ? (backend.musicStatus === "Playing" ? "⏸" : "▶")
                                            : modelData.glyph
                                        font.family: th.fontFamily
                                        font.pixelSize: th.sizeBody
                                        color: primary
                                            ? (ctrlArea.containsMouse ? th.textOnAccent : th.accentDefault)
                                            : (ctrlArea.containsMouse ? th.textPrimary : th.textTertiary)
                                    }

                                    MouseArea {
                                        id: ctrlArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        enabled: parent.isEnabled
                                        cursorShape: Qt.PointingHandCursor
                                        ToolTip.visible: containsMouse
                                        ToolTip.text: modelData.tip
                                        ToolTip.delay: 400
                                        onClicked: {
                                            if (modelData.action === "toggle")    backend.musicPlayPause()
                                            else if (modelData.action === "prev")  backend.musicPrevious()
                                            else if (modelData.action === "next")  backend.musicNext()
                                            else                                   backend.musicVolume(modelData.action === "up" ? 1 : -1)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Config
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 36
                    radius: th.radiusSm
                    color: "transparent"
                    border.width: 1
                    border.color: configArea.containsMouse ? th.borderStrong : th.borderSubtle
                    Behavior on border.color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                    Row {
                        anchors.centerIn: parent
                        spacing: th.spacingSm
                        IconSvg {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 14; height: 14
                            d: "M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0 -6M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
                            stroke: configArea.containsMouse ? th.textPrimary : th.textSecondary
                            strokeWidth: 2
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: "Config"
                            color: configArea.containsMouse ? th.textPrimary : th.textSecondary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeSmall
                        }
                    }
                    MouseArea {
                        id: configArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: settingsDlg.open()
                    }
                }
            }
        }

        // ── Painel principal ───────────────────────────────────────────────
        ColumnLayout {
            id: mainPanel
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 44
            Layout.rightMargin: 44
            Layout.topMargin: 38
            Layout.bottomMargin: 38
            spacing: th.spacingLg

            opacity: 0
            transform: Translate { id: panelRise; y: 24 }
            Component.onCompleted: {
                if (backend.reduceMotion) { mainPanel.opacity = 1; panelRise.y = 0 }
                else panelEntrance.start()
            }
            SequentialAnimation {
                id: panelEntrance
                PauseAnimation { duration: 120 }
                ParallelAnimation {
                    NumberAnimation { target: mainPanel; property: "opacity"; to: 1; duration: th.durationSlow; easing.type: Easing.OutCubic }
                    NumberAnimation { target: panelRise; property: "y"; to: 0; duration: th.durationSlow; easing.type: Easing.OutCubic }
                }
            }

            // Header
            Column {
                Layout.fillWidth: true
                spacing: 6
                Text {
                    text: "O que você quer aprender?"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeDisplay
                    font.weight: th.weightBold
                    font.letterSpacing: -0.3
                }
                Text {
                    text: "Solte um material e o Kairos cuida do resto."
                    color: th.textTertiary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeSmall
                }
            }

            DropZone {
                id: dropZone
                Layout.fillWidth: true
                onSourceLoaded: (source) => backend.loadSource(source)
            }

            // Campo URL do YouTube (mantido — entrada além de arquivos)
            TextField {
                id: urlField
                Layout.fillWidth: true
                placeholderText: "Cole uma URL do YouTube e pressione Enter..."
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
                color: th.textPrimary
                placeholderTextColor: th.textTertiary
                selectByMouse: true

                background: Rectangle {
                    color: "transparent"
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 1
                        color: urlField.activeFocus ? th.accentDefault : th.borderSubtle
                        Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }
                    }
                }

                onAccepted: {
                    let t = urlField.text.trim()
                    if (t !== "") { backend.loadSource(t); urlField.clear() }
                }
            }

            // Botão Processar — ação primária âmbar
            Button {
                id: processBtn
                Layout.fillWidth: true
                enabled: backend.canProcess

                readonly property bool isRunning: backend.statusState === "running"

                transformOrigin: Item.Center
                scale: (!backend.reduceMotion && processBtn.enabled && !processBtn.isRunning)
                    ? (processBtn.down ? th.scalePress : 1.0)
                    : 1.0
                Behavior on scale {
                    enabled: !backend.reduceMotion
                    NumberAnimation { duration: th.durationFast; easing.type: Easing.OutCubic }
                }

                background: Rectangle {
                    radius: th.radiusMd
                    color: {
                        if (!processBtn.enabled) return th.bgElevated
                        if (processBtn.isRunning) return th.accentDefault
                        return processBtn.hovered ? th.accentHover : th.accentDefault
                    }
                    border.width: 1
                    border.color: {
                        if (!processBtn.enabled) return th.borderSubtle
                        return processBtn.hovered && !processBtn.isRunning ? th.accentHover : th.accentDefault
                    }
                    Behavior on color        { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                    Behavior on border.color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                }

                contentItem: Row {
                    spacing: th.spacingSm
                    anchors.centerIn: parent

                    // Ícone play / spinner
                    Item {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 17; height: 17

                        IconSvg {
                            id: playIcon
                            anchors.fill: parent
                            visible: !processBtn.isRunning
                            d: "M5 3l14 9-14 9V3z"
                            filled: true
                            stroke: processBtn.enabled ? th.textOnAccent : th.textTertiary
                        }
                        IconSvg {
                            id: spinIcon
                            anchors.fill: parent
                            visible: processBtn.isRunning
                            d: "M12 2a10 10 0 0 1 10 10"
                            strokeWidth: 2.4
                            stroke: th.textOnAccent
                            transformOrigin: Item.Center
                            RotationAnimation on rotation {
                                running: processBtn.isRunning && !backend.reduceMotion
                                loops: Animation.Infinite
                                from: 0; to: 360; duration: 1000
                            }
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: processBtn.isRunning ? "PROCESSANDO" : "PROCESSAR"
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeButton
                        font.letterSpacing: 2
                        font.weight: th.weightBold
                        color: processBtn.enabled ? th.textOnAccent : th.textTertiary
                    }
                }

                topPadding: 16; bottomPadding: 16
                onClicked: backend.process(root.selectedPromptIndex)
            }

            // Pipeline tracker
            PipelineTracker {
                Layout.fillWidth: true
            }

            // Status
            Text {
                id: statusText
                Layout.fillWidth: true
                text: backend.statusText
                textFormat: Text.RichText
                linkColor: th.accentDefault
                font.family: th.fontFamily
                font.pixelSize: th.sizeSmall
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: {
                    let s = backend.statusState
                    if (s === "running")  return th.stateRunningFg
                    if (s === "success")  return th.stateSuccessFg
                    if (s === "error")    return th.stateErrorFg
                    if (s === "warning")  return th.stateWarningFg
                    return th.stateIdleFg
                }
                Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
                onLinkActivated: (link) => Qt.openUrlExternally(link)
            }

            // Mapa de conhecimento — surge no estado success
            KnowledgeMap {
                id: knowledgeMap
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            // Espaçador só ocupa o vazio quando o mapa não está visível
            Item {
                Layout.fillHeight: true
                visible: !knowledgeMap.visible
            }
        }
    }

    // ── Toggle de tema (flutuante, top-right) ──────────────────────────────
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.rightMargin: 24
        width: 40; height: 40
        radius: 11
        z: 60
        color: th.bgElevated
        border.width: 1
        border.color: themeArea.containsMouse ? th.accentDefault : th.borderSubtle
        Behavior on border.color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

        IconSvg {
            anchors.centerIn: parent
            width: 18; height: 18
            stroke: themeArea.containsMouse ? th.accentDefault : th.textSecondary
            strokeWidth: 2
            // dark → sol (clicar vai pro claro); light → lua
            d: backend.darkMode
                ? "M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4M16 12a4 4 0 1 0 -8 0a4 4 0 1 0 8 0"
                : "M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"
        }

        MouseArea {
            id: themeArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: backend.toggleTheme()
        }
    }

    // ── Banner de atualização (flutuante, bottom-center) ───────────────────
    Rectangle {
        id: updateBanner
        visible: backend.updateAvailable
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: th.spacingXl
        z: 70

        width: bannerRow.implicitWidth + th.spacingLg * 2
        height: bannerRow.implicitHeight + th.spacingMd * 2
        radius: th.radiusLg
        color: th.bgElevated
        border.width: 1
        border.color: th.accentDefault

        opacity: backend.updateAvailable ? 1 : 0
        Behavior on opacity { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationNormal } }

        RowLayout {
            id: bannerRow
            anchors.centerIn: parent
            spacing: th.spacingMd

            IconSvg {
                Layout.preferredWidth: 18; Layout.preferredHeight: 18
                stroke: th.accentDefault
                strokeWidth: 2
                d: "M12 3v12M7 10l5 5 5-5M5 21h14"
            }

            Text {
                text: "Nova versão disponível: " + backend.updateVersion
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
                color: th.textPrimary
            }

            Rectangle {
                Layout.preferredHeight: 30
                Layout.preferredWidth: dlLabel.implicitWidth + th.spacingLg * 2
                radius: th.radiusMd
                color: dlArea.containsMouse ? th.accentHover : th.accentDefault
                Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                Text {
                    id: dlLabel
                    anchors.centerIn: parent
                    text: "Baixar"
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeButton
                    color: th.textOnAccent
                }
                MouseArea {
                    id: dlArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.openUpdatePage()
                }
            }

            IconSvg {
                Layout.preferredWidth: 16; Layout.preferredHeight: 16
                stroke: closeArea.containsMouse ? th.textPrimary : th.textTertiary
                strokeWidth: 2
                d: "M6 6l12 12M18 6L6 18"
                MouseArea {
                    id: closeArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.dismissUpdate()
                }
            }
        }
    }

    SettingsDialog { id: settingsDlg }

    ErrorDialog { id: errorDialog }

    Connections {
        target: backend
        function onDecisionNeeded(title, description) {
            errorDialog.openWith(title, description)
        }
    }
}

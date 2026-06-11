import QtQuick
import QtQuick.Dialogs
import QtQuick.Shapes
import "."

// Réplica de .dropzone do protótipo: borda tracejada (idle) → sólida âmbar
// (dragover/accepted), ícone-box 52px, título/subtítulo e pílulas de tipo.
Item {
    id: root

    signal sourceLoaded(string source)

    implicitHeight: 230

    Theme { id: th; darkMode: backend.darkMode }

    // Estado visual: "" (idle) | "dragover" | "accepted" | "invalid"
    property string dzState: ""

    readonly property bool _accepted: dzState === "accepted"
    readonly property bool _invalid:  dzState === "invalid"
    readonly property bool _drag:     dzState === "dragover"

    // Cor de borda corrente (animável). Idle pulsa entre border-strong e accent-dim.
    property color borderColor: th.borderStrong
    Behavior on borderColor { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }

    transformOrigin: Item.Center
    scale: (!backend.reduceMotion && _drag) ? th.scaleHover : 1.0
    Behavior on scale { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationNormal; easing.type: Easing.OutCubic } }

    // ── Fundo + overlay âmbar ──────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        radius: th.radiusLg
        color: th.bgSurface
        Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }

        Rectangle {
            anchors.fill: parent
            radius: th.radiusLg
            color: th.accentSubtle
            opacity: (root._drag || root._accepted) ? 1 : 0
            Behavior on opacity { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationNormal } }
        }
    }

    // ── Borda (Shape: tracejada no idle, sólida nos demais) ────────────────
    Shape {
        anchors.fill: parent
        antialiasing: true
        ShapePath {
            strokeColor: root.borderColor
            strokeWidth: 2
            fillColor: "transparent"
            strokeStyle: (root.dzState === "") ? ShapePath.DashLine : ShapePath.SolidLine
            dashPattern: [5, 4]
            joinStyle: ShapePath.RoundJoin
            PathRectangle {
                x: 1; y: 1
                width: root.width - 2
                height: root.height - 2
                radius: th.radiusLg
            }
        }
    }

    // ── Conteúdo ───────────────────────────────────────────────────────────
    Column {
        anchors.centerIn: parent
        spacing: th.spacingMd

        // dz-icon
        Rectangle {
            id: dzIcon
            anchors.horizontalCenter: parent.horizontalCenter
            width: 52; height: 52
            radius: 14
            color: root._accepted ? th.accentDefault : th.bgElevated
            border.width: 1
            border.color: root._accepted ? th.accentDefault : th.borderSubtle
            Behavior on color        { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
            Behavior on border.color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }

            IconSvg {
                anchors.centerIn: parent
                width: 24; height: 24
                stroke: root._accepted ? th.textOnAccent
                       : root._invalid ? th.stateErrorFg : th.accentDefault
                strokeWidth: root._accepted ? 2.5 : 2
                // upload (idle) → check (accepted)
                d: root._accepted
                    ? "M20 6 9 17l-5-5"
                    : "M12 3v12M7 8l5-5 5 5M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
            }
        }

        // dz-title
        Text {
            id: dzTitle
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(implicitWidth, root.width - 64)
            text: root._accepted ? root._acceptedName
                : root._invalid ? "Formato inválido"
                : "Solte um arquivo aqui"
            color: root._invalid ? th.stateErrorFg : th.textPrimary
            font.family: th.fontFamily
            font.pixelSize: th.sizeH3
            font.weight: th.weightSemiBold
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideMiddle
            Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationNormal } }
        }

        // dz-sub
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root._accepted ? "pronto para processar"
                : root._invalid ? "use PDF, texto, áudio ou URL do YouTube"
                : "ou clique para procurar"
            color: th.textTertiary
            font.family: th.fontFamily
            font.pixelSize: th.sizeSmall
            font.letterSpacing: 0.3
            horizontalAlignment: Text.AlignHCenter
        }

        // dz-types (pílulas) — escondidas quando aceito
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: th.spacingSm
            visible: !root._accepted
            opacity: root._invalid ? 0 : 1

            Repeater {
                model: ["PDF", "TEXTO", "YOUTUBE", "ÁUDIO"]
                delegate: Rectangle {
                    radius: th.radiusPill
                    color: th.bgElevated
                    border.width: 1
                    border.color: th.borderSubtle
                    implicitWidth: pillText.implicitWidth + 20
                    implicitHeight: pillText.implicitHeight + 8
                    Text {
                        id: pillText
                        anchors.centerIn: parent
                        text: modelData
                        color: th.textSecondary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeTag
                        font.letterSpacing: 0.5
                    }
                }
            }
        }
    }

    // ── Animação breathe (só no idle) ──────────────────────────────────────
    SequentialAnimation {
        running: root.dzState === "" && !backend.reduceMotion && !hoverArea.containsMouse
        loops: Animation.Infinite
        onStopped: root.borderColor = root._idleBorderColor()
        ColorAnimation { target: root; property: "borderColor"; to: th.accentSubtle; duration: th.durationBreathe / 2; easing.type: Easing.InOutSine }
        ColorAnimation { target: root; property: "borderColor"; to: th.borderStrong; duration: th.durationBreathe / 2; easing.type: Easing.InOutSine }
    }

    // Borda estática quando não está respirando (hover/dragover/accepted/invalid)
    onDzStateChanged: borderColor = _idleBorderColor()

    function _idleBorderColor() {
        if (dzState === "accepted") return th.accentDefault
        if (dzState === "dragover") return th.accentDefault
        if (dzState === "invalid")  return th.stateErrorFg
        if (hoverArea.containsMouse) return th.accentDefault
        return th.borderStrong
    }

    // ── Interação ──────────────────────────────────────────────────────────
    DropArea {
        anchors.fill: parent
        onEntered: (drag) => { if (root.dzState !== "accepted") root.dzState = "dragover" }
        onExited: { if (root.dzState === "dragover") root.dzState = "" }
        onDropped: (drop) => {
            root.dzState = ""
            if (drop.urls.length === 0) { root._showInvalid(); return }
            let urlStr = drop.urls[0].toString()
            if (urlStr.startsWith("file://")) {
                let localPath = urlStr.replace(/^file:\/\//, "").toLowerCase()
                let ok = [".pdf", ".txt", ".md", ".markdown",
                          ".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac"]
                    .some((s) => localPath.endsWith(s))
                if (!ok) { root._showInvalid(); return }
                root._acceptSource(urlStr, urlStr.replace(/^file:\/\//, "").split("/").pop())
            } else if (urlStr.indexOf("youtube.com") !== -1 || urlStr.indexOf("youtu.be") !== -1) {
                let display = urlStr.length <= 42 ? urlStr : urlStr.substring(0, 39) + "..."
                root._acceptSource(urlStr, display)
            } else {
                root._showInvalid()
            }
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onContainsMouseChanged: root.borderColor = root._idleBorderColor()
        onClicked: fileDialog.open()
    }

    FileDialog {
        id: fileDialog
        title: "Selecione um material"
        nameFilters: [
            "Materiais (*.pdf *.txt *.md *.markdown *.mp3 *.wav *.m4a *.ogg *.opus *.flac)",
            "Arquivos PDF (*.pdf)",
            "Texto (*.txt *.md *.markdown)",
            "Áudio (*.mp3 *.wav *.m4a *.ogg *.opus *.flac)"
        ]
        onAccepted: {
            let urlStr = fileDialog.selectedFile.toString()
            let filename = urlStr.split("/").pop()
            root._acceptSource(urlStr, filename)
        }
    }

    Timer {
        id: resetTimer
        interval: 2000
        onTriggered: root.dzState = ""
    }

    property string _acceptedName: ""

    function _acceptSource(source, displayName) {
        resetTimer.stop()
        _acceptedName = displayName
        dzState = "accepted"
        root.sourceLoaded(source)
    }

    function _showInvalid() {
        dzState = "invalid"
        resetTimer.restart()
    }
}

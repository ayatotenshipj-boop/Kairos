import QtQuick
import QtQuick.Layouts
import "."

// Mapa de conhecimento — grafo radial do tema recém-processado.
// Lê backend.graphData (read-only: desenha o que está no vault) e abre cada nota
// no Obsidian via backend.openNote(). Visual fiel à seção brain map do protótipo.
Rectangle {
    id: kmRoot

    property var graph: backend.graphData
    readonly property var nodes: (graph && graph.nodes) ? graph.nodes : []
    readonly property int nodeCount: nodes.length
    readonly property bool hasMap: graph && graph.central !== undefined
                                   && backend.statusState === "success"
    property int hotIndex: -1
    property real reveal: 0

    visible: hasMap
    color: th.bgSurface
    radius: th.radiusLg
    border.width: 1
    border.color: th.borderSubtle
    clip: true

    Theme { id: th; darkMode: backend.darkMode }

    onHasMapChanged: {
        hotIndex = -1
        if (hasMap) {
            if (backend.reduceMotion) reveal = 1
            else { reveal = 0; revealAnim.restart() }
        } else {
            reveal = 0
        }
        lineCanvas.requestPaint()
    }
    onRevealChanged: lineCanvas.requestPaint()

    NumberAnimation {
        id: revealAnim
        target: kmRoot
        property: "reveal"
        to: 1
        duration: th.durationSlow
        easing.type: Easing.OutCubic
    }

    function nodePos(i) {
        var w = canvasArea.width, h = canvasArea.height
        var cx = w / 2, cy = h / 2
        var rx = w * 0.34, ry = h * 0.34 * 0.92
        var ang = (2 * Math.PI / Math.max(1, nodeCount)) * i - Math.PI / 2
        return Qt.point(cx + rx * Math.cos(ang), cy + ry * Math.sin(ang))
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: th.spacingLg
        spacing: th.spacingXs

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "MAPA DE CONHECIMENTO"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeLabel
                font.weight: th.weightSemiBold
                font.letterSpacing: 2.5
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "do seu vault Obsidian"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
            }
        }

        Text {
            text: kmRoot.hasMap
                  ? ("📁 " + kmRoot.graph.central + "/  ·  "
                     + (kmRoot.nodeCount + 1) + " notas linkadas")
                  : ""
            color: th.textTertiary
            font.family: th.fontFamily
            font.pixelSize: th.sizeSmall
        }

        Item {
            id: canvasArea
            Layout.fillWidth: true
            Layout.fillHeight: true

            onWidthChanged: lineCanvas.requestPaint()
            onHeightChanged: lineCanvas.requestPaint()

            // Linhas centro → sub-nó (traçadas conforme reveal)
            Canvas {
                id: lineCanvas
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    var cx = width / 2, cy = height / 2
                    for (var i = 0; i < kmRoot.nodeCount; i++) {
                        var p = kmRoot.nodePos(i)
                        var ex = cx + (p.x - cx) * kmRoot.reveal
                        var ey = cy + (p.y - cy) * kmRoot.reveal
                        ctx.beginPath()
                        ctx.moveTo(cx, cy)
                        ctx.lineTo(ex, ey)
                        ctx.lineWidth = (i === kmRoot.hotIndex) ? 2.5 : 1.5
                        ctx.strokeStyle = (i === kmRoot.hotIndex)
                            ? th.accentDefault : th.borderStrong
                        ctx.stroke()
                    }
                }
            }

            // Nó central
            Item {
                id: central
                width: centralCol.width
                height: centralCol.height
                x: canvasArea.width / 2 - width / 2
                y: canvasArea.height / 2 - height / 2
                opacity: Math.min(1, kmRoot.reveal * (kmRoot.nodeCount + 1))

                Column {
                    id: centralCol
                    spacing: th.spacingXs

                    Item {
                        width: 34; height: 34
                        anchors.horizontalCenter: parent.horizontalCenter
                        Rectangle {  // glow
                            anchors.centerIn: parent
                            width: 52; height: 52; radius: 26
                            color: "transparent"
                            border.color: th.accentSubtle
                            border.width: 10
                        }
                        Rectangle {
                            anchors.fill: parent
                            radius: 17
                            color: th.accentDefault
                            border.color: th.accentDefault
                            border.width: 2
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: kmRoot.hasMap ? kmRoot.graph.central : ""
                        color: th.textPrimary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeH3
                        font.weight: th.weightBold
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "tema · pasta"
                        color: th.accentDefault
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeTag
                        font.letterSpacing: 0.5
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (kmRoot.hasMap) backend.openNote(kmRoot.graph.central_path)
                }
            }

            // Sub-nós
            Repeater {
                model: kmRoot.nodes

                delegate: Item {
                    id: sub
                    required property int index
                    required property var modelData
                    readonly property real appear:
                        Math.max(0, Math.min(1, kmRoot.reveal * (kmRoot.nodeCount + 1) - index))
                    readonly property point pos: kmRoot.nodePos(index)
                    property bool hovered: false

                    width: subCol.width
                    height: subCol.height
                    x: pos.x - width / 2
                    y: pos.y - height / 2
                    opacity: appear
                    scale: 0.5 + 0.5 * appear

                    Column {
                        id: subCol
                        spacing: th.spacingXs
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 17; height: 17; radius: 8.5
                            color: sub.hovered ? th.accentDefault : th.bgElevated
                            border.color: sub.hovered ? th.accentDefault : th.textTertiary
                            border.width: 2
                            Behavior on color {
                                enabled: !backend.reduceMotion
                                ColorAnimation { duration: th.durationFast }
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 110
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            text: sub.modelData.label
                            color: sub.hovered ? th.accentDefault : th.textSecondary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeCaption
                            Behavior on color {
                                enabled: !backend.reduceMotion
                                ColorAnimation { duration: th.durationFast }
                            }
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "nota"
                            color: th.textTertiary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeTag
                            font.letterSpacing: 0.5
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: { sub.hovered = true; kmRoot.hotIndex = sub.index }
                        onExited: {
                            sub.hovered = false
                            if (kmRoot.hotIndex === sub.index) kmRoot.hotIndex = -1
                        }
                        onClicked: backend.openNote(sub.modelData.path)
                    }
                }
            }
        }
    }
}

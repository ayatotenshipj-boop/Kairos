import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

// Diálogo de escolha reutilizável para falhas do pipeline (arquivo muito grande,
// backend indisponível, falha de processamento). Oferece duas saídas:
// "Salvar localmente" (#pendente) ou "Cancelar" (volta à DropZone).
// Nunca bloqueia a UI thread — apenas dispara slots do backend.
Dialog {
    id: root

    property string heading: ""
    property string body: ""

    function openWith(title, description) {
        root.heading = title
        root.body = description
        root.open()
    }

    modal: true
    anchors.centerIn: Overlay.overlay
    width: 460
    padding: 26
    standardButtons: Dialog.NoButton
    closePolicy: Popup.NoAutoClose

    Theme { id: th; darkMode: backend.darkMode }

    background: Rectangle {
        color: th.bgSurface
        border.color: th.borderStrong
        border.width: 1
        radius: th.radiusLg
    }

    enter: Transition {
        NumberAnimation {
            property: "opacity"; from: 0; to: 1
            duration: backend.reduceMotion ? 0 : th.durationNormal
            easing.type: Easing.OutCubic
        }
    }
    exit: Transition {
        NumberAnimation {
            property: "opacity"; from: 1; to: 0
            duration: backend.reduceMotion ? 0 : th.durationFast
            easing.type: Easing.InCubic
        }
    }

    contentItem: ColumnLayout {
        spacing: th.spacingLg

        Text {
            text: root.heading
            color: th.textPrimary
            font.family: th.fontFamily
            font.pixelSize: th.sizeH2
            font.weight: th.weightBold
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            text: root.body
            color: th.textSecondary
            font.family: th.fontFamily
            font.pixelSize: th.sizeBody
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: th.spacingSm

            Item { Layout.fillWidth: true }

            // Cancelar
            Rectangle {
                implicitWidth: cancelText.implicitWidth + 2 * th.spacingLg
                implicitHeight: 34
                radius: th.radiusSharp
                color: cancelArea.containsMouse ? th.bgElevated : th.bgSurface
                border.width: 1
                border.color: cancelArea.containsMouse ? th.borderStrong : th.borderSubtle
                Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                Text {
                    id: cancelText
                    anchors.centerIn: parent
                    text: "Cancelar"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeButton
                }
                MouseArea {
                    id: cancelArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: { backend.cancelProcessing(); root.close() }
                }
            }

            // Salvar localmente
            Rectangle {
                implicitWidth: saveText.implicitWidth + 2 * th.spacingLg
                implicitHeight: 34
                radius: th.radiusSharp
                color: saveArea.containsMouse ? th.accentHover : th.accentDefault
                Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                Text {
                    id: saveText
                    anchors.centerIn: parent
                    text: "Salvar localmente"
                    color: th.textOnAccent
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeButton
                    font.weight: th.weightSemiBold
                }
                MouseArea {
                    id: saveArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: { backend.saveLocally(); root.close() }
                }
            }
        }
    }
}

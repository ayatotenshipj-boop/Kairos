import QtQuick
import QtQuick.Controls
import "."

Dialog {
    id: root

    property string initialLabel: ""
    property string initialText:  ""

    modal: true
    title: initialLabel !== "" ? "Editar prompt" : "Novo prompt"
    standardButtons: Dialog.NoButton

    width: 540
    padding: 26

    background: Rectangle {
        color: th.bgSurface
        border.color: th.borderStrong
        border.width: 1
        radius: th.radiusLg
    }

    Theme { id: th; darkMode: backend.darkMode }

    onOpened: {
        labelField.text = root.initialLabel
        promptField.text = root.initialText
        labelField.forceActiveFocus()
    }

    Column {
        width: parent.width
        spacing: th.spacingMd

        Text {
            width: parent.width
            text: "Defina como a IA deve abordar o conteúdo."
            color: th.textTertiary
            font.family: th.fontFamily
            font.pixelSize: th.sizeCaption
            wrapMode: Text.Wrap
            bottomPadding: th.spacingSm
        }

        Text {
            text: "Nome"
            color: th.textTertiary
            font.family: th.fontFamily
            font.pixelSize: th.sizeLabel
            font.weight: th.weightSemiBold
            font.letterSpacing: 2
            font.capitalization: Font.AllUppercase
        }

        TextField {
            id: labelField
            width: parent.width
            placeholderText: "Ex: Conceitos-chave"
            font.family: th.fontFamily
            font.pixelSize: th.sizeBody
            color: th.textPrimary
            placeholderTextColor: th.textTertiary
            selectByMouse: true
            background: Rectangle {
                color: th.bgInput
                border.color: labelField.activeFocus ? th.accentMuted : th.borderSubtle
                border.width: 1
                radius: th.radiusSharp
                Behavior on border.color { ColorAnimation { duration: th.durationFast } }
            }
        }

        Text {
            text: "Instrução enviada à IA"
            color: th.textTertiary
            font.family: th.fontFamily
            font.pixelSize: th.sizeLabel
            font.weight: th.weightSemiBold
            font.letterSpacing: 2
            font.capitalization: Font.AllUppercase
        }

        ScrollView {
            width: parent.width
            height: 140
            clip: true

            TextArea {
                id: promptField
                width: parent.width
                wrapMode: TextArea.Wrap
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
                color: th.textPrimary
                placeholderText: "Texto do prompt..."
                placeholderTextColor: th.textTertiary
                selectByMouse: true
                background: Rectangle {
                    color: th.bgInput
                    border.color: promptField.activeFocus ? th.accentMuted : th.borderSubtle
                    border.width: 1
                    radius: th.radiusSharp
                    Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                }
            }
        }

        // Instrução de estrutura sempre concatenada ao prompt (read-only).
        // Parte da arquitetura — não editável pelo usuário.
        Rectangle {
            width: parent.width
            height: structureColumn.implicitHeight + th.spacingMd * 2
            color: th.accentSubtle
            border.color: th.accentMuted
            border.width: 1
            radius: th.radiusSm

            Column {
                id: structureColumn
                anchors.fill: parent
                anchors.margins: th.spacingMd
                spacing: th.spacingSm

                Row {
                    spacing: th.spacingSm
                    IconSvg {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 13; height: 13
                        d: "M5 11h14v11H5zM7 11V7a5 5 0 0 1 10 0v4"
                        stroke: th.accentDefault
                        strokeWidth: 2
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Sempre adicionado automaticamente"
                        color: th.accentDefault
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeMicro
                        font.weight: th.weightSemiBold
                        font.letterSpacing: 1
                        font.capitalization: Font.AllUppercase
                    }
                }

                Text {
                    width: parent.width
                    text: backend.structureInstruction
                    color: th.textSecondary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeSmall
                    wrapMode: Text.Wrap
                }
            }
        }

        Row {
            anchors.right: parent.right
            spacing: th.spacingSm

            Button {
                id: cancelBtn
                text: "Cancelar"
                onClicked: root.reject()

                background: Rectangle {
                    radius: th.radiusSm
                    color: cancelBtn.hovered ? th.bgElevated : "transparent"
                    border.color: cancelBtn.hovered ? th.borderStrong : th.borderSubtle
                    border.width: 1
                    Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                    Behavior on color        { ColorAnimation { duration: th.durationFast } }
                }
                contentItem: Text {
                    text: cancelBtn.text
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeSmall
                    font.weight: th.weightSemiBold
                    color: th.textSecondary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                leftPadding: 20; rightPadding: 20; topPadding: 8; bottomPadding: 8
            }

            Button {
                id: saveBtn
                text: "Salvar"
                enabled: labelField.text.trim() !== "" && promptField.text.trim() !== ""
                onClicked: root.accept()

                background: Rectangle {
                    radius: th.radiusSm
                    color: saveBtn.enabled
                        ? (saveBtn.hovered ? th.accentHover : th.accentDefault)
                        : th.bgElevated
                    border.width: saveBtn.enabled ? 0 : 1
                    border.color: th.borderSubtle
                    Behavior on color { ColorAnimation { duration: th.durationFast } }
                }
                contentItem: Text {
                    text: saveBtn.text
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeSmall
                    font.weight: th.weightSemiBold
                    color: saveBtn.enabled ? th.textOnAccent : th.textTertiary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    Behavior on color { ColorAnimation { duration: th.durationFast } }
                }
                leftPadding: 20; rightPadding: 20; topPadding: 8; bottomPadding: 8
            }
        }
    }

    function getLabelText()  { return labelField.text.trim() }
    function getPromptText() { return promptField.text.trim() }
}

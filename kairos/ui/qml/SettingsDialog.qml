import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Dialog {
    id: root

    modal: true
    title: "Configurações"
    standardButtons: Dialog.NoButton

    width: 560
    padding: 0

    background: Rectangle {
        color: th.bgSurface
        border.color: th.borderDefault
        border.width: 1
        radius: th.radiusSharp
    }

    // Abertura/fechamento suave (instantâneo sob reduced-motion).
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

    Theme { id: th; darkMode: backend.darkMode }

    property int _editingIndex: -1
    readonly property var _backendValues: ["notebooklm", "gemini", "ollama"]
    property string _geminiModel: ""

    onOpened: _loadSettings()

    ColumnLayout {
        width: parent.width
        spacing: 0

        // Caminhos
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            spacing: th.spacingMd

            Text {
                text: "CAMINHOS"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                font.letterSpacing: 3
            }

            // Vault Obsidian
            ColumnLayout {
                Layout.fillWidth: true
                spacing: th.spacingXs

                Text {
                    text: "Vault do Obsidian:"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: th.spacingSm

                    TextField {
                        id: vaultField
                        Layout.fillWidth: true
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeBody
                        color: th.textPrimary
                        placeholderTextColor: th.textTertiary
                        selectByMouse: true
                        background: Rectangle {
                            color: th.bgInput
                            border.color: vaultField.activeFocus ? th.accentMuted : th.borderSubtle
                            border.width: 1
                            radius: th.radiusSharp
                            Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                        }
                    }
                    Button {
                        text: "Procurar"
                        onClicked: {
                            let p = backend.browseForPath(vaultField.text, true)
                            if (p !== "") vaultField.text = p
                        }
                        leftPadding: 12; rightPadding: 12; topPadding: 5; bottomPadding: 5
                        background: Rectangle {
                            radius: th.radiusSharp
                            color: parent.hovered ? th.bgElevated : th.bgSurface
                            border.color: parent.hovered ? th.borderDefault : th.borderSubtle
                            border.width: 1
                            Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                            Behavior on color        { ColorAnimation { duration: th.durationFast } }
                        }
                        contentItem: Text {
                            text: parent.text
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeBody
                            color: th.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            // Simpmusic
            ColumnLayout {
                Layout.fillWidth: true
                spacing: th.spacingXs

                Text {
                    text: "Simpmusic:"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: th.spacingSm

                    TextField {
                        id: simpField
                        Layout.fillWidth: true
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeBody
                        color: th.textPrimary
                        placeholderTextColor: th.textTertiary
                        selectByMouse: true
                        background: Rectangle {
                            color: th.bgInput
                            border.color: simpField.activeFocus ? th.accentMuted : th.borderSubtle
                            border.width: 1
                            radius: th.radiusSharp
                            Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                        }
                    }
                    Button {
                        text: "Procurar"
                        onClicked: {
                            let p = backend.browseForPath(simpField.text, false)
                            if (p !== "") simpField.text = p
                        }
                        leftPadding: 12; rightPadding: 12; topPadding: 5; bottomPadding: 5
                        background: Rectangle {
                            radius: th.radiusSharp
                            color: parent.hovered ? th.bgElevated : th.bgSurface
                            border.color: parent.hovered ? th.borderDefault : th.borderSubtle
                            border.width: 1
                            Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                            Behavior on color        { ColorAnimation { duration: th.durationFast } }
                        }
                        contentItem: Text {
                            text: parent.text
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeBody
                            color: th.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

        // Processamento
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            spacing: th.spacingMd

            Text {
                text: "PROCESSAMENTO"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                font.letterSpacing: 3
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: th.spacingXs

                Text {
                    text: "Backend de IA:"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                }

                ComboBox {
                    id: backendCombo
                    Layout.fillWidth: true
                    model: ["NotebookLM", "Gemini", "Local"]
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody

                    background: Rectangle {
                        color: th.bgInput
                        border.color: backendCombo.activeFocus ? th.accentMuted : th.borderSubtle
                        border.width: 1
                        radius: th.radiusSharp
                        Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                    }
                    contentItem: Text {
                        leftPadding: th.spacingSm
                        text: backendCombo.displayText
                        color: th.textPrimary
                        font.family: th.fontFamily
                        font.pixelSize: th.sizeBody
                        verticalAlignment: Text.AlignVCenter
                    }
                    delegate: ItemDelegate {
                        width: backendCombo.width
                        contentItem: Text {
                            text: modelData
                            color: th.textPrimary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeBody
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            color: highlighted ? th.bgElevated : th.bgSurface
                        }
                    }
                    popup: Popup {
                        y: backendCombo.height
                        width: backendCombo.width
                        padding: 1
                        contentItem: ListView {
                            clip: true
                            implicitHeight: contentHeight
                            model: backendCombo.popup.visible ? backendCombo.delegateModel : null
                        }
                        background: Rectangle {
                            color: th.bgSurface
                            border.color: th.borderDefault
                            border.width: 1
                            radius: th.radiusSharp
                        }
                    }
                }
            }

            // Gemini — chave de API (oculta) + aviso de privacidade
            ColumnLayout {
                Layout.fillWidth: true
                spacing: th.spacingXs
                visible: backendCombo.currentIndex === 1

                Text {
                    text: "Chave da API do Gemini:"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                }
                TextField {
                    id: geminiKeyField
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: "ou via variável de ambiente GEMINI_API_KEY"
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                    color: th.textPrimary
                    placeholderTextColor: th.textTertiary
                    selectByMouse: true
                    background: Rectangle {
                        color: th.bgInput
                        border.color: geminiKeyField.activeFocus ? th.accentMuted : th.borderSubtle
                        border.width: 1
                        radius: th.radiusSharp
                        Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                    }
                }
                Text {
                    text: "Privacidade: no free tier, o Google pode usar os inputs para treinar seus modelos."
                    color: th.textTertiary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeCaption
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }

            // Local — endpoint (modelo inferido pelo servidor)
            ColumnLayout {
                Layout.fillWidth: true
                spacing: th.spacingXs
                visible: backendCombo.currentIndex === 2

                Text {
                    text: "Endpoint do servidor local:"
                    color: th.textPrimary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                }
                TextField {
                    id: localEndpointField
                    Layout.fillWidth: true
                    placeholderText: "ex.: http://localhost:11434"
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                    color: th.textPrimary
                    placeholderTextColor: th.textTertiary
                    selectByMouse: true
                    background: Rectangle {
                        color: th.bgInput
                        border.color: localEndpointField.activeFocus ? th.accentMuted : th.borderSubtle
                        border.width: 1
                        radius: th.radiusSharp
                        Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                    }
                }
                Text {
                    text: "Requer um servidor local em execução. O modelo é inferido pelo servidor."
                    color: th.textTertiary
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeCaption
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

        // Interface
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            spacing: th.spacingSm

            Text {
                text: "INTERFACE"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                font.letterSpacing: 3
            }

            Switch {
                id: reduceMotionSwitch
                text: "Reduzir movimento"
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody

                indicator: Rectangle {
                    implicitWidth: 40
                    implicitHeight: 20
                    x: reduceMotionSwitch.leftPadding
                    y: reduceMotionSwitch.height / 2 - height / 2
                    radius: 10
                    color: reduceMotionSwitch.checked ? th.accentDefault : th.bgInput
                    border.color: reduceMotionSwitch.checked ? th.accentDefault : th.borderDefault
                    border.width: 1
                    Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                    Rectangle {
                        x: reduceMotionSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                        width: 16
                        height: 16
                        radius: 8
                        color: reduceMotionSwitch.checked ? th.textOnAccent : th.textTertiary
                        Behavior on x { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationFast } }
                    }
                }

                contentItem: Text {
                    text: reduceMotionSwitch.text
                    font: reduceMotionSwitch.font
                    color: th.textPrimary
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: reduceMotionSwitch.indicator.width + th.spacingSm
                }
            }

            Text {
                text: "Desativa pulsos e animações de entrada."
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Switch {
                id: discordSwitch
                text: "Discord Rich Presence"
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody

                indicator: Rectangle {
                    implicitWidth: 40
                    implicitHeight: 20
                    x: discordSwitch.leftPadding
                    y: discordSwitch.height / 2 - height / 2
                    radius: 10
                    color: discordSwitch.checked ? th.accentDefault : th.bgInput
                    border.color: discordSwitch.checked ? th.accentDefault : th.borderDefault
                    border.width: 1
                    Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                    Rectangle {
                        x: discordSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                        width: 16
                        height: 16
                        radius: 8
                        color: discordSwitch.checked ? th.textOnAccent : th.textTertiary
                        Behavior on x { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationFast } }
                    }
                }

                contentItem: Text {
                    text: discordSwitch.text
                    font: discordSwitch.font
                    color: th.textPrimary
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: discordSwitch.indicator.width + th.spacingSm
                }
            }

            TextField {
                id: discordClientIdField
                visible: discordSwitch.checked
                Layout.fillWidth: true
                placeholderText: "Application (Client) ID do Discord Developer Portal"
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
                color: th.textPrimary
                placeholderTextColor: th.textTertiary
                selectByMouse: true
                background: Rectangle {
                    color: th.bgInput
                    border.color: discordClientIdField.activeFocus ? th.accentMuted : th.borderSubtle
                    border.width: 1
                    radius: th.radiusSharp
                    Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                }
            }
            Text {
                visible: discordSwitch.checked
                text: "Requer o Discord aberto e um App ID. Sem Discord, nada acontece."
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

        // Música
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            spacing: th.spacingSm

            Text {
                text: "MÚSICA"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                font.letterSpacing: 3
            }

            Switch {
                id: simpAutostartSwitch
                text: "Iniciar SimpMusic junto"
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody

                indicator: Rectangle {
                    implicitWidth: 40
                    implicitHeight: 20
                    x: simpAutostartSwitch.leftPadding
                    y: simpAutostartSwitch.height / 2 - height / 2
                    radius: 10
                    color: simpAutostartSwitch.checked ? th.accentDefault : th.bgInput
                    border.color: simpAutostartSwitch.checked ? th.accentDefault : th.borderDefault
                    border.width: 1
                    Behavior on color { enabled: !backend.reduceMotion; ColorAnimation { duration: th.durationFast } }

                    Rectangle {
                        x: simpAutostartSwitch.checked ? parent.width - width - 2 : 2
                        y: 2
                        width: 16
                        height: 16
                        radius: 8
                        color: simpAutostartSwitch.checked ? th.textOnAccent : th.textTertiary
                        Behavior on x { enabled: !backend.reduceMotion; NumberAnimation { duration: th.durationFast } }
                    }
                }

                contentItem: Text {
                    text: simpAutostartSwitch.text
                    font: simpAutostartSwitch.font
                    color: th.textPrimary
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: simpAutostartSwitch.indicator.width + th.spacingSm
                }
            }

            Text {
                text: "Desligado: o SimpMusic não abre com o Kairos."
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                text: "Playlist (URL):"
                color: th.textPrimary
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
            }
            TextField {
                id: playlistUrlField
                Layout.fillWidth: true
                placeholderText: "ex.: https://simpmusic.org/app/playlist?list=..."
                font.family: th.fontFamily
                font.pixelSize: th.sizeBody
                color: th.textPrimary
                placeholderTextColor: th.textTertiary
                selectByMouse: true
                background: Rectangle {
                    color: th.bgInput
                    border.color: playlistUrlField.activeFocus ? th.accentMuted : th.borderSubtle
                    border.width: 1
                    radius: th.radiusSharp
                    Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                }
            }
            Text {
                text: "Aberta automaticamente ao iniciar o SimpMusic."
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                text: "SimpMusic não encontrado."
                visible: !backend.musicAvailable
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

        // Prompts
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            spacing: th.spacingMd

            Text {
                text: "PROMPTS"
                color: th.textTertiary
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
                font.letterSpacing: 3
            }

            Rectangle {
                Layout.fillWidth: true
                height: 160
                color: th.bgInput
                border.color: th.borderSubtle
                border.width: 1
                radius: th.radiusSharp
                clip: true

                ListView {
                    id: promptList
                    anchors.fill: parent
                    anchors.margins: 2
                    model: promptsModel
                    clip: true

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        contentItem: Rectangle {
                            implicitWidth: 4
                            color: th.borderDefault
                            radius: 2
                        }
                    }

                    delegate: Rectangle {
                        width: promptList.width
                        height: 32
                        color: promptList.currentIndex === index
                            ? th.bgSurface
                            : (mouseArea.containsMouse ? th.bgElevated : "transparent")
                        Behavior on color { ColorAnimation { duration: th.durationFast } }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            leftPadding: th.spacingSm
                            text: model.label
                            color: promptList.currentIndex === index ? th.accentDefault : th.textPrimary
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeBody
                            Behavior on color { ColorAnimation { duration: th.durationFast } }
                        }

                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: promptList.currentIndex = index
                        }
                    }
                }
            }

            // CRUD buttons
            Row {
                spacing: th.spacingSm

                Repeater {
                    model: [
                        { label: "Adicionar", action: "add"    },
                        { label: "Editar",    action: "edit"   },
                        { label: "Remover",   action: "remove" },
                    ]
                    Button {
                        text: modelData.label
                        topPadding: 4; bottomPadding: 4; leftPadding: 12; rightPadding: 12
                        onClicked: {
                            if (modelData.action === "add") {
                                root._editingIndex = -1
                                promptEditDlg.initialLabel = ""
                                promptEditDlg.initialText  = ""
                                promptEditDlg.open()
                            } else if (modelData.action === "edit") {
                                let idx = promptList.currentIndex
                                if (idx < 0) return
                                root._editingIndex = idx
                                promptEditDlg.initialLabel = promptsModel.get(idx).label
                                promptEditDlg.initialText  = promptsModel.get(idx).text
                                promptEditDlg.open()
                            } else {
                                let idx = promptList.currentIndex
                                if (idx < 0) return
                                if (promptsModel.count <= 1) { removeWarning.visible = true; return }
                                promptsModel.remove(idx)
                                promptList.currentIndex = Math.min(idx, promptsModel.count - 1)
                            }
                        }
                        background: Rectangle {
                            radius: th.radiusSharp
                            color: parent.hovered ? th.bgElevated : th.bgSurface
                            border.color: parent.hovered ? th.borderDefault : th.borderSubtle
                            border.width: 1
                            Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                            Behavior on color        { ColorAnimation { duration: th.durationFast } }
                        }
                        contentItem: Text {
                            text: parent.text
                            font.family: th.fontFamily
                            font.pixelSize: th.sizeBody
                            color: th.textPrimary
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            Text {
                id: removeWarning
                visible: false
                text: "É necessário ter pelo menos um prompt."
                color: th.stateWarningFg
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
            }

            Text {
                id: saveError
                visible: false
                text: ""
                color: th.stateErrorFg
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
            }

            Text {
                id: saveOk
                visible: false
                text: "Configurações salvas ✓"
                color: th.stateSuccessFg
                font.family: th.fontFamily
                font.pixelSize: th.sizeCaption
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: th.borderSubtle }

        // Salvar / Cancelar
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: th.spacingXl
            Layout.topMargin: th.spacingMd
            Layout.bottomMargin: th.spacingMd

            Item { Layout.fillWidth: true }

            Button {
                text: "Salvar"
                onClicked: root._save()
                leftPadding: 20; rightPadding: 20; topPadding: 7; bottomPadding: 7
                background: Rectangle {
                    radius: th.radiusSharp
                    color: parent.hovered ? th.accentHover : th.accentDefault
                    border.width: 0
                    Behavior on color { ColorAnimation { duration: th.durationFast } }
                }
                contentItem: Text {
                    text: parent.text
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                    font.weight: th.weightSemiBold
                    color: th.textOnAccent
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                text: "Cancelar"
                onClicked: root.reject()
                leftPadding: 20; rightPadding: 20; topPadding: 7; bottomPadding: 7
                background: Rectangle {
                    radius: th.radiusSharp
                    color: parent.hovered ? th.bgElevated : "transparent"
                    border.color: parent.hovered ? th.borderDefault : th.borderSubtle
                    border.width: 1
                    Behavior on border.color { ColorAnimation { duration: th.durationFast } }
                    Behavior on color        { ColorAnimation { duration: th.durationFast } }
                }
                contentItem: Text {
                    text: parent.text
                    font.family: th.fontFamily
                    font.pixelSize: th.sizeBody
                    color: th.textTertiary
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    ListModel { id: promptsModel }

    PromptEditDialog {
        id: promptEditDlg
        onAccepted: {
            let lbl = promptEditDlg.getLabelText()
            let txt = promptEditDlg.getPromptText()
            if (root._editingIndex === -1) {
                promptsModel.append({ id: lbl.toLowerCase().replace(/[^a-z0-9]/g, "_"), label: lbl, text: txt })
            } else {
                let existing = promptsModel.get(root._editingIndex)
                promptsModel.set(root._editingIndex, { id: existing.id, label: lbl, text: txt })
            }
        }
    }

    Connections {
        target: backend
        function onSettingsError(msg) {
            saveError.text = msg
            saveError.visible = true
        }
        function onSettingsSaved() {
            saveOk.visible = true
            closeTimer.restart()
        }
    }

    // Mantém a confirmação visível um instante antes de fechar.
    Timer {
        id: closeTimer
        interval: 1200
        onTriggered: root.accept()
    }

    function _loadSettings() {
        removeWarning.visible = false
        saveError.visible = false
        saveOk.visible = false
        let settings = backend.getSettings()
        vaultField.text = settings.obsidian_vault_path || ""
        simpField.text  = settings.simpmusic_path || ""
        simpAutostartSwitch.checked = settings.simpmusic_autostart !== false
        playlistUrlField.text = settings.music_playlist_url || ""
        reduceMotionSwitch.checked = settings.reduce_motion || false
        discordSwitch.checked = settings.discord_presence || false
        discordClientIdField.text = settings.discord_client_id || ""
        let bi = root._backendValues.indexOf(settings.processor_backend || "notebooklm")
        backendCombo.currentIndex = bi >= 0 ? bi : 0
        geminiKeyField.text    = settings.gemini_api_key || ""
        localEndpointField.text = settings.local_endpoint || ""
        root._geminiModel      = settings.gemini_model || ""
        promptsModel.clear()
        let prompts = settings.prompts || []
        for (let i = 0; i < prompts.length; i++) {
            let p = prompts[i]
            promptsModel.append({ id: p.id || "", label: p.label, text: p.text })
        }
        if (promptsModel.count > 0) promptList.currentIndex = 0
    }

    function _save() {
        saveError.visible = false
        saveOk.visible = false
        let prompts = []
        for (let i = 0; i < promptsModel.count; i++) {
            let p = promptsModel.get(i)
            prompts.push({ id: p.id, label: p.label, text: p.text })
        }
        // Sucesso → backend emite settingsSaved (mostra confirmação + fecha);
        // falha → settingsError (mostra erro, mantém o dialog aberto).
        backend.saveSettings({
            obsidian_vault_path: vaultField.text,
            simpmusic_path: simpField.text,
            simpmusic_autostart: simpAutostartSwitch.checked,
            music_playlist_url: playlistUrlField.text,
            reduce_motion: reduceMotionSwitch.checked,
            discord_presence: discordSwitch.checked,
            discord_client_id: discordClientIdField.text,
            processor_backend: root._backendValues[backendCombo.currentIndex],
            gemini_api_key: geminiKeyField.text,
            gemini_model: root._geminiModel,
            local_endpoint: localEndpointField.text,
            prompts: prompts
        })
    }
}

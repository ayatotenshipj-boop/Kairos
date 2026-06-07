import logging
import re
from copy import deepcopy
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from kairos.config import config as cfg

logger = logging.getLogger(__name__)


def _label_to_id(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "_", label.lower().strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "prompt"


class PromptEditDialog(QDialog):
    """Dialog simples para criar ou editar um prompt."""

    def __init__(self, parent=None, label: str = "", text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Editar prompt" if label else "Novo prompt")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui(label, text)

    def _build_ui(self, label: str, text: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Label:"))
        self.label_input = QLineEdit(label)
        self.label_input.setPlaceholderText("Ex: Conceitos-chave")
        layout.addWidget(self.label_input)

        layout.addWidget(QLabel("Texto do prompt:"))
        self.text_input = QTextEdit()
        self.text_input.setPlainText(text)
        self.text_input.setMinimumHeight(120)
        layout.addWidget(self.text_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_ok(self):
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Atenção", "O label do prompt não pode estar vazio.")
            return
        if not self.text_input.toPlainText().strip():
            QMessageBox.warning(self, "Atenção", "O texto do prompt não pode estar vazio.")
            return
        self.accept()

    def get_values(self) -> tuple[str, str]:
        return self.label_input.text().strip(), self.text_input.toPlainText().strip()


class SettingsDialog(QDialog):
    """Janela de configurações: caminhos e prompts editáveis."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._config = cfg.load()
        self._prompts: list[dict] = deepcopy(self._config.get("prompts", []))
        self._path_fields: dict[str, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(self._section_label("Caminhos"))
        layout.addLayout(self._path_row("Vault do Obsidian:", "obsidian_vault_path", directory=True))
        layout.addLayout(self._path_row("Simpmusic:", "simpmusic_path", directory=False))

        layout.addWidget(self._section_label("Prompts"))
        self.prompt_list = QListWidget()
        self.prompt_list.setObjectName("promptList")
        for p in self._prompts:
            self.prompt_list.addItem(p["label"])
        layout.addWidget(self.prompt_list)

        prompt_btns = QHBoxLayout()
        for label, slot in (("Adicionar", self._on_add), ("Editar", self._on_edit), ("Remover", self._on_remove)):
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            prompt_btns.addWidget(btn)
        prompt_btns.addStretch()
        layout.addLayout(prompt_btns)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("Salvar")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(save_btn)
        bottom.addWidget(cancel_btn)
        layout.addLayout(bottom)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sidebarHeader")
        return lbl

    def _path_row(self, label: str, key: str, directory: bool) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        field = QLineEdit(str(self._config.get(key, "") or ""))
        self._path_fields[key] = field
        row.addWidget(field, 1)
        browse_btn = QPushButton("Procurar")
        browse_btn.clicked.connect(lambda checked, k=key, d=directory: self._browse(k, d))
        row.addWidget(browse_btn)
        return row

    def _browse(self, key: str, directory: bool):
        field = self._path_fields[key]
        current = field.text().strip()
        start = current if current and Path(current).exists() else str(Path.home())
        if directory:
            path = QFileDialog.getExistingDirectory(self, "Selecionar pasta", start)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo", start)
        if path:
            field.setText(path)

    def _on_add(self):
        dialog = PromptEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            label, text = dialog.get_values()
            self._prompts.append({"id": _label_to_id(label), "label": label, "text": text})
            self.prompt_list.addItem(label)

    def _on_edit(self):
        idx = self.prompt_list.currentRow()
        if idx < 0:
            return
        p = self._prompts[idx]
        dialog = PromptEditDialog(self, label=p["label"], text=p["text"])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            label, text = dialog.get_values()
            self._prompts[idx] = {"id": p["id"], "label": label, "text": text}
            self.prompt_list.item(idx).setText(label)

    def _on_remove(self):
        idx = self.prompt_list.currentRow()
        if idx < 0:
            return
        if len(self._prompts) <= 1:
            QMessageBox.warning(self, "Atenção", "É necessário ter pelo menos um prompt.")
            return
        self._prompts.pop(idx)
        self.prompt_list.takeItem(idx)

    def _on_save(self):
        vault_path = self._path_fields["obsidian_vault_path"].text().strip()
        if not vault_path:
            QMessageBox.warning(
                self,
                "Atenção",
                "O caminho do vault do Obsidian está vazio.\n"
                "Algumas funções não vão funcionar sem ele.",
            )

        self._config["obsidian_vault_path"] = vault_path
        self._config["simpmusic_path"] = self._path_fields["simpmusic_path"].text().strip()
        self._config["prompts"] = self._prompts

        try:
            cfg.save(self._config)
            self.accept()
        except RuntimeError as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            QMessageBox.critical(self, "Erro ao salvar", str(e))

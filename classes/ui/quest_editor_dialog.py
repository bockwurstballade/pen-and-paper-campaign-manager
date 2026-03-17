import os
import uuid
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
)

from classes.core.data_manager import DataManager
from classes.ui.image_selector_widget import ImageSelectorWidget


class QuestEditorDialog(QDialog):
    def __init__(self, parent=None, campaign_id: Optional[str] = None, quest_data: Optional[Dict[str, Any]] = None, file_path: Optional[str] = None):
        super().__init__(parent)

        self.setWindowTitle("Quest erstellen / bearbeiten")
        self.setMinimumSize(700, 650)
        self.resize(850, 750)

        self.loaded_file = file_path
        self.campaign_id = campaign_id
        self.quest_id = str(uuid.uuid4())
        self._current_image_filename = None

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Titelbild
        self.image_widget = ImageSelectorWidget(self, placeholder_text="Kein Titelbild verfügbar.")
        main_layout.addWidget(self.image_widget)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titel der Quest …")

        self.questgiver_input = QLineEdit()
        self.questgiver_input.setPlaceholderText("Questgeber …")

        self.assigned_to_input = QLineEdit()
        self.assigned_to_input.setPlaceholderText("Vergeben an …")

        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("Status (frei) …")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Beschreibung …")
        self.description_input.setFixedHeight(170)

        self.goals_input = QTextEdit()
        self.goals_input.setPlaceholderText("Ziele …")
        self.goals_input.setFixedHeight(170)

        form_layout.addRow("Titel:", self.title_input)
        form_layout.addRow("Questgeber:", self.questgiver_input)
        form_layout.addRow("Vergeben an:", self.assigned_to_input)
        form_layout.addRow("Status:", self.status_input)
        form_layout.addRow("Beschreibung:", self.description_input)
        form_layout.addRow("Ziele:", self.goals_input)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Quest speichern")
        self.save_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.save_btn.clicked.connect(self.save_quest)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        if quest_data:
            self.load_data(quest_data)

    def load_data(self, data: Dict[str, Any]) -> None:
        self.quest_id = data.get("id", self.quest_id)
        self.campaign_id = data.get("campaign_id", self.campaign_id)

        self.title_input.setText(data.get("title", ""))
        self.questgiver_input.setText(data.get("questgiver", ""))
        self.assigned_to_input.setText(data.get("assigned_to", ""))
        self.status_input.setText(data.get("status", ""))
        self.description_input.setPlainText(data.get("description", "") or "")
        self.goals_input.setPlainText(data.get("goals", "") or "")

        self._current_image_filename = data.get("image_filename")
        if self.loaded_file:
            quest_dir = os.path.dirname(self.loaded_file)
            self.image_widget.set_existing_image(folder_path=quest_dir, filename=self._current_image_filename)
        else:
            self.image_widget.clear()

    def get_data(self) -> Dict[str, Any]:
        return {
            "id": self.quest_id,
            "campaign_id": self.campaign_id,
            "title": self.title_input.text().strip(),
            "questgiver": self.questgiver_input.text().strip(),
            "assigned_to": self.assigned_to_input.text().strip(),
            "status": self.status_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "goals": self.goals_input.toPlainText().strip(),
        }

    def save_quest(self) -> None:
        data = self.get_data()

        if not data["campaign_id"]:
            QMessageBox.warning(self, "Fehler", "Bitte zuerst eine Kampagne auswählen.")
            return
        if not data["title"]:
            QMessageBox.warning(self, "Fehler", "Bitte einen Titel für die Quest eingeben.")
            return

        try:
            if not self.image_widget.selected_source_path and self._current_image_filename:
                data["image_filename"] = self._current_image_filename

            saved_path = DataManager.save_quest(
                data,
                file_path=self.loaded_file,
                image_source_path=self.image_widget.selected_source_path,
            )
            self.loaded_file = saved_path
            self._current_image_filename = data.get("image_filename")

            QMessageBox.information(self, "Erfolg", "Quest erfolgreich gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")


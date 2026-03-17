import uuid
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
    QPushButton, QMessageBox, QHBoxLayout, QTextEdit
)

from classes.core.data_manager import DataManager
from classes.ui.image_selector_widget import ImageSelectorWidget

class CampaignCreationDialog(QDialog):
    def __init__(self, parent=None, campaign_data=None, file_path=None):
        super().__init__(parent)
        self.setWindowTitle("Kampagne erstellen / bearbeiten")
        self.setMinimumWidth(400)

        self.loaded_file = file_path
        self.campaign_id = str(uuid.uuid4())
        self._current_image_filename = None
        
        # --- Layout ---
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Bild
        self.image_widget = ImageSelectorWidget(self, placeholder_text="Kein Bild verfügbar.")
        main_layout.addWidget(self.image_widget)

        # Input Fields
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Name der Kampagne...")
        
        self.ruleset_input = QLineEdit()
        self.ruleset_input.setPlaceholderText("z.B. D&D 5e, Cthulhu, Das Schwarze Auge...")

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "One-Shot",
            "Kampagne",
            "Sandbox",
            "West March"
        ])

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Neutrale Beschreibung der Kampagne …")
        self.description_input.setFixedHeight(140)

        self.teaser_input = QTextEdit()
        self.teaser_input.setPlaceholderText("Teaser-Text (z. B. für Discord) …")
        self.teaser_input.setFixedHeight(140)

        form_layout.addRow("Titel:", self.title_input)
        form_layout.addRow("Regelwerk:", self.ruleset_input)
        form_layout.addRow("Art:", self.type_combo)
        form_layout.addRow("Beschreibung:", self.description_input)
        form_layout.addRow("Teaser:", self.teaser_input)

        main_layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Kampagne speichern")
        self.save_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.save_btn.clicked.connect(self.save_campaign)
        
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        # Populate if loaded
        if campaign_data:
            self.load_data(campaign_data)

    def load_data(self, data: dict):
        self.campaign_id = data.get("id", self.campaign_id)
        self.title_input.setText(data.get("title", ""))
        self.ruleset_input.setText(data.get("ruleset", ""))
        self.description_input.setPlainText(data.get("description", "") or "")
        self.teaser_input.setPlainText(data.get("teaser", "") or "")

        # Bild laden
        self._current_image_filename = data.get("image_filename")
        if self.loaded_file:
            camp_dir = os.path.dirname(self.loaded_file)
            self.image_widget.set_existing_image(folder_path=camp_dir, filename=self._current_image_filename)
        else:
            self.image_widget.clear()
        
        c_type = data.get("type", "Kampagne")
        index = self.type_combo.findText(c_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

    def get_data(self) -> dict:
        return {
            "id": self.campaign_id,
            "title": self.title_input.text().strip(),
            "ruleset": self.ruleset_input.text().strip(),
            "type": self.type_combo.currentText(),
            "description": self.description_input.toPlainText().strip(),
            "teaser": self.teaser_input.toPlainText().strip(),
        }

    def save_campaign(self):
        data = self.get_data()
        
        if not data["title"]:
            QMessageBox.warning(self, "Fehler", "Bitte einen Titel für die Kampagne eingeben.")
            return

        try:
            if not self.image_widget.selected_source_path and self._current_image_filename:
                data["image_filename"] = self._current_image_filename

            saved_path = DataManager.save_campaign(
                data,
                self.loaded_file,
                image_source_path=self.image_widget.selected_source_path,
            )
            self.loaded_file = saved_path
            self._current_image_filename = data.get("image_filename")
            QMessageBox.information(self, "Erfolg", "Kampagne erfolgreich gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")

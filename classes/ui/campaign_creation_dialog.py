import uuid
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
    QPushButton, QMessageBox, QHBoxLayout
)

from classes.core.data_manager import DataManager

class CampaignCreationDialog(QDialog):
    def __init__(self, parent=None, campaign_data=None, file_path=None):
        super().__init__(parent)
        self.setWindowTitle("Kampagne erstellen / bearbeiten")
        self.setMinimumWidth(400)

        self.loaded_file = file_path
        self.campaign_id = str(uuid.uuid4())
        
        # --- Layout ---
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

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

        form_layout.addRow("Titel:", self.title_input)
        form_layout.addRow("Regelwerk:", self.ruleset_input)
        form_layout.addRow("Art:", self.type_combo)

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
        
        c_type = data.get("type", "Kampagne")
        index = self.type_combo.findText(c_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

    def get_data(self) -> dict:
        return {
            "id": self.campaign_id,
            "title": self.title_input.text().strip(),
            "ruleset": self.ruleset_input.text().strip(),
            "type": self.type_combo.currentText()
        }

    def save_campaign(self):
        data = self.get_data()
        
        if not data["title"]:
            QMessageBox.warning(self, "Fehler", "Bitte einen Titel für die Kampagne eingeben.")
            return

        try:
            saved_path = DataManager.save_campaign(data, self.loaded_file)
            self.loaded_file = saved_path
            QMessageBox.information(self, "Erfolg", "Kampagne erfolgreich gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")

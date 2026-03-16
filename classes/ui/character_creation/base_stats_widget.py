from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QComboBox, QTextEdit, QLabel, QHBoxLayout, QPushButton
from typing import Dict, Any

from classes.core.data_manager import DataManager
from classes.ui.campaign_creation_dialog import CampaignCreationDialog

class BaseStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_form = QFormLayout(self)
        self.setStyleSheet("margin: 0; padding: 0;") # Avoid double margins

        self.role_input = QComboBox()
        self.role_input.addItems(["Spielercharakter", "NSC / Gegner"])
        
        # --- Campaign Selection ---
        self.campaign_combo = QComboBox()
        self.campaign_data_map = {} # Maps display text to UUID
        
        self.new_campaign_btn = QPushButton("+ Neue Kampagne")
        self.new_campaign_btn.clicked.connect(self.create_new_campaign)
        
        camp_layout = QHBoxLayout()
        camp_layout.addWidget(self.campaign_combo)
        camp_layout.addWidget(self.new_campaign_btn)
        
        self.name_input = QLineEdit()
        self.class_input = QLineEdit()
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Männlich", "Weiblich", "Divers"])
        
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Zahl eingeben")
        
        self.hitpoints_input = QLineEdit()
        self.hitpoints_input.setPlaceholderText("Zahl eingeben")
        # Das Signal verbinden wir später von außen oder cachen base hier
        self.hitpoints_input.textChanged.connect(self.update_base_hitpoints)
        self.base_hitpoints = 0
        
        self.build_input = QLineEdit()
        self.religion_input = QLineEdit()
        self.occupation_input = QLineEdit()
        
        self.marital_status_input = QComboBox()
        self.marital_status_input.addItems(["Ledig", "Verheiratet", "Verwitwet"])
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Hier kannst du eine Hintergrundgeschichte oder Notizen eintragen...")
        self.description_input.setFixedHeight(120)
        
        self.base_damage_input = QLineEdit()
        self.base_damage_input.setPlaceholderText("z.B. 1W6 oder 1W6+2")

        # Layout befüllen
        self.base_form.addRow("Typ:", self.role_input)
        self.base_form.addRow("Kampagne:", camp_layout)
        self.base_form.addRow("Name:", self.name_input)
        self.base_form.addRow("Klasse:", self.class_input)
        self.base_form.addRow("Geschlecht:", self.gender_input)
        self.base_form.addRow("Alter:", self.age_input)
        self.base_form.addRow("Lebenspunkte:", self.hitpoints_input)
        self.base_form.addRow("Statur:", self.build_input)
        self.base_form.addRow("Religion:", self.religion_input)
        self.base_form.addRow("Beruf:", self.occupation_input)
        self.base_form.addRow("Familienstand:", self.marital_status_input)
        self.base_form.addRow("Grundschaden:", self.base_damage_input)
        self.base_form.addRow("Beschreibung:", self.description_input)

        # Kampagnen sofort laden (bei neuem Charakter wird load_data() nicht aufgerufen)
        self.load_campaigns()

    def update_base_hitpoints(self):
        try:
            self.base_hitpoints = int(self.hitpoints_input.text())
        except ValueError:
            self.base_hitpoints = 0

    def load_campaigns(self):
        self.campaign_combo.clear()
        self.campaign_data_map.clear()
        
        self.campaign_combo.addItem("Keine Kampagne", None)
        
        campaigns = DataManager.get_all_campaigns()
        for c in campaigns:
            display = c["display"]
            c_id = c["data"].get("id")
            self.campaign_combo.addItem(display, c_id)
            self.campaign_data_map[c_id] = display

    def create_new_campaign(self):
        dlg = CampaignCreationDialog(self)
        if dlg.exec():
            # Refresh the list
            self.load_campaigns()
            
            # Select the newly created one if possible
            new_id = dlg.campaign_id
            if new_id in self.campaign_data_map:
                idx = self.campaign_combo.findData(new_id)
                if idx >= 0:
                    self.campaign_combo.setCurrentIndex(idx)

    def load_data(self, character: Dict[str, Any]):
        self.load_campaigns()
        
        campaign_id = character.get("campaign_id")
        if campaign_id and campaign_id in self.campaign_data_map:
            idx = self.campaign_combo.findData(campaign_id)
            if idx >= 0:
                self.campaign_combo.setCurrentIndex(idx)
        else:
            self.campaign_combo.setCurrentIndex(0)

        role = character.get("role", "pc")
        if role == "npc":
            self.role_input.setCurrentText("NSC / Gegner")
        else:
            self.role_input.setCurrentText("Spielercharakter")
            
        self.name_input.setText(character.get("name", ""))
        self.class_input.setText(character.get("class", ""))
        self.gender_input.setCurrentText(character.get("gender", "Männlich"))
        self.age_input.setText(str(character.get("age", "")))
        
        self.base_hitpoints = int(character.get("hitpoints", 0))
        self.hitpoints_input.setText(str(self.base_hitpoints))
        
        self.build_input.setText(character.get("build", ""))
        self.religion_input.setText(character.get("religion", ""))
        self.occupation_input.setText(character.get("occupation", ""))
        self.marital_status_input.setCurrentText(character.get("marital_status", "Ledig"))
        self.base_damage_input.setText(character.get("base_damage", ""))
        self.description_input.setPlainText(character.get("description", ""))

    def get_data(self) -> Dict[str, Any]:
        age_str = self.age_input.text().strip()
        age = int(age_str) if age_str else 0
        
        campaign_id = self.campaign_combo.currentData()
        
        return {
            "campaign_id": campaign_id,
            "name": self.name_input.text().strip(),
            "role": "pc" if self.role_input.currentText().startswith("Spieler") else "npc",
            "char_class": self.class_input.text(),
            "gender": self.gender_input.currentText(),
            "age": age,
            "hitpoints": self.base_hitpoints,
            "base_damage": self.base_damage_input.text().strip(),
            "build": self.build_input.text(),
            "religion": self.religion_input.text().strip(),
            "occupation": self.occupation_input.text().strip(),
            "marital_status": self.marital_status_input.currentText(),
            "description": self.description_input.toPlainText().strip()
        }

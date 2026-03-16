from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QPushButton, QLabel
from typing import Dict, Any

from classes.ui.character_creation.skills import CharacterCreationDialogSkills
from classes.ui.ui_utils import style_groupbox

class SkillsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Diese Handler Klasse hat vorher direkt auf dem Hauptdialog operiert.
        # Jetzt operiert sie auf *diesem* Widget.
        self.skills_handler = CharacterCreationDialogSkills(self)
        
        # Strukturen für das State-Tracking (früher im Hauptdialog)
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {}
        self.skill_end_labels = {}
        self.category_labels = {}
        self.inspiration_labels = {}
        self.group_boxes = {}
        self.form_layouts = {}
        self.add_buttons = {}
        self.total_points_label = QLabel("Verbleibende Punkte: 400")
        
        # Für MissionEffects tracking (wir kopieren das Verhalten aus dem alten Dialog)
        # Die eigentlichen Modifikatoren / Effekte könnten später woanders berechnet werden,
        # aber wir halten den Zustand hier.
        self.base_values = {
            "Kategorien": {},        # z. B. {"Handeln": 5}
            "Geistesblitzpunkte": {},# z. B. {"Wissen": 1}
            "Fertigkeiten": {}       # z. B. {"Laufen": 50}
        }

        # UI initialisieren
        for category in self.skills:
            self.group_boxes[category] = QGroupBox(category)
            style_groupbox(self.group_boxes[category])

            self.form_layouts[category] = QFormLayout()
            self.skill_inputs[category] = {}

            vbox = QVBoxLayout()
            vbox.addLayout(self.form_layouts[category])

            self.add_buttons[category] = QPushButton("+ Neue Fähigkeit")
            # lambda mit default param cat=category
            self.add_buttons[category].clicked.connect(lambda _, cat=category: self.skills_handler.add_skill(cat))
            vbox.addWidget(self.add_buttons[category])

            self.group_boxes[category].setLayout(vbox)
            self.layout.addWidget(self.group_boxes[category])

            self.category_labels[category] = QLabel(f"{category}-Wert: 0")
            self.inspiration_labels[category] = QLabel(f"Geistesblitzpunkte ({category}): 0")
            self.layout.addWidget(self.category_labels[category])
            self.layout.addWidget(self.inspiration_labels[category])

        self.layout.addWidget(self.total_points_label)


    def load_data(self, character: Dict[str, Any]):
        # Skills aufräumen
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {"Handeln": {}, "Wissen": {}, "Soziales": {}}
        self.skill_end_labels = {"Handeln": {}, "Wissen": {}, "Soziales": {}}

        # Alte Layouts leeren
        for category in self.form_layouts:
            layout = self.form_layouts[category]
            while layout.rowCount() > 0:
                layout.removeRow(0)

        # Fähigkeiten wiederherstellen
        for category, skills in character.get("skills", {}).items():
            if category not in self.skills:
                # Fallback für zukünftige Kategorien
                self.skills[category] = []
                self.skill_inputs[category] = {}
                self.skill_end_labels[category] = {}
                continue # Ohne GroupBox/Layout rendert das zwar nicht (müsste man via create_category implementieren), ist aber safe

            for skill, value in skills.items():
                self.skills[category].append(skill)
                
                # Wir bauen die UI-Zeile indirekt oder direkt nach (siehe skills.py)
                # Da skills.py keine load Funktion hat, bauen wir es hier auf.
                # Wichtig: PyQt Imports
                from PyQt6.QtWidgets import QLineEdit, QHBoxLayout
                input_field = QLineEdit(str(value))
                input_field.textChanged.connect(self.skills_handler.update_points)

                end_label = QLabel("Endwert: 0")
                self.skill_end_labels[category][skill] = end_label

                remove_button = QPushButton("– Entfernen")
                remove_button.clicked.connect(lambda _, cat=category, sk=skill: self.skills_handler.remove_skill(cat, sk))

                h_layout = QHBoxLayout()
                h_layout.addWidget(input_field)
                h_layout.addWidget(end_label)
                h_layout.addWidget(remove_button)
                
                self.form_layouts[category].addRow(f"{skill}:", h_layout)
                self.skill_inputs[category][skill] = input_field

        # Update values
        self.skills_handler.update_points()

    def get_data(self) -> Dict[str, Dict[str, int]]:
        # Liefer ein rohes dict der Skills für den CharacterBuilder zurück
        skills_raw = {}
        for category in self.skills:
            skills_raw[category] = {}
            for skill, input_field in self.skill_inputs[category].items():
                value = input_field.text()
                skills_raw[category][skill] = int(value) if value else 0
        return skills_raw

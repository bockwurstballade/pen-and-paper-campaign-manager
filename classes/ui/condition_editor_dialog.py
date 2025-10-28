
# benötigte Imports
import os
import json
import uuid
## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

class ConditionEditorDialog(QDialog):
    def __init__(self, parent=None, available_skill_targets=None,
                 available_category_targets=None,
                 available_inspiration_targets=None):
        super().__init__(parent)

        self.setWindowTitle("Zustand bearbeiten / erstellen")
        self.setGeometry(250, 250, 450, 400)

        self.loaded_file = None
        self.condition_id = None

        # Falls nichts übergeben wurde: leere Listen
        self.available_skill_targets = available_skill_targets or []
        self.available_category_targets = available_category_targets or []
        self.available_inspiration_targets = available_inspiration_targets or []

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.description_input = QLineEdit()

        self.effect_type_input = QComboBox()
        self.effect_type_input.addItems([
            "keine Auswirkung",
            "missionsweit",
            "rundenbasiert"
        ])

        self.effect_target_input = QComboBox()
        self.rebuild_effect_target_options()

        self.effect_value_input = QLineEdit()
        self.effect_value_input.setPlaceholderText("z. B. -20 oder +15")

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Beschreibung:", self.description_input)
        form_layout.addRow("Auswirkungstyp:", self.effect_type_input)
        form_layout.addRow("Ziel der Auswirkung:", self.effect_target_input)
        form_layout.addRow("Modifikator:", self.effect_value_input)

        main_layout.addLayout(form_layout)

        save_button = QPushButton("Zustand speichern")
        save_button.clicked.connect(self.save_condition)
        main_layout.addWidget(save_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def rebuild_effect_target_options(self):
        current = self.effect_target_input.currentText() if hasattr(self, "effect_target_input") else ""

        targets = ["(kein Ziel / n/a)", "Lebenspunkte"]

        targets.extend(self.available_skill_targets)
        targets.extend(self.available_category_targets)
        targets.extend(self.available_inspiration_targets)

        targets.append("Benutzerdefiniert ...")

        print("DEBUG targets im Dialog:", targets)

        self.effect_target_input.clear()
        self.effect_target_input.addItems(targets)

        if current in targets:
            self.effect_target_input.setCurrentText(current)


    def ask_for_custom_target_if_needed(self):
        """
        Wenn der User 'Benutzerdefiniert ...' gewählt hat, fragen wir ihn nach freiem Text.
        Gibt den finalen target-String zurück.
        """
        choice = self.effect_target_input.currentText()
        if choice == "Benutzerdefiniert ...":
            custom_text, ok = QInputDialog.getText(self, "Eigenes Ziel", "Auf welches Attribut wirkt sich der Zustand aus?")
            if not ok:
                return "(kein Ziel / n/a)"
            return custom_text.strip() if custom_text.strip() else "(kein Ziel / n/a)"
        return choice

    def load_condition_data(self, cond_data, file_path):
        """
        Lädt einen bestehenden Zustand in den Dialog.
        cond_data ist ein einzelnes Zustands-Dict (mit id, name, ...)
        """
        self.loaded_file = file_path
        self.condition_id = cond_data.get("id", str(uuid.uuid4()))

        self.name_input.setText(cond_data.get("name", ""))
        self.description_input.setText(cond_data.get("description", ""))

        effect_type = cond_data.get("effect_type", "keine Auswirkung")
        if effect_type not in ["keine Auswirkung", "missionsweit", "rundenbasiert"]:
            effect_type = "keine Auswirkung"
        self.effect_type_input.setCurrentText(effect_type)

        # Ziel nutzen (falls nicht in Liste, hängen wir es temporär rein)
        target_loaded = cond_data.get("effect_target", "(kein Ziel / n/a)")
        self.rebuild_effect_target_options()
        if target_loaded and target_loaded not in [self.effect_target_input.itemText(i) for i in range(self.effect_target_input.count())]:
            self.effect_target_input.addItem(target_loaded)
        self.effect_target_input.setCurrentText(target_loaded)

        self.effect_value_input.setText(str(cond_data.get("effect_value", 0)))

    def save_condition(self):
        """
        Speichert/aktualisiert den Zustand in conditions.json.
        """
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein.")
            return

        description = self.description_input.text().strip()

        effect_type = self.effect_type_input.currentText()

        # Zielattribut holen (ggf. custom abfragen)
        target = self.ask_for_custom_target_if_needed()

        # Wert parse-int (falls leer -> 0)
        value_str = self.effect_value_input.text().strip()
        if value_str == "":
            effect_value = 0
        else:
            try:
                effect_value = int(value_str)
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Der Modifikator muss eine ganze Zahl sein (z. B. -10 oder +5).")
                return

        # UUID setzen/festhalten
        if not self.condition_id:
            self.condition_id = str(uuid.uuid4())

        cond_obj = {
            "id": self.condition_id,
            "name": name,
            "description": description,
            "effect_type": effect_type,
            "effect_target": target if effect_type != "keine Auswirkung" else "",
            "effect_value": effect_value if effect_type != "keine Auswirkung" else 0
        }

        target_file = self.loaded_file if self.loaded_file else "conditions.json"

        # existierende Datei laden
        cond_list = []
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "conditions" in data and isinstance(data["conditions"], list):
                        cond_list = data["conditions"]
            except Exception:
                pass

        # Zustand einfügen / ersetzen
        replaced = False
        for i, existing in enumerate(cond_list):
            if existing.get("id") == self.condition_id:
                cond_list[i] = cond_obj
                replaced = True
                break
        if not replaced:
            cond_list.append(cond_obj)

        # zurückschreiben
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump({"conditions": cond_list}, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Erfolg", f"Zustand '{name}' wurde gespeichert!")
        self.accept()


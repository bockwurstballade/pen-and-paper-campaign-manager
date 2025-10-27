import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog
)

from PyQt6.QtCore import Qt
from decimal import Decimal, ROUND_HALF_UP

def kaufmaennisch_runden(x):
    """Rundet nach kaufmännischer Regel: ab 0.5 wird aufgerundet."""
    return int(Decimal(str(round(x, 3))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

class AttributeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Eigenschaft")
        self.setGeometry(200, 200, 300, 150)

        layout = QVBoxLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Attribut-Name")
        self.value_input = QLineEdit(self)
        self.value_input.setPlaceholderText("Attribut-Wert")
        layout.addWidget(QLabel("Attribut-Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Attribut-Wert:"))
        layout.addWidget(self.value_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Abbrechen", self)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def get_attribute(self):
        name = self.name_input.text().strip()
        value = self.value_input.text().strip()
        return name, value if name and value else (None, None)

class CharacterCreationDialog(QDialog):

    def __init__(self, parent=None):
        self.loaded_file = None  # Wird gesetzt, wenn Charakter geladen wurde

        super().__init__(parent)
        self.setWindowTitle("Neuen Charakter erstellen")
        self.setGeometry(150, 150, 450, 700)

        # Hauptlayout
        main_layout = QVBoxLayout()

        # Basisdaten-Formular
        self.base_form = QFormLayout()
        self.name_input = QLineEdit()
        self.class_input = QComboBox()
        self.class_input.addItems(["Krieger", "Magier", "Dieb"])
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Männlich", "Weiblich", "Divers"])
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Zahl eingeben")
        self.hitpoints_input = QLineEdit()
        self.hitpoints_input.setPlaceholderText("Zahl eingeben")
        self.build_input = QComboBox()
        self.build_input.addItems(["Schlank", "Durchschnittlich", "Kräftig"])
        self.religion_input = QLineEdit()
        self.occupation_input = QLineEdit()
        self.marital_status_input = QComboBox()
        self.marital_status_input.addItems(["Ledig", "Verheiratet", "Verwitwet"])

        self.base_form.addRow("Name:", self.name_input)
        self.base_form.addRow("Klasse:", self.class_input)
        self.base_form.addRow("Geschlecht:", self.gender_input)
        self.base_form.addRow("Alter:", self.age_input)
        self.base_form.addRow("Lebenspunkte:", self.hitpoints_input)
        self.base_form.addRow("Statur:", self.build_input)
        self.base_form.addRow("Religion:", self.religion_input)
        self.base_form.addRow("Beruf:", self.occupation_input)
        self.base_form.addRow("Familienstand:", self.marital_status_input)

        main_layout.addLayout(self.base_form)

        # Fähigkeiten
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {}
        self.skill_end_labels = {}
        self.category_labels = {}
        self.inspiration_labels = {}
        self.group_boxes = {}
        self.form_layouts = {}
        self.add_buttons = {}
        self.total_points_label = QLabel("Verbleibende Punkte: 400")
        self.total_points = 400

        for category in self.skills:
            self.group_boxes[category] = QGroupBox(category)
            self.form_layouts[category] = QFormLayout()
            self.skill_inputs[category] = {}
            self.group_boxes[category].setLayout(QVBoxLayout())
            self.group_boxes[category].layout().addLayout(self.form_layouts[category])
            self.add_buttons[category] = QPushButton("+ Neue Fähigkeit")
            self.add_buttons[category].clicked.connect(lambda _, cat=category: self.add_skill(cat))
            self.group_boxes[category].layout().addWidget(self.add_buttons[category])
            main_layout.addWidget(self.group_boxes[category])
            self.category_labels[category] = QLabel(f"{category}-Wert: 0")
            self.inspiration_labels[category] = QLabel(f"Geistesblitzpunkte ({category}): 0")
            main_layout.addWidget(self.category_labels[category])
            main_layout.addWidget(self.inspiration_labels[category])

        main_layout.addWidget(self.total_points_label)

        # Items
        self.items_group = QGroupBox("Items")
        self.items_layout = QVBoxLayout()
        self.item_groups = {}
        self.item_add_button = QPushButton("+ Neues Item")
        self.item_add_button.clicked.connect(self.add_item)
        self.items_layout.addWidget(self.item_add_button)
        self.items_group.setLayout(self.items_layout)
        main_layout.addWidget(self.items_group)

        # Speichern-Button
        save_button = QPushButton("Charakter speichern")
        save_button.clicked.connect(self.save_character)
        main_layout.addWidget(save_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def add_skill(self, category):
        skill_name, ok = QInputDialog.getText(self, f"Neue Fähigkeit für {category}", "Fähigkeitsname:")
        if not ok or not skill_name.strip():
            QMessageBox.warning(self, "Fehler", "Fähigkeitsname darf nicht leer sein.")
            return
        skill_name = skill_name.strip()
        if skill_name in self.skills[category]:
            QMessageBox.warning(self, "Fehler", f"Fähigkeit '{skill_name}' existiert bereits in {category}.")
            return

        # Fähigkeit hinzufügen
        self.skills[category].append(skill_name)
        self.skill_end_labels.setdefault(category, {})

        # Eingabefeld + Entfernen-Button + Endwert-Label
        input_field = QLineEdit()
        input_field.setPlaceholderText("0–100")
        input_field.textChanged.connect(self.update_points)

        end_label = QLabel("Endwert: 0")
        self.skill_end_labels[category][skill_name] = end_label

        remove_button = QPushButton("– Entfernen")
        remove_button.clicked.connect(lambda _, cat=category, skill=skill_name: self.remove_skill(cat, skill))

        # Layout der Zeile
        h_layout = QHBoxLayout()
        h_layout.addWidget(input_field)
        h_layout.addWidget(end_label)
        h_layout.addWidget(remove_button)

        self.skill_inputs[category][skill_name] = input_field
        self.form_layouts[category].addRow(f"{skill_name}:", h_layout)
        self.update_points()


    def remove_skill(self, category, skill_name):
        """Entfernt eine Fähigkeit aus dem Layout und den Datenstrukturen."""
        if skill_name not in self.skills[category]:
            return

        self.skills[category].remove(skill_name)
        input_field = self.skill_inputs[category].pop(skill_name)
        if skill_name in self.skill_end_labels.get(category, {}):
            del self.skill_end_labels[category][skill_name]

        # Layoutzeile im FormLayout finden und entfernen
        form_layout = self.form_layouts[category]
        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if label_item and label_item.widget() and label_item.widget().text().startswith(skill_name):
                # Widgets explizit löschen
                label_item.widget().deleteLater()
                if field_item:
                    field_widget = field_item.layout() or field_item.widget()
                    if field_widget:
                        while isinstance(field_widget, QHBoxLayout) and field_widget.count():
                            item = field_widget.takeAt(0)
                            if item.widget():
                                item.widget().deleteLater()
                        field_widget.deleteLater()
                form_layout.removeRow(i)
                break

        self.update_points()
        QMessageBox.information(self, "Erfolg", f"Fertigkeit '{skill_name}' wurde entfernt.")


    def add_item(self):
        item_name, ok = QInputDialog.getText(self, "Neues Item", "Item-Name:")
        if not ok or not item_name.strip():
            QMessageBox.warning(self, "Fehler", "Item-Name darf nicht leer sein.")
            return
        item_name = item_name.strip()
        if item_name in self.item_groups:
            QMessageBox.warning(self, "Fehler", f"Item '{item_name}' existiert bereits.")
            return

        item_group = QGroupBox(item_name)
        item_layout = QVBoxLayout()
        self.item_groups[item_name] = {"attributes": {}, "layout": item_layout, "group": item_group}
        
        attr_layout = QFormLayout()
        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addLayout(attr_layout)
        item_layout.addWidget(add_attr_button)

        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item(item))
        item_layout.addWidget(remove_button)

        item_group.setLayout(item_layout)
        self.items_layout.insertWidget(self.items_layout.count() - 1, item_group)

    def add_attribute(self, item_name):
        dialog = AttributeDialog(self)
        if dialog.exec() == 1:
            attr_name, attr_value = dialog.get_attribute()
            if not attr_name or not attr_value:
                QMessageBox.warning(self, "Fehler", "Attribut-Name und -Wert dürfen nicht leer sein.")
                return
            if attr_name in self.item_groups[item_name]["attributes"]:
                QMessageBox.warning(self, "Fehler", f"Attribut '{attr_name}' existiert bereits für {item_name}.")
                return

            self.item_groups[item_name]["attributes"][attr_name] = attr_value
            attr_layout = self.item_groups[item_name]["layout"].itemAt(0).layout()
            attr_layout.addRow(f"{attr_name}:", QLabel(attr_value))

    def remove_item(self, item_name):
        if item_name in self.item_groups:
            item_group = self.item_groups[item_name]["group"]
            self.items_layout.removeWidget(item_group)
            item_group.deleteLater()
            del self.item_groups[item_name]
            QMessageBox.information(self, "Erfolg", f"Item '{item_name}' wurde entfernt.")

    def update_points(self):
        try:
            total_used = 0
            for category in self.skills:
                category_sum = 0
                for skill, input_field in self.skill_inputs[category].items():
                    value = input_field.text()
                    if value:
                        val = int(value)
                        if 0 <= val <= 100:
                            category_sum += val
                        else:
                            input_field.setText("")
                            raise ValueError(f"{skill}: Wert muss zwischen 0 und 100 liegen.")
                # Kategorie-Wert berechnen
                category_score = kaufmaennisch_runden(category_sum / 10)
                self.category_labels[category].setText(f"{category}-Wert: {category_score}")

                # Geistesblitzpunkte berechnen
                inspiration_points = kaufmaennisch_runden(category_sum / (10 * 10))
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {inspiration_points}")

                # Endwerte für Fähigkeiten aktualisieren
                for skill, input_field in self.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    end_value = val + category_score
                    if category in self.skill_end_labels and skill in self.skill_end_labels[category]:
                        self.skill_end_labels[category][skill].setText(f"Endwert: {end_value}")

                total_used += category_sum

            remaining = 400 - total_used
            self.total_points_label.setText(f"Verbleibende Punkte: {remaining}")
            if remaining < 0:
                raise ValueError("Gesamtpunkte überschreiten 400!")

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e))


    def save_character(self):
        try:
            name = self.name_input.text().strip()
            if not name:
                raise ValueError("Name darf nicht leer sein.")
            age = int(self.age_input.text())
            if not 1 <= age <= 120:
                raise ValueError("Alter muss zwischen 1 und 120 liegen.")
            hitpoints = int(self.hitpoints_input.text())
            if not 1 <= hitpoints <= 100:
                raise ValueError("Lebenspunkte müssen zwischen 1 und 100 liegen.")
            religion = self.religion_input.text().strip()
            occupation = self.occupation_input.text().strip()
            if not religion or not occupation:
                raise ValueError("Religion und Beruf dürfen nicht leer sein.")
            total_used = 0
            skills_data = {}
            category_scores = {}
            inspiration_points = {}
            for category in self.skills:
                skills_data[category] = {}
                category_sum = 0
                for skill, input_field in self.skill_inputs[category].items():
                    value = input_field.text()
                    val = int(value) if value else 0
                    if not 0 <= val <= 100:
                        raise ValueError(f"{skill}: Wert muss zwischen 0 und 100 liegen.")
                    skills_data[category][skill] = val
                    category_sum += val
                total_used += category_sum
                category_scores[category] = kaufmaennisch_runden(category_sum / 10)
                inspiration_points[category] = kaufmaennisch_runden(category_scores[category] / 10)
            if total_used > 400:
                raise ValueError("Gesamtpunkte überschreiten 400!")
            items_data = {item_name: data["attributes"] for item_name, data in self.item_groups.items()}
        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e) if str(e) != "" else "Bitte gültige Zahlen eingeben.")
            return

        character = {
            "id": self.get_next_id(),
            "name": name,
            "class": self.class_input.currentText(),
            "gender": self.gender_input.currentText(),
            "age": age,
            "hitpoints": hitpoints,
            "build": self.build_input.currentText(),
            "religion": religion,
            "occupation": occupation,
            "marital_status": self.marital_status_input.currentText(),
            "skills": skills_data,
            "category_scores": category_scores,
            "inspiration_points": inspiration_points,
            "items": items_data
        }

        if self.loaded_file:
            with open(self.loaded_file, "w", encoding="utf-8") as f:
                json.dump(character, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Erfolg", f"Charakter '{name}' wurde aktualisiert!")
        else:
            self.save_to_json(character)
            QMessageBox.information(self, "Erfolg", f"Neuer Charakter '{name}' wurde gespeichert!")

        self.accept()

    def load_character_data(self, character, file_path):
        """Befüllt das Formular mit den Daten eines geladenen Charakters."""
        self.loaded_file = file_path

        self.name_input.setText(character.get("name", ""))
        self.class_input.setCurrentText(character.get("class", "Krieger"))
        self.gender_input.setCurrentText(character.get("gender", "Männlich"))
        self.age_input.setText(str(character.get("age", "")))
        self.hitpoints_input.setText(str(character.get("hitpoints", "")))
        self.build_input.setCurrentText(character.get("build", "Durchschnittlich"))
        self.religion_input.setText(character.get("religion", ""))
        self.occupation_input.setText(character.get("occupation", ""))
        self.marital_status_input.setCurrentText(character.get("marital_status", "Ledig"))

        # Fähigkeiten wiederherstellen
        for category, skills in character.get("skills", {}).items():
            for skill, value in skills.items():
                self.skills[category].append(skill)
                input_field = QLineEdit(str(value))
                input_field.textChanged.connect(self.update_points)

                end_label = QLabel("Endwert: 0")
                self.skill_end_labels.setdefault(category, {})[skill] = end_label

                remove_button = QPushButton("– Entfernen")
                remove_button.clicked.connect(lambda _, cat=category, skill=skill: self.remove_skill(cat, skill))

                h_layout = QHBoxLayout()
                h_layout.addWidget(input_field)
                h_layout.addWidget(end_label)
                h_layout.addWidget(remove_button)
                self.form_layouts[category].addRow(f"{skill}:", h_layout)

                self.skill_inputs[category][skill] = input_field

        # Items wiederherstellen
        for item_name, attributes in character.get("items", {}).items():
            self.item_groups[item_name] = {"attributes": {}, "layout": None, "group": None}
            item_group = QGroupBox(item_name)
            item_layout = QVBoxLayout()

            attr_layout = QFormLayout()
            for attr_name, attr_value in attributes.items():
                attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))
                self.item_groups[item_name]["attributes"][attr_name] = attr_value

            add_attr_button = QPushButton("+ Neue Eigenschaft")
            add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
            remove_button = QPushButton("- Item entfernen")
            remove_button.clicked.connect(lambda _, item=item_name: self.remove_item(item))

            item_layout.addLayout(attr_layout)
            item_layout.addWidget(add_attr_button)
            item_layout.addWidget(remove_button)
            item_group.setLayout(item_layout)

            self.items_layout.insertWidget(self.items_layout.count() - 1, item_group)
            self.item_groups[item_name]["layout"] = item_layout
            self.item_groups[item_name]["group"] = item_group

        self.update_points()


    def get_next_id(self):
        characters = self.load_characters()
        return max([char["id"] for char in characters], default=0) + 1

    def load_characters(self):
        if os.path.exists("characters.json"):
            with open("characters.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("characters", [])
        return []

    def save_to_json(self, character):
        characters = self.load_characters()
        characters.append(character)
        with open("characters.json", "w", encoding="utf-8") as f:
            json.dump({"characters": characters}, f, indent=4)

class WelcomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Charakterverwaltung - Willkommen")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        welcome_label = QLabel("Willkommen zur Charakterverwaltung!", self)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome_label)

        subtitle_label = QLabel("Verwalten Sie Ihre Pen-and-Paper-Charaktere für 'How to Be a Hero'", self)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        start_button = QPushButton("Neuen Charakter erstellen", self)
        start_button.clicked.connect(self.start_character_creation)
        layout.addWidget(start_button)

        load_button = QPushButton("Bestehenden Charakter laden", self)
        load_button.clicked.connect(self.load_character)
        layout.addWidget(load_button)

        layout.addStretch()


    def start_character_creation(self):
        dialog = CharacterCreationDialog(self)
        dialog.exec()

    def load_character(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Charakterdatei öffnen",
            "",
            "JSON Dateien (*.json);;Alle Dateien (*)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden der Datei:\n{e}")
            return

        # Prüfen, ob Datei eine Liste oder Sammlung enthält
        if isinstance(data, dict) and "characters" in data:
            characters = data["characters"]
            if not characters:
                QMessageBox.warning(self, "Fehler", "Keine Charaktere in der Datei gefunden.")
                return

            # Falls mehrere vorhanden, optional Auswahldialog (später)
            character = characters[0]  # aktuell: immer ersten laden
        else:
            character = data  # einzelner Charakter direkt gespeichert

        dialog = CharacterCreationDialog(self)
        dialog.load_character_data(character, file_name)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())
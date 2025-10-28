import sys
import json
import os
import uuid
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from random import randint


from PyQt6.QtCore import Qt
from decimal import Decimal, ROUND_HALF_UP

def load_all_characters_from_folder():
    """
    Liest alle gespeicherten Charaktere aus dem Ordner 'characters'
    und gibt eine Liste von Dicts zurück: 
    [ { "data": <char_dict>, "path": <pfad>, "display": <anzeigetext> }, ... ]
    """
    chars = []
    if not os.path.exists("characters"):
        return chars

    for fname in os.listdir("characters"):
        if fname.lower().endswith(".json"):
            full_path = os.path.join("characters", fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                char_name = data.get("name", "(unbenannt)")
                char_class = data.get("class", "?")
                char_age = data.get("age", "?")
                char_id = data.get("id", "???")
                display = f"{char_name} | {char_class}, {char_age} Jahre [{char_id[:8]}...]"

                chars.append({
                    "data": data,
                    "path": full_path,
                    "display": display,
                })
            except Exception:
                pass
    return chars


def kaufmaennisch_runden(x):
    """Rundet nach kaufmännischer Regel: ab 0.5 wird aufgerundet."""
    return int(Decimal(str(round(x, 3))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

class ItemEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Item bearbeiten / erstellen")
        self.setGeometry(200, 200, 400, 500)

        # wenn wir ein bestehendes Item laden, merken wir uns die Quelle
        self.loaded_file = None
        self.item_id = None  # UUID des Items

        # internes Attribut-Storage: {attr_name: {...}}
        self.attributes_inputs = {}

        # Zustände, die diesem Item zugeordnet sind (Liste von Condition-UUIDs)
        self.linked_conditions = []

        main_layout = QVBoxLayout()

        # Basisdaten
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.description_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Beschreibung:", self.description_input)
        main_layout.addLayout(form_layout)

        # Waffen-Option
        self.is_weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
        self.is_weapon_checkbox.stateChanged.connect(self.toggle_weapon_fields)
        form_layout.addRow("", self.is_weapon_checkbox)

        # Eingabefeld für Schadensformel (nur sichtbar, wenn Waffe)
        self.damage_formula_input = QLineEdit()
        self.damage_formula_input.setPlaceholderText("z. B. 1W6+2")
        self.damage_formula_input.setVisible(False)
        form_layout.addRow("Schadensformel:", self.damage_formula_input)


        # Attribute-Bereich
        self.attr_group = QGroupBox("Attribute")
        self.attr_layout_outer = QVBoxLayout()
        self.attr_form_layout = QFormLayout()
        self.attr_layout_outer.addLayout(self.attr_form_layout)

        self.add_attr_button = QPushButton("+ Neues Attribut")
        self.add_attr_button.clicked.connect(lambda: self.add_attribute_row())
        self.attr_layout_outer.addWidget(self.add_attr_button)

        self.attr_group.setLayout(self.attr_layout_outer)
        main_layout.addWidget(self.attr_group)

        # Zustände-Bereich
        self.conditions_group = QGroupBox("Verknüpfte Zustände")
        self.conditions_layout = QVBoxLayout()

        self.conditions_list_label = QLabel("Keine Zustände verknüpft.")
        self.conditions_layout.addWidget(self.conditions_list_label)

        # Buttons: bestehenden Zustand verknüpfen / neuen Zustand erstellen
        cond_button_row = QHBoxLayout()
        self.add_existing_condition_button = QPushButton("+ Bestehenden Zustand verknüpfen")
        self.add_existing_condition_button.clicked.connect(self.add_existing_condition)

        self.create_new_condition_button = QPushButton("+ Neuen Zustand erstellen")
        self.create_new_condition_button.clicked.connect(self.create_new_condition_from_item)

        cond_button_row.addWidget(self.add_existing_condition_button)
        cond_button_row.addWidget(self.create_new_condition_button)
        self.conditions_layout.addLayout(cond_button_row)

        # Entfernen-Button
        self.remove_condition_button = QPushButton("– Zustand entfernen")
        self.remove_condition_button.clicked.connect(self.remove_linked_condition)
        self.conditions_layout.addWidget(self.remove_condition_button)

        self.conditions_group.setLayout(self.conditions_layout)
        main_layout.addWidget(self.conditions_group)

        # Speichern-Button
        save_button = QPushButton("Item speichern")
        save_button.clicked.connect(self.save_item)
        main_layout.addWidget(save_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def toggle_weapon_fields(self):
        """Zeigt oder versteckt die Eingabe für die Schadensformel."""
        self.damage_formula_input.setVisible(self.is_weapon_checkbox.isChecked())


    def add_attribute_row(self, preset_name=None, preset_value=None):
        """
        Fügt eine neue Attribut-Zeile hinzu: [Label attr_name:] [Wertfeld] [Entfernen-Button]
        preset_* wird beim Laden existierender Items benutzt.
        Beim manuellen Anlegen via Button fragen wir interaktiv nach Name und Wert.
        """

        # 1. Attribut-Name bestimmen
        if preset_name is None:
            attr_name, ok = QInputDialog.getText(self, "Neues Attribut", "Attribut-Name:")
            if not ok:
                return  # User hat abgebrochen -> einfach nix tun
            attr_name = attr_name.strip()
            if not attr_name:
                QMessageBox.warning(self, "Fehler", "Attribut-Name darf nicht leer sein.")
                return
            if attr_name in self.attributes_inputs:
                QMessageBox.warning(self, "Fehler", f"Attribut '{attr_name}' existiert bereits.")
                return
        else:
            attr_name = str(preset_name)

        # 2. Attribut-Wert bestimmen
        if preset_value is None:
            attr_value, ok = QInputDialog.getText(self, "Neues Attribut", f"Wert für '{attr_name}':")
            if not ok:
                return  # User hat abgebrochen -> gar nicht erst anlegen
            attr_value = attr_value.strip()
        else:
            attr_value = str(preset_value)

        # 3. GUI-Zeile bauen
        value_field = QLineEdit(attr_value)
        remove_button = QPushButton("– Entfernen")

        row_layout = QHBoxLayout()
        name_label = QLabel(attr_name + ":")
        row_layout.addWidget(name_label)
        row_layout.addWidget(value_field)
        row_layout.addWidget(remove_button)

        placeholder_label = QLabel("")  # linker Slot fürs QFormLayout
        self.attr_form_layout.addRow(placeholder_label, row_layout)

        # 4. intern speichern
        self.attributes_inputs[attr_name] = {
            "field": value_field,
            "row_layout": row_layout,
            "name_label": name_label,
            "placeholder_label": placeholder_label,
        }

        # 5. Entfernen-Button verdrahten
        remove_button.clicked.connect(lambda _, key=attr_name: self.remove_attribute_row(key))

    def remove_attribute_row(self, attr_name):
        if attr_name not in self.attributes_inputs:
            return

        entry = self.attributes_inputs[attr_name]
        row_layout = entry["row_layout"]

        # Die richtige Zeile im FormLayout finden
        for i in range(self.attr_form_layout.rowCount()):
            label_item = self.attr_form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = self.attr_form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)

            if field_item is not None:
                layout_obj = field_item.layout()
                if layout_obj is row_layout:
                    # alle Widgets/Layers in row_layout zerstören
                    while row_layout.count():
                        child_item = row_layout.takeAt(0)
                        if child_item.widget():
                            child_item.widget().deleteLater()
                        elif child_item.layout():
                            inner = child_item.layout()
                            while inner.count():
                                inner_child = inner.takeAt(0)
                                if inner_child.widget():
                                    inner_child.widget().deleteLater()

                    # Placeholder-Label entfernen
                    if label_item and label_item.widget():
                        label_item.widget().deleteLater()

                    self.attr_form_layout.removeRow(i)
                    break

        del self.attributes_inputs[attr_name]

    def update_condition_display(self):
        """Aktualisiert die Anzeige der verknüpften Zustände im Item-Dialog."""
        if not self.linked_conditions:
            self.conditions_list_label.setText("Keine Zustände verknüpft.")
            return

        # conditions.json lesen, um Namen zuzuordnen
        cond_map = {}
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_map = {c["id"]: c for c in data.get("conditions", [])}
            except Exception:
                pass

        lines = []
        for cid in self.linked_conditions:
            cond = cond_map.get(cid)
            if cond:
                lines.append(f"{cond.get('name', '(unbenannt)')} ({cid[:8]}...)")
            else:
                lines.append(f"[Fehlend] {cid[:8]}...")

        self.conditions_list_label.setText("\n".join(lines))

    def add_existing_condition(self):
        """Lässt den Nutzer einen bestehenden Zustand aus conditions.json auswählen und verknüpft ihn."""
        if not os.path.exists("conditions.json"):
            QMessageBox.warning(self, "Fehler", "Keine conditions.json gefunden.")
            return

        with open("conditions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            conditions = data.get("conditions", [])

        if not conditions:
            QMessageBox.information(self, "Hinweis", "Es sind keine Zustände vorhanden.")
            return

        cond_names = [f"{c.get('name', '(unbenannt)')} [{c.get('id', '?')}]" for c in conditions]
        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du verknüpfen?",
            cond_names,
            0,
            False
        )
        if not ok:
            return

        idx = cond_names.index(choice)
        selected = conditions[idx]
        cid = selected.get("id")

        if cid in self.linked_conditions:
            QMessageBox.information(self, "Hinweis", "Dieser Zustand ist bereits verknüpft.")
            return

        self.linked_conditions.append(cid)
        self.update_condition_display()

    def create_new_condition_from_item(self):
        """Erstellt einen neuen Zustand und verknüpft ihn direkt mit diesem Item."""
        dlg = ConditionEditorDialog(self)
        dlg.condition_id = str(uuid.uuid4())
        dlg.exec()

        # Versuchen, den zuletzt gespeicherten Zustand aus conditions.json zu verknüpfen
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "conditions" in data and data["conditions"]:
                        latest = data["conditions"][-1]  # heuristik: letzter Eintrag = zuletzt gespeichert
                        cid = latest.get("id")
                        if cid and cid not in self.linked_conditions:
                            self.linked_conditions.append(cid)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Konnte neuen Zustand nicht verknüpfen:\n{e}")

        self.update_condition_display()

    def remove_linked_condition(self):
        """Ermöglicht, eine bestehende Verknüpfung zu entfernen."""
        if not self.linked_conditions:
            QMessageBox.information(self, "Hinweis", "Dieses Item hat keine verknüpften Zustände.")
            return

        # Namen zu IDs auflösen, damit der User nicht nur UUIDs sieht
        cond_map = {}
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_map = {c["id"]: c for c in data.get("conditions", [])}
            except Exception:
                pass

        cond_choices = [
            cond_map[cid]["name"] if cid in cond_map else f"[Fehlend] {cid[:8]}..."
            for cid in self.linked_conditions
        ]

        choice, ok = QInputDialog.getItem(
            self,
            "Zustand entfernen",
            "Welchen Zustand möchtest du entfernen?",
            cond_choices,
            0,
            False
        )
        if not ok:
            return

        idx = cond_choices.index(choice)
        cid_to_remove = self.linked_conditions[idx]
        self.linked_conditions.remove(cid_to_remove)
        self.update_condition_display()

    def load_item_data(self, item_data, file_path):
        """
        Lädt bestehendes Item in den Dialog, damit es bearbeitet werden kann.
        item_data ist ein einzelnes Item-Dict (mit 'id', 'name', ...)
        """
        self.loaded_file = file_path
        self.item_id = item_data.get("id", str(uuid.uuid4()))

        self.name_input.setText(item_data.get("name", ""))
        self.description_input.setText(item_data.get("description", ""))

        # Waffen-Checkbox & Schadensformel laden
        is_weapon = item_data.get("is_weapon", False)
        self.is_weapon_checkbox.setChecked(is_weapon)
        self.damage_formula_input.setText(item_data.get("damage_formula", ""))
        self.damage_formula_input.setVisible(is_weapon)


        # Zustände / Links laden
        self.linked_conditions = item_data.get("linked_conditions", [])
        self.update_condition_display()

        # Attribute rendern
        attrs = item_data.get("attributes", {})
        for attr_name, attr_value in attrs.items():
            self.add_attribute_row(preset_name=attr_name, preset_value=attr_value)

    def save_item(self):
        """
        Speichert/aktualisiert das Item in der items.json.
        - Wenn self.loaded_file gesetzt -> in diese Datei schreiben.
        - Sonst: neue Datei anlegen bzw. bestehende items.json im Arbeitsordner erweitern.
        """
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein.")
            return

        description = self.description_input.text().strip()

        # Attribute einsammeln
        attributes = {}
        for attr_name, data in self.attributes_inputs.items():
            value_field = data["field"]
            attributes[attr_name] = value_field.text().strip()

        # UUID vergeben/festhalten
        if not self.item_id:
            self.item_id = str(uuid.uuid4())

        item_obj = {
            "id": self.item_id,
            "name": name,
            "description": description,
            "attributes": attributes,
            "linked_conditions": self.linked_conditions
        }

        # Dateipfad bestimmen
        target_file = self.loaded_file if self.loaded_file else "items.json"

        # Bestehende Items laden (wenn Datei existiert)
        items_list = []
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
                        items_list = data["items"]
            except Exception:
                # wenn Datei kaputt ist -> starten wir leer
                pass

        # Prüfen, ob Item schon in der Liste ist -> dann ersetzen wir es
        replaced = False
        for idx, existing in enumerate(items_list):
            if existing.get("id") == self.item_id:
                items_list[idx] = item_obj
                replaced = True
                break

        if not replaced:
            items_list.append(item_obj)

        # Zurückschreiben
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump({"items": items_list}, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Erfolg", f"Item '{name}' wurde gespeichert!")
        self.accept()


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
        self.loaded_file = None
        self.loaded_file = None      # Pfad zur Datei auf Platte (wenn geladen/gespeichert)
        self.char_id = None          # UUID des Charakters

        super().__init__(parent)
        self.setWindowTitle("Neuen Charakter erstellen")
        self.setGeometry(150, 150, 500, 700)

        # ---------- SCROLL WRAPPER ----------
        # Das äußere Layout gehört dem Dialog selbst
        outer_layout = QVBoxLayout(self)

        # ScrollArea, in der der eigentliche Content wohnt
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Widget innerhalb der ScrollArea
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        # Das echte Content-Layout (das früher main_layout war)
        content_layout = QVBoxLayout(self.scroll_widget)

        # ScrollArea ins äußere Layout einhängen
        outer_layout.addWidget(self.scroll_area)

        # Ab hier benutzen wir main_layout so wie vorher
        main_layout = content_layout
        # ---------- /SCROLL WRAPPER ----------


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
        self.hitpoints_input.textChanged.connect(self.update_base_hitpoints)
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
        self.role_input = QComboBox()
        self.role_input.addItems(["Spielercharakter", "NSC / Gegner"])
        self.base_form.insertRow(0, "Typ:", self.role_input)


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
            self.style_groupbox(self.group_boxes[category])

            self.form_layouts[category] = QFormLayout()
            self.skill_inputs[category] = {}

            vbox = QVBoxLayout()
            vbox.addLayout(self.form_layouts[category])

            self.add_buttons[category] = QPushButton("+ Neue Fähigkeit")
            self.add_buttons[category].clicked.connect(lambda _, cat=category: self.add_skill(cat))
            vbox.addWidget(self.add_buttons[category])

            self.group_boxes[category].setLayout(vbox)

            main_layout.addWidget(self.group_boxes[category])

            self.category_labels[category] = QLabel(f"{category}-Wert: 0")
            self.inspiration_labels[category] = QLabel(f"Geistesblitzpunkte ({category}): 0")
            main_layout.addWidget(self.category_labels[category])
            main_layout.addWidget(self.inspiration_labels[category])


        main_layout.addWidget(self.total_points_label)

        # Items
        self.items_group = QGroupBox("Items")
        self.style_groupbox(self.items_group)
        self.items_layout = QVBoxLayout()
        self.item_groups = {}
        self.item_add_button = QPushButton("+ Neues Item")
        self.item_add_button.clicked.connect(self.add_item)
        self.items_layout.addWidget(self.item_add_button)
        self.item_add_from_lib_button = QPushButton("+ Item aus Sammlung hinzufügen")
        self.item_add_from_lib_button.clicked.connect(self.add_item_from_library)
        self.items_layout.addWidget(self.item_add_from_lib_button)
        self.items_group.setLayout(self.items_layout)
        main_layout.addWidget(self.items_group)

        # Zustände
        self.conditions_group = QGroupBox("Zustände")
        self.style_groupbox(self.conditions_group)
        self.conditions_layout = QVBoxLayout()
        self.condition_groups = {}
        # Zustände von Items
        # mappt item_name -> liste von condition_ids (UUIDs)
        self.item_condition_links = {}

        # mappt condition_id -> dict mit den vollen Zustandsdaten
        # so wie sie aus conditions.json kommen oder ad hoc gebaut wurden
        self.active_condition_by_id = {}

        # wir brauchen außerdem einen Counter, um Zustände, die von mehreren Items kommen, nicht doppelt zu entfernen
        # mappt condition_id -> wie viele Quellen (Items oder manuell) diesen Zustand "aktiv" halten
        self.condition_refcount = {}
        self.condition_add_button = QPushButton("+ Neuer Zustand")
        self.condition_add_button.clicked.connect(self.add_condition)
        self.conditions_layout.addWidget(self.condition_add_button)
        self.conditions_group.setLayout(self.conditions_layout)
        self.condition_add_from_lib_button = QPushButton("+ Zustand aus Sammlung hinzufügen")
        self.condition_add_from_lib_button.clicked.connect(self.add_condition_from_library)
        self.conditions_layout.addWidget(self.condition_add_from_lib_button)
        main_layout.addWidget(self.conditions_group)


        self.base_hitpoints = 0

        # Grundschaden (z. B. Faustkampf oder allgemeiner Nahkampfschaden)
        self.base_damage_input = QLineEdit()
        self.base_damage_input.setPlaceholderText("z.B. 1W6 oder 1W6+2")
        main_layout.addWidget(QLabel("Grundschaden:"))
        main_layout.addWidget(self.base_damage_input)

        self.base_values = {
            "Lebenspunkte": 0,
            "Kategorien": {},        # z. B. {"Handeln": 5}
            "Geistesblitzpunkte": {},# z. B. {"Wissen": 1}
            "Fertigkeiten": {}       # z. B. {"Laufen": 50}
        }


        # Speichern-Button
        save_button = QPushButton("Charakter speichern")
        save_button.clicked.connect(self.save_character)
        main_layout.addWidget(save_button)

        main_layout.addStretch()

    def _is_condition_target_valid_for_this_character(self, effect_target: str) -> bool:
        """
        Prüft, ob ein effect_target wie
        - "Lebenspunkte"
        - "Fertigkeit: Schleichen"
        - "Kategoriewert: Handeln"
        - "Geistesblitzpunkte: Wissen"
        in diesem Charakter tatsächlich existiert.

        Gibt True zurück, wenn der Zustand sinnvoll angewendet werden kann.
        """
        if not effect_target or effect_target == "(kein Ziel / n/a)":
            return True  # dann gibt's eh keinen Effekt, also nix zu validieren

        # 1) Lebenspunkte ist immer okay
        if effect_target == "Lebenspunkte":
            return True

        # 2) Fertigkeit: <name>
        if effect_target.startswith("Fertigkeit: "):
            skill_name = effect_target.replace("Fertigkeit: ", "", 1).strip()
            # checkt, ob der Char diese Fertigkeit überhaupt hat
            for cat, skill_list in self.skills.items():
                if skill_name in skill_list:
                    return True
            return False

        # 3) Kategoriewert: <cat>
        if effect_target.startswith("Kategoriewert: "):
            cat_name = effect_target.replace("Kategoriewert: ", "", 1).strip()
            # Kategorienamen sind unsere keys in self.skills (Handeln/Wissen/Soziales/…)
            return cat_name in self.skills

        # 4) Geistesblitzpunkte: <cat>
        if effect_target.startswith("Geistesblitzpunkte: "):
            cat_name = effect_target.replace("Geistesblitzpunkte: ", "", 1).strip()
            return cat_name in self.skills

        # 5) Wenn es ein komplett freies/custom Ziel ist (Benutzerdefiniert ... oder etwas Exotisches),
        #    dann können wir nicht prüfen → wir lassen es als gültig durchgehen.
        return True


    def style_groupbox(self, box: QGroupBox):
        box.setStyleSheet("""
            QGroupBox {
                margin-top: 8px;
                padding: 8px;
                border: 1px solid #444;
                border-radius: 6px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 4px;
                color: #ddd;
                font-weight: bold;
            }
        """)

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
        # 1. Namen abfragen wie bisher
        item_name, ok = QInputDialog.getText(self, "Neues Item", "Item-Name:")
        if not ok or not item_name.strip():
            QMessageBox.warning(self, "Fehler", "Item-Name darf nicht leer sein.")
            return
        item_name = item_name.strip()
        if item_name in self.item_groups:
            QMessageBox.warning(self, "Fehler", f"Item '{item_name}' existiert bereits.")
            return

        # 2. GroupBox für dieses Item
        item_group = QGroupBox(item_name)
        self.style_groupbox(item_group)

        item_layout = QVBoxLayout()

        # Wir speichern für dieses Item:
        # - attributes: dict[str,str]
        # - layout: das VBoxLayout
        # - group: die QGroupBox
        # - id: None (neu erzeugtes Item hat noch keine globale Item-ID)
        # - linked_conditions: [] (erstmal leer)
        # - is_weapon_checkbox: QCheckBox
        # - damage_field: QLineEdit
        self.item_groups[item_name] = {
            "attributes": {},
            "layout": item_layout,
            "group": item_group,
            "id": None,
            "linked_conditions": [],
            "is_weapon_checkbox": None,
            "damage_field": None,
        }

        # 3. Attribut-Liste (genau wie vorher)
        attr_layout = QFormLayout()
        item_layout.addLayout(attr_layout)

        # Wir brauchen Zugriff auf attr_layout später, also speichern wir es auch:
        self.item_groups[item_name]["attr_layout"] = attr_layout

        # 4. Waffen-spezifischer Bereich
        weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
        damage_input = QLineEdit()
        damage_input.setPlaceholderText("z. B. 1W6+2")
        damage_row = QHBoxLayout()
        damage_row.addWidget(QLabel("Schadensformel:"))
        damage_row.addWidget(damage_input)

        # standardmäßig ausgeblendet, bis Checkbox aktiv
        damage_input.setVisible(False)

        def on_weapon_toggle(state):
            damage_input.setVisible(state == Qt.CheckState.Checked.value)

        weapon_checkbox.stateChanged.connect(on_weapon_toggle)

        item_layout.addWidget(weapon_checkbox)
        item_layout.addLayout(damage_row)

        # Referenzen speichern, damit save_character() drankommt
        self.item_groups[item_name]["is_weapon_checkbox"] = weapon_checkbox
        self.item_groups[item_name]["damage_field"] = damage_input

        # 5. Button: neues Attribut hinzufügen (wie vorher)
        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addWidget(add_attr_button)

        # 6. Entfernen-Button wie vorher
        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item(item))
        item_layout.addWidget(remove_button)

        # 7. In die UI einhängen (vor den beiden globalen Buttons)
        item_group.setLayout(item_layout)

        # In items_layout ist aktuell:
        #   [ + Neues Item ]
        #   [ + Item aus Sammlung hinzufügen ]
        # Wir wollen das neue Item VOR diesen Buttons einfügen.
        insert_pos = max(0, self.items_layout.count() - 2)
        self.items_layout.insertWidget(insert_pos, item_group)


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

    def add_item_from_library(self):
        """Fügt dem Charakter ein Item aus items.json hinzu und aktiviert dessen Zustände."""
        # 1. Items-Datei lesen
        if not os.path.exists("items.json"):
            QMessageBox.warning(self, "Fehler", "Keine items.json gefunden.")
            return

        try:
            with open("items.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                items_list = data.get("items", [])
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von items.json:\n{e}")
            return

        if not items_list:
            QMessageBox.information(self, "Hinweis", "Es sind keine Items in items.json vorhanden.")
            return

        # 2. Item auswählen lassen
        item_choices = [f"{it.get('name','(unbenannt)')} [{it.get('id','?')}]" for it in items_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Item auswählen",
            "Welches Item soll hinzugefügt werden?",
            item_choices,
            0,
            False
        )
        if not ok:
            return

        idx = item_choices.index(choice)
        chosen_item = items_list[idx]

        item_name = chosen_item.get("name", "Unbenanntes Item")
        item_id = chosen_item.get("id", str(uuid.uuid4()))
        attributes = chosen_item.get("attributes", {})
        linked_conditions = chosen_item.get("linked_conditions", [])

        # 3. Prüfen, ob Item mit gleichem Namen schon existiert
        if item_name in self.item_groups:
            QMessageBox.warning(self, "Fehler", f"Item '{item_name}' existiert bereits im Inventar.")
            return

        # 4. Item-UI Block erstellen wie in add_item(), aber vorbefüllt
        item_group = QGroupBox(item_name)
        item_group = QGroupBox(item_name)
        self.style_groupbox(item_group)

        item_layout = QVBoxLayout()
        self.item_groups[item_name] = {
            "attributes": {},
            "layout": item_layout,
            "group": item_group,
            "id": item_id,
            "linked_conditions": linked_conditions,
            "is_weapon": chosen_item.get("is_weapon", False),
            "damage_formula": chosen_item.get("damage_formula", ""),
            # diese beiden Felder haben Bibliotheks-Items nicht als Widgets:
            "is_weapon_checkbox": None,
            "damage_field": None,
        }

        attr_layout = QFormLayout()
        # Attribute aus dem gespeicherten Item hinzufügen
        for attr_name, attr_value in attributes.items():
            attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))
            self.item_groups[item_name]["attributes"][attr_name] = attr_value

        if chosen_item.get("is_weapon"):
            dmg = chosen_item.get("damage_formula", "")
            attr_layout.addRow("Waffe", QLabel(f"Schaden: {dmg}"))

        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addLayout(attr_layout)
        item_layout.addWidget(add_attr_button)

        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))
        item_layout.addWidget(remove_button)

        item_group.setLayout(item_layout)
        self.items_layout.insertWidget(self.items_layout.count() - 2, item_group)
        # ^ wir -2 einfügen statt -1, weil wir jetzt 2 Buttons (Neues Item / Aus Sammlung) am Ende haben

        # 5. Zustände aus diesem Item aktivieren
        self.item_condition_links[item_name] = linked_conditions
        self.attach_item_conditions(item_name, linked_conditions)

    def attach_item_conditions(self, item_name, condition_ids):
        """
        Nimmt die Zustands-UUIDs eines Items, schaut in conditions.json nach,
        und sorgt dafür, dass diese Zustände im Charakter sichtbar/aktiv sind.
        Falls ein Zustand schon da ist (z.B. durch ein anderes Item), erhöhen wir nur den Refcount.
        """
        # conditions.json laden -> Map von ID -> Zustand
        cond_map = {}
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_map = {c["id"]: c for c in data.get("conditions", [])}
            except Exception:
                pass

        for cid in condition_ids:
            cond_data = cond_map.get(cid)
            if not cond_data:
                # Zustand ungekannt? -> wir hängen trotzdem nen Platzhalter ein, aber ohne Wirkung
                cond_data = {
                    "id": cid,
                    "name": f"(Unbekannter Zustand {cid[:8]}...)",
                    "description": "Originalzustand nicht gefunden.",
                    "effect_type": "keine Auswirkung",
                    "effect_target": "",
                    "effect_value": 0
                }

            # Refcount erhöhen
            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            # Wenn Zustand schon im UI ist, nicht doppelt zeichnen
            if cid in self.active_condition_by_id:
                continue

            # Zustand im UI darstellen
            self.render_condition_block_from_condition_data(cid, cond_data, source_item=item_name)

            # merken
            self.active_condition_by_id[cid] = cond_data

        # Effekte neu anwenden (falls missionsweit etc.)
        self.recalculate_conditions_effects()

    def render_condition_block_from_condition_data(self, cid, cond_data, source_item=None):
        """
        Zeichnet einen Zustand in die Zustands-UI (self.conditions_layout),
        basierend auf einem cond_data-Dict im Format aus conditions.json.
        cid = eindeutige Zustands-ID (UUID)
        source_item = optionaler Item-Name, das diesen Zustand liefert
        """

        cond_name = cond_data.get("name", f"Zustand {cid[:8]}")
        desc = cond_data.get("description", "")
        effect_type = cond_data.get("effect_type", "keine Auswirkung")
        effect_target = cond_data.get("effect_target", "")
        effect_value = cond_data.get("effect_value", 0)

        group = QGroupBox(cond_name)
        self.style_groupbox(group)

        layout = QVBoxLayout()

        # Beschreibung
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Effektzeile (falls einer existiert)
        if effect_type != "keine Auswirkung" and effect_target:
            # Prüfen, ob dieses Target für DIESEN Charakter überhaupt Sinn ergibt
            target_ok = self._is_condition_target_valid_for_this_character(effect_target)

            if target_ok:
                # normaler Stil
                effect_label = QLabel(
                    f"{effect_type.capitalize()}e Wirkung: "
                    f"{effect_target} "
                    f"{effect_value:+}"
                )
                effect_label.setStyleSheet("color: #555; font-style: italic;")
                layout.addWidget(effect_label)
            else:
                # WARNUNG: dieser Zustand will etwas modifizieren,
                # das der Charakter gar nicht hat
                effect_label = QLabel(
                    f"{effect_type.capitalize()}e Wirkung: "
                    f"{effect_target} {effect_value:+}  (⚠ nicht vorhanden bei diesem Charakter)"
                )
                effect_label.setStyleSheet("color: #b00; font-weight: bold;")
                layout.addWidget(effect_label)

                warn_label = QLabel(
                    "Hinweis: Dieser Zustand verweist auf einen Wert, "
                    "den dieser Charakter aktuell nicht besitzt."
                )
                warn_label.setWordWrap(True)
                warn_label.setStyleSheet("color: #b00; font-size: 10px;")
                layout.addWidget(warn_label)

        # Falls der Zustand aus einem Item kommt, Info anzeigen
        if source_item:
            src_label = QLabel(f"Aktiv durch Item: {source_item}")
            src_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(src_label)

        # Entfernen-Button nur für manuell aktivierte Zustände (also ohne source_item).
        # Item-Zustände verschwinden nur, wenn das Item entfernt wird.
        if source_item is None:
            remove_button = QPushButton("– Zustand entfernen")
            remove_button.clicked.connect(lambda _, cond_id=cid: self.manual_remove_condition_by_id(cond_id))
            layout.addWidget(remove_button)

        group.setLayout(layout)

        # Gruppe VOR den Buttons einfügen (Buttons sind am Ende des Layouts)
        # self.conditions_layout enthält:
        #   [ "+ Neuer Zustand", ... , "+ Zustand aus Sammlung hinzufügen" ]
        # Wir wollen den Block davor reinschieben.
        insert_pos = max(0, self.conditions_layout.count() - 2)
        self.conditions_layout.insertWidget(insert_pos, group)

        # Widget-Metadaten in active_condition_by_id speichern (für späteres Entfernen usw.)
        temp = self.active_condition_by_id.get(cid, {})
        temp["_widget"] = group
        # Merge dicts
        merged = {**cond_data, **temp}
        self.active_condition_by_id[cid] = merged


    def remove_item_and_detach_conditions(self, item_name):
        """
        Entfernt ein Item aus dem Charakterinventar und reduziert die Refcounts
        der damit verknüpften Zustände.
        Zustände, die dadurch auf 0 fallen, verschwinden wieder aus der UI.
        """
        if item_name not in self.item_groups:
            return

        # 1. Zustands-Links dieses Items holen
        linked_conds = self.item_groups[item_name].get("linked_conditions", [])
        for cid in linked_conds:
            if cid in self.condition_refcount:
                self.condition_refcount[cid] -= 1
                if self.condition_refcount[cid] <= 0:
                    # komplett entfernen
                    self.condition_refcount.pop(cid, None)
                    self.remove_condition_widget_by_id(cid)

        # 2. Item-UI entfernen
        item_group = self.item_groups[item_name]["group"]
        self.items_layout.removeWidget(item_group)
        item_group.deleteLater()
        del self.item_groups[item_name]

        # 3. auch den Link aus item_condition_links löschen
        if item_name in self.item_condition_links:
            del self.item_condition_links[item_name]

        # 4. Effekte neu anwenden
        self.recalculate_conditions_effects()

        QMessageBox.information(self, "Erfolg", f"Item '{item_name}' wurde entfernt.")


    def remove_condition_widget_by_id(self, cid):
        """
        Entfernt die UI-Darstellung eines Zustands (falls sichtbar) und vergisst ihn in active_condition_by_id.
        Achtung: das betrifft NUR Zustände, die über Items gekommen sind ODER manuell entfernt wurden.
        """
        cond_info = self.active_condition_by_id.get(cid)
        if not cond_info:
            return

        widget = cond_info.get("_widget")
        if widget:
            self.conditions_layout.removeWidget(widget)
            widget.deleteLater()

        # aus Tracking entfernen
        self.active_condition_by_id.pop(cid, None)

    def add_condition(self):
        # baue die möglichen Ziele aus DIESEM Charakter
        skill_targets, cat_targets, insp_targets = self._build_condition_target_lists()

        dlg = ConditionEditorDialog(
            parent=self,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.condition_id = str(uuid.uuid4())  # direkt neue UUID vergeben
        result = dlg.exec()
        if result != QDialog.DialogCode.Accepted:
            return  # Abbruch -> nix tun

        # Zustand wurde gespeichert → wir müssen ihn in den Charakter aktivieren
        # und ins UI holen

        # Schritt 1: conditions.json neu einlesen und den gespeicherten Zustand finden
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_list = data.get("conditions", [])
            except Exception:
                cond_list = []
        else:
            cond_list = []

        # Wir suchen den Zustand per ID, die der Dialog gesetzt hat
        saved_cond = None
        for c in cond_list:
            if c.get("id") == dlg.condition_id:
                saved_cond = c
                break

        # Falls wir ihn nicht finden, ist was schief – dann bauen wir ihn eben aus Dialogfeldern rekonstruiert neu
        if not saved_cond:
            saved_cond = {
                "id": dlg.condition_id,
                "name": dlg.name_input.text().strip(),
                "description": dlg.description_input.text().strip(),
                "effect_type": dlg.effect_type_input.currentText(),
                "effect_target": dlg.ask_for_custom_target_if_needed(),  # finaler target string
                "effect_value": int(dlg.effect_value_input.text() or "0")
            }

        cid = saved_cond["id"]

        # Refcount erhöhen
        self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

        # In unsere aktiven Zustände aufnehmen (falls nicht schon da)
        already_active = cid in self.active_condition_by_id
        self.active_condition_by_id[cid] = {
            "id": cid,
            "name": saved_cond.get("name", ""),
            "description": saved_cond.get("description", ""),
            "effect_type": saved_cond.get("effect_type", "keine Auswirkung"),
            "effect_target": saved_cond.get("effect_target", ""),
            "effect_value": saved_cond.get("effect_value", 0),
            # _widget füllen wir gleich beim rendern, falls nötig
        }

        if not already_active:
            self.render_condition_block_from_condition_data(cid, self.active_condition_by_id[cid], source_item=None)

        # Effekte neu anwenden
        self.recalculate_conditions_effects()

    def remove_condition(self, condition_name):
        """Entfernt einen Zustand aus der Liste."""
        if condition_name in self.condition_groups:
            group = self.condition_groups[condition_name]["group"]
            self.conditions_layout.removeWidget(group)
            group.deleteLater()
            del self.condition_groups[condition_name]
            QMessageBox.information(self, "Erfolg", f"Zustand '{condition_name}' wurde entfernt.")
        # Falls missionsweite Effekte betroffen sind → aktualisieren
        self.apply_mission_effects()
        self.apply_all_mission_effects()

    def _build_condition_target_lists(self):
        skill_targets = []
        category_targets = []
        insp_targets = []

        for cat, skill_list in self.skills.items():
            # Skills
            for skill in skill_list:
                skill_targets.append(f"Fertigkeit: {skill}")

            # Kategorien immer eintragen:
            category_targets.append(f"Kategoriewert: {cat}")
            insp_targets.append(f"Geistesblitzpunkte: {cat}")

        return skill_targets, category_targets, insp_targets


    def manual_remove_condition_by_id(self, cid):
        """
        Entfernt einen manuell erstellten Zustand endgültig.
        Verringert Refcount und löscht ihn ggf. auch aus condition_groups.
        """
        if cid not in self.condition_refcount:
            return

        self.condition_refcount[cid] -= 1
        if self.condition_refcount[cid] <= 0:
            self.condition_refcount.pop(cid, None)
            # UI entfernen
            self.remove_condition_widget_by_id(cid)

            # auch aus condition_groups löschen, falls dort drin
            # Wir müssen über Namen iterieren, weil condition_groups keyed by name ist
            to_delete = []
            for name, data in self.condition_groups.items():
                if data.get("id") == cid:
                    to_delete.append(name)
            for name in to_delete:
                del self.condition_groups[name]

        # Effekte neu anwenden
        self.recalculate_conditions_effects()

    def add_condition_from_library(self):
        """Fügt dem Charakter einen bestehenden Zustand aus conditions.json hinzu (ohne Itembindung)."""
        # 1. conditions.json laden
        if not os.path.exists("conditions.json"):
            QMessageBox.warning(self, "Fehler", "Keine conditions.json gefunden.")
            return

        try:
            with open("conditions.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                cond_list = data.get("conditions", [])
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von conditions.json:\n{e}")
            return

        if not cond_list:
            QMessageBox.information(self, "Hinweis", "Es sind keine Zustände in conditions.json vorhanden.")
            return

        # 2. Auswahl anzeigen
        choices = [f"{c.get('name','(unbenannt)')} [{c.get('id','?')}]" for c in cond_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du hinzufügen?",
            choices,
            0,
            False
        )
        if not ok:
            return

        idx = choices.index(choice)
        chosen = cond_list[idx]

        # 3. Die rohen Daten dieses Zustands holen
        cid = chosen.get("id", str(uuid.uuid4()))
        cond_name = chosen.get("name", f"Zustand {cid[:8]}")
        cond_description = chosen.get("description", "")
        cond_effect_type = chosen.get("effect_type", "keine Auswirkung")
        cond_effect_target = chosen.get("effect_target", "")
        cond_effect_value = chosen.get("effect_value", 0)

        # 4. In unsere laufenden Strukturen integrieren
        # Falls Zustand schon aktiv ist (z. B. durch Item oder schon mal hinzugefügt), 
        # erhöhen wir nur den Refcount und zeichnen ihn NICHT neu.
        already_active = cid in self.active_condition_by_id

        # Refcount +1
        self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

        if not already_active:
            # Zustand muss neu erzeugt und gerendert werden
            cond_data = {
                "id": cid,
                "name": cond_name,
                "description": cond_description,
                "effect_type": cond_effect_type,
                "effect_target": cond_effect_target,
                "effect_value": cond_effect_value,
            }

            # merken
            self.active_condition_by_id[cid] = cond_data

            # UI-Block bauen, ohne source_item (weil direkt auf den Char angewendet)
            self.render_condition_block_from_condition_data(cid, cond_data, source_item=None)

        # 5. Effekte neu anwenden
        self.recalculate_conditions_effects()

    def recalculate_conditions_effects(self):
        """
        Spiegelt alle aktiven Zustände (aus Items + manuell) nach self.condition_groups,
        damit apply_mission_effects / apply_all_mission_effects korrekt arbeiten,
        und aktualisiert anschließend die Missionseffekte.
        """
        self.condition_groups = {}

        for cid, cond_data in self.active_condition_by_id.items():
            widget = cond_data.get("_widget")
            if widget is None:
                # Falls aus irgendeinem Grund kein UI-Widget erzeugt wurde,
                # dann ist der Zustand nicht visuell aktiv -> überspringen.
                continue

            name_for_group = cond_data.get("name", f"Zustand {cid[:8]}")
            self.condition_groups[name_for_group] = {
                "description": cond_data.get("description", ""),
                "type": cond_data.get("effect_type", "keine Auswirkung"),
                "effect_target": cond_data.get("effect_target", ""),
                "effect_value": cond_data.get("effect_value", 0),
                "group": widget,
                "id": cid,
            }

        # Deine bestehende Logik weiterverwenden:
        self.apply_mission_effects()
        self.apply_all_mission_effects()



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
            # Basiswerte für spätere Zustandsanwendung speichern
            for category in self.skills:
                category_label_text = self.category_labels[category].text()
                cat_value = int(category_label_text.split(":")[-1].strip())
                self.base_values["Kategorien"][category] = cat_value

                insp_label_text = self.inspiration_labels[category].text()
                insp_value = int(insp_label_text.split(":")[-1].strip().replace("Geistesblitzpunkte", "").strip())
                self.base_values["Geistesblitzpunkte"][category] = insp_value

                for skill, input_field in self.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    self.base_values["Fertigkeiten"][skill] = val

            self.total_points_label.setText(f"Verbleibende Punkte: {remaining}")
            if remaining < 0:
                raise ValueError("Gesamtpunkte überschreiten 400!")
            self.update_endwert_labels()

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e))

    def apply_mission_effects(self):
        """Aktualisiert alle missionsweiten Effekte auf den Charakterwerten."""
        base_hp = self.base_hitpoints
        total_hp_modifier = 0
        affecting_conditions = []

        for cond_name, cond in self.condition_groups.items():
            if cond["type"] == "missionsweit" and cond["effect_target"] == "Lebenspunkte":
                total_hp_modifier += cond["effect_value"]
                affecting_conditions.append(f"{cond_name} ({cond['effect_value']:+})")

        modified_hp = base_hp + total_hp_modifier

        if affecting_conditions:
            self.hitpoints_input.setStyleSheet("color: red; font-weight: bold;")
            tooltip = " | ".join(affecting_conditions)
            self.hitpoints_input.setToolTip(f"Modifiziert durch: {tooltip}")
            # Anzeige anpassen, aber Basiswert beibehalten
            self.hitpoints_input.blockSignals(True)
            self.hitpoints_input.setText(str(modified_hp))
            self.hitpoints_input.blockSignals(False)
        else:
            self.hitpoints_input.blockSignals(True)
            self.hitpoints_input.setText(str(base_hp))
            self.hitpoints_input.blockSignals(False)
            self.hitpoints_input.setStyleSheet("")
            self.hitpoints_input.setToolTip("")

    def apply_all_mission_effects(self):
        """Wendet alle missionsweiten Zustände auf Lebenspunkte, Kategorien, Geistesblitzpunkte und Fertigkeiten an."""
        # 1️⃣ Starte mit sauberen Basiswerten
        self.apply_mission_effects()  # HP separat behandeln

        # 2️⃣ Kategorie-Labels anpassen
        for category, base_val in self.base_values["Kategorien"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Kategoriewert: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            if affecting:
                self.category_labels[category].setText(f"{category}-Wert: {modified_val} (Mod: {'; '.join(affecting)})")
                self.category_labels[category].setStyleSheet("color: darkred; font-weight: bold;")
            else:
                self.category_labels[category].setText(f"{category}-Wert: {base_val}")
                self.category_labels[category].setStyleSheet("")

        # 3️⃣ Geistesblitzpunkte anpassen
        for category, base_val in self.base_values["Geistesblitzpunkte"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Geistesblitzpunkte: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            if affecting:
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {modified_val} (Mod: {'; '.join(affecting)})")
                self.inspiration_labels[category].setStyleSheet("color: darkblue; font-weight: bold;")
            else:
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {base_val}")
                self.inspiration_labels[category].setStyleSheet("")

        # 4️⃣ Fertigkeiten anpassen
        for skill, base_val in self.base_values["Fertigkeiten"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Fertigkeit: {skill}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier

            for category, skills_dict in self.skill_inputs.items():
                if skill in skills_dict:
                    field = skills_dict[skill]
                    field.blockSignals(True)
                    field.setText(str(modified_val))
                    field.blockSignals(False)
                    if affecting:
                        field.setStyleSheet("color: darkgreen; font-weight: bold;")
                        tooltip = " | ".join(affecting)
                        field.setToolTip(f"Modifiziert durch: {tooltip}")
                    else:
                        field.setStyleSheet("")
                        field.setToolTip("")
                    break

        # ✨ NEU: nach allen Modifikationen Endwert-Labels updaten
        self.update_endwert_labels()

    def update_endwert_labels(self):
        """
        Aktualisiert alle Endwert-Labels für alle Fertigkeiten basierend auf:
        - aktuellem (ggf. modifiziertem) Skill-Wert im Eingabefeld
        - aktuellem (ggf. modifiziertem) Kategoriewert-Label
        """
        for category in self.skills:
            # aktuellen (ggf. modifizierten) Kategoriewert aus dem Label parsen
            # Label sieht jetzt z.B. so aus:
            #   "Handeln-Wert: 5"
            # oder nach Mod: 
            #   "Handeln-Wert: 3 (Mod: Fieber (-2))"
            cat_label_text = self.category_labels[category].text()
            # wir holen die erste Zahl nach dem Doppelpunkt
            try:
                cat_current_value_str = cat_label_text.split(":")[1].strip().split(" ")[0]
                cat_current_value = int(cat_current_value_str)
            except Exception:
                cat_current_value = 0

            # jetzt alle Skills dieser Kategorie anfassen
            for skill, input_field in self.skill_inputs[category].items():
                # aktueller (ggf. modifizierter) Skillwert aus dem Feld
                try:
                    skill_val = int(input_field.text()) if input_field.text() else 0
                except ValueError:
                    skill_val = 0

                # Endwert = Skillwert + Kategoriewert
                final_val = skill_val + cat_current_value

                # zum passenden Endwert-Label schreiben
                if category in self.skill_end_labels and skill in self.skill_end_labels[category]:
                    self.skill_end_labels[category][skill].setText(f"Endwert: {final_val}")



    def update_base_hitpoints(self):
        """Aktualisiert den gespeicherten Basiswert, wenn der Nutzer Lebenspunkte manuell ändert."""
        try:
            # Wenn der Nutzer gerade einen Wert eingibt, interpretieren wir ihn als Basiswert
            self.base_hitpoints = int(self.hitpoints_input.text())
        except ValueError:
            # keine Zahl → ignorieren
            self.base_hitpoints = 0


    def save_character(self):
        try:
            name = self.name_input.text().strip()
            if not name:
                raise ValueError("Name darf nicht leer sein.")

            age = int(self.age_input.text())
            if not 1 <= age <= 120:
                raise ValueError("Alter muss zwischen 1 und 120 liegen.")

            hitpoints = self.base_hitpoints
            if not 1 <= hitpoints <= 100:
                raise ValueError("Lebenspunkte müssen zwischen 1 und 100 liegen.")

            religion = self.religion_input.text().strip()
            occupation = self.occupation_input.text().strip()
            base_damage = self.base_damage_input.text().strip()

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

            # Items sammeln
            # Wir speichern jetzt vollständiger:
            # - attributes
            # - id (falls vorhanden)
            # - linked_conditions (falls vorhanden)
            items_data = {}
            for item_name, data in self.item_groups.items():
                is_weapon = False
                damage_formula = ""

                # Falls dieses Item im Dialog direkt erstellt wurde,
                # gibt es die Felder is_weapon_checkbox / damage_field
                weapon_cb = data.get("is_weapon_checkbox")
                dmg_field = data.get("damage_field")

                if weapon_cb is not None and dmg_field is not None:
                    is_weapon = weapon_cb.isChecked()
                    damage_formula = dmg_field.text().strip() if is_weapon else ""
                else:
                    # Falls das Item aus der Bibliothek kam (add_item_from_library),
                    # liegen die Infos nicht in Widgets, sondern nur implizit in attributes.
                    # Beim Laden aus der Bibliothek hatten wir:
                    #   if chosen_item.get("is_weapon"):
                    #       ...
                    # Da haben wir's NICHT explizit gespeichert. Holen wir jetzt nach:
                    is_weapon = bool(data.get("is_weapon", False))
                    damage_formula = data.get("damage_formula", "")

                items_data[item_name] = {
                    "attributes": data.get("attributes", {}),
                    "id": data.get("id", None),  # kann None sein für neue Items
                    "linked_conditions": data.get("linked_conditions", []),
                    "is_weapon": is_weapon,
                    "damage_formula": damage_formula,
                }


            # Zustände sammeln (für Savegame-Kompatibilität)
            # -> wir nehmen ALLE aktiven Zustände aus self.active_condition_by_id
            #    (also sowohl manuell erzeugte als auch durch Items automatisch aktivierte)
            conditions_data = {}
            for cid, cond_data in self.active_condition_by_id.items():
                # cond_data enthält unsere Felder aus conditions.json / add_condition
                # aber plus "_widget"; das darf NICHT in die Datei
                cleaned = {
                    "id": cid,
                    "name": cond_data.get("name", ""),
                    "description": cond_data.get("description", ""),
                    "effect_type": cond_data.get("effect_type", "keine Auswirkung"),
                    "effect_target": cond_data.get("effect_target", ""),
                    "effect_value": cond_data.get("effect_value", 0),
                }
                # Wir legen im Savegame nach name ab, so wie du es vorher gespeichert hast,
                # aber jetzt mit angereichertem Inhalt (inklusive id).
                # Falls zwei Zustände denselben Anzeigenamen haben, gewinnt der letzte – das ist
                # ok für jetzt; ein sauberer Ansatz wäre eine Liste statt dict, aber wir
                # behalten erstmal kompatibles Format.
                conditions_data[cleaned["name"]] = cleaned

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e) if str(e) != "" else "Bitte gültige Zahlen eingeben.")
            return

        # Stelle sicher, dass der Charakter eine stabile ID hat
        if not self.char_id:
            self.char_id = str(uuid.uuid4())

        character = {
            "id": self.char_id,
            "name": name,
            "class": self.class_input.currentText(),
            "gender": self.gender_input.currentText(),
            "age": age,
            "hitpoints": hitpoints,
            "base_damage": base_damage,
            "build": self.build_input.currentText(),
            "religion": religion,
            "occupation": occupation,
            "marital_status": self.marital_status_input.currentText(),
            "skills": skills_data,
            "category_scores": category_scores,
            "inspiration_points": inspiration_points,
            "items": items_data,
            "conditions": conditions_data,
            "role": "pc" if self.role_input.currentText().startswith("Spieler") else "npc"
        }

        # Speicherort bestimmen
        # Falls wir schon aus einer Datei geladen wurden oder bereits gespeichert haben:
        if self.loaded_file:
            target_path = self.loaded_file
        else:
            # Ordner characters/ anlegen, falls nicht vorhanden
            os.makedirs("characters", exist_ok=True)

            # Dateiname z. B. "characters/<uuid>_<name>.json"
            safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
            if not safe_name:
                safe_name = "unbenannt"
            target_path = os.path.join("characters", f"{self.char_id} - {safe_name}.json")

            # Das merken wir uns für zukünftige Saves in dieser Session
            self.loaded_file = target_path

        # JSON schreiben
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(character, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Erfolg", f"Charakter '{name}' wurde gespeichert:\n{target_path}")
        self.accept()



    def load_character_data(self, character, file_path):
        """Befüllt das Formular mit den Daten eines geladenen Charakters."""
        self.loaded_file = file_path

        # Datei & ID merken
        self.loaded_file = file_path
        self.char_id = character.get("id", str(uuid.uuid4()))
        # Basisfelder
        self.name_input.setText(character.get("name", ""))
        self.class_input.setCurrentText(character.get("class", "Krieger"))
        self.gender_input.setCurrentText(character.get("gender", "Männlich"))
        self.age_input.setText(str(character.get("age", "")))
        self.base_hitpoints = int(character.get("hitpoints", 0))
        self.hitpoints_input.setText(str(self.base_hitpoints))
        self.build_input.setCurrentText(character.get("build", "Durchschnittlich"))
        self.religion_input.setText(character.get("religion", ""))
        self.occupation_input.setText(character.get("occupation", ""))
        self.marital_status_input.setCurrentText(character.get("marital_status", "Ledig"))

        # Reset Strukturen für Fähigkeiten
        # (Falls du reload im gleichen Dialog machst, bräuchtest du hier ein hartes "Layout cleanup".
        # Wenn du pro Load eh neuen Dialog öffnest, ist das unkritisch.)
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {"Handeln": {}, "Wissen": {}, "Soziales": {}}
        self.skill_end_labels = {"Handeln": {}, "Wissen": {}, "Soziales": {}}

        # Fähigkeiten wiederherstellen
        for category, skills in character.get("skills", {}).items():
            for skill, value in skills.items():
                if category not in self.skills:
                    # Fallback, falls in Zukunft neue Kategorien auftauchen
                    self.skills[category] = []
                    self.skill_inputs[category] = {}
                    self.skill_end_labels[category] = {}
                    # Du müsstest hier theoretisch auch eine neue GroupBox + FormLayout bauen,
                    # aber momentan haben wir nur Handeln/Wissen/Soziales, also ignorieren wir das für jetzt.

                self.skills[category].append(skill)

                input_field = QLineEdit(str(value))
                input_field.textChanged.connect(self.update_points)

                end_label = QLabel("Endwert: 0")
                self.skill_end_labels[category][skill] = end_label

                remove_button = QPushButton("– Entfernen")
                remove_button.clicked.connect(lambda _, cat=category, skill=skill: self.remove_skill(cat, skill))

                h_layout = QHBoxLayout()
                h_layout.addWidget(input_field)
                h_layout.addWidget(end_label)
                h_layout.addWidget(remove_button)
                self.form_layouts[category].addRow(f"{skill}:", h_layout)

                self.skill_inputs[category][skill] = input_field

        # Items wiederherstellen (neues Format)
        self.item_groups = {}
        self.item_condition_links = {}

        for item_name, item_info in character.get("items", {}).items():
            attrs = item_info.get("attributes", {})
            item_uuid = item_info.get("id", str(uuid.uuid4()))
            linked_conditions = item_info.get("linked_conditions", [])

            item_group = QGroupBox(item_name)
            item_layout = QVBoxLayout()

            attr_layout = QFormLayout()
            for attr_name, attr_value in attrs.items():
                attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))

            add_attr_button = QPushButton("+ Neue Eigenschaft")
            add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))

            remove_button = QPushButton("- Item entfernen")
            remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))

            item_layout.addLayout(attr_layout)
            item_layout.addWidget(add_attr_button)
            item_layout.addWidget(remove_button)
            item_group.setLayout(item_layout)

            # Vor die beiden Buttons ("+ Neues Item", "+ Item aus Sammlung") einfügen:
            self.items_layout.insertWidget(self.items_layout.count() - 2, item_group)

            self.item_groups[item_name] = {
                "attributes": dict(attrs),
                "layout": item_layout,
                "group": item_group,
                "id": item_uuid,
                "linked_conditions": linked_conditions
            }

            self.item_condition_links[item_name] = linked_conditions

        # Zustands-Tracking komplett neu aufsetzen
        self.active_condition_by_id = {}
        self.condition_refcount = {}

        # 1) Zustände aus Items anhängen
        for item_name, cond_ids in self.item_condition_links.items():
            self.attach_item_conditions(item_name, cond_ids)

        # 2) Zustände aus dem Save explizit wiederherstellen (manuell aktivierte)
        for saved_name, cond_entry in character.get("conditions", {}).items():
            cid = cond_entry.get("id", str(uuid.uuid4()))
            cond_data = {
                "id": cid,
                "name": cond_entry.get("name", saved_name),
                "description": cond_entry.get("description", ""),
                "effect_type": cond_entry.get("effect_type", "keine Auswirkung"),
                "effect_target": cond_entry.get("effect_target", ""),
                "effect_value": cond_entry.get("effect_value", 0),
            }

            # Refcount erhöhen -> Zustand ist aktiv laut Save
            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            if cid not in self.active_condition_by_id:
                # Zustand ist noch nicht durch ein Item gekommen -> wir müssen ihn rendern
                self.active_condition_by_id[cid] = cond_data
                self.render_condition_block_from_condition_data(cid, cond_data, source_item=None)
            else:
                # Zustand kam schon durch ein Item rein, hat also schon ein _widget.
                # Wir wollen ihn nur "aufwerten", damit er nicht verschwindet, wenn Item entfernt wird.
                # Das ist schon durch den refcount erledigt.
                pass

        # WICHTIG:
        # condition_groups NICHT hier manuell bauen!
        # Stattdessen den zentralen Weg benutzen:
        self.recalculate_conditions_effects()

        # Skills / Endwerte aktualisieren
        self.update_points()
        # Charakter Rolle
        role = character.get("role", "pc")
        if role == "npc":
            self.role_input.setCurrentText("NSC / Gegner")
        else:
            self.role_input.setCurrentText("Spielercharakter")


class DiceRollDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Würfelprobe")
        self.setGeometry(300, 300, 400, 300)

        self.characters = load_all_characters_from_folder()
        self.current_char = None  # dict mit allen Daten des ausgewählten Charakters
        self.char_effective = None  # vorberechnete Strukturen (siehe unten)

        # Widgets
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 1) Charakter-Auswahl
        self.char_select = QComboBox()
        if self.characters:
            for c in self.characters:
                self.char_select.addItem(c["display"])
        else:
            self.char_select.addItem("<<kein Charakter gefunden>>")
        self.char_select.currentIndexChanged.connect(self.on_character_changed)
        form.addRow("Charakter:", self.char_select)

        # 2) Fertigkeit / Kategorie Auswahl
        self.skill_select = QComboBox()
        self.skill_select.currentIndexChanged.connect(self.on_skill_changed)
        form.addRow("Fertigkeit / Kategorie:", self.skill_select)

        # 3) Endwert-Anzeige (read only)
        self.endwert_display = QLineEdit()
        self.endwert_display.setReadOnly(True)
        form.addRow("Endwert:", self.endwert_display)

        # 4) Bonus/Malus Eingabe (Erleichtern um ...)
        self.bonus_input = QLineEdit()
        self.bonus_input.setPlaceholderText("z. B. 5 oder -10")
        self.bonus_input.textChanged.connect(self.update_effective_target_value)
        form.addRow("Erleichtern um:", self.bonus_input)

        # 5) Wurf-Ergebnis Eingabe (1-100)
        self.roll_input = QLineEdit()
        self.roll_input.setPlaceholderText("z. B. 42 oder 100")
        form.addRow("Gewürfelter Wert:", self.roll_input)

        layout.addLayout(form)

        # Ergebnisfeld
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        # Button "Auswerten"
        self.eval_button = QPushButton("Auswerten")
        self.eval_button.clicked.connect(self.evaluate_roll)
        layout.addWidget(self.eval_button)

        layout.addStretch()

        # Initial: ersten Charakter laden (falls vorhanden)
        if self.characters:
            self.on_character_changed(0)

    # --- Hilfslogik zur Charakterberechnung ---

    def compute_effective_values_for_character(self, char_data):
        """
        Liefert ein Dict mit:
         {
           "categories": {cat: effective_cat_value, ...},
           "skills": {skill: effective_skill_value, ...}
         }
        Zustände ('missionsweit') werden eingerechnet.
        """

        # 1. Basiswerte sammeln (aus gespeichertem Charakter)
        #    -> base_skill_values[skill], base_category_base[cat]
        base_skill_values = {}
        base_category_sum = {}   # cat -> sum der rohen skill-werte
        base_category_values = {}  # cat -> kaufmännisch gerundet(sum/10)

        skills_by_cat = char_data.get("skills", {})
        for cat, skillmap in skills_by_cat.items():
            total = 0
            for skill, val in skillmap.items():
                try:
                    val_int = int(val)
                except:
                    val_int = 0
                base_skill_values[skill] = val_int
                total += val_int
            # Kategorie-Basiswert wie im Editor: kaufmännisch_runden(total/10)
            base_category_values[cat] = kaufmaennisch_runden(total / 10)
            base_category_sum[cat] = total  # nur falls wir's mal brauchen später

        # 2. Zustands-Modifikatoren sammeln
        #    Wir schauen NUR auf effect_type == "missionsweit"
        skill_mods = {}
        category_mods = {}

        conds = char_data.get("conditions", {})
        for cond_name, cond in conds.items():
            if cond.get("effect_type") != "missionsweit":
                continue

            target = cond.get("effect_target", "")
            val = cond.get("effect_value", 0)
            try:
                val = int(val)
            except:
                val = 0

            # Fertigkeit: XYZ
            if target.startswith("Fertigkeit: "):
                skill_name = target.replace("Fertigkeit: ", "", 1).strip()
                skill_mods[skill_name] = skill_mods.get(skill_name, 0) + val

            # Kategoriewert: XYZ
            elif target.startswith("Kategoriewert: "):
                cat_name = target.replace("Kategoriewert: ", "", 1).strip()
                category_mods[cat_name] = category_mods.get(cat_name, 0) + val

            # Hinweis: Geistesblitzpunkte buffen wir fürs Würfeln erstmal nicht separat,
            # da du gesagt hast, wir können auf Kategorien/Skills würfeln.
            # Falls du später auch direkte Geistesblitzpunkte-Würfe willst,
            # müssten wir die hier berücksichtigen.

        # 3. effektive Kategorien anwenden
        effective_categories = {}
        for cat, base_val in base_category_values.items():
            effective_categories[cat] = base_val + category_mods.get(cat, 0)

        # 4. effektive Skills:
        #    effektiver Skillwert = Basis Skill + Skill-Mods + effektiver Kategorienwert (der Kategorie, zu der der Skill gehört)
        effective_skills = {}
        for cat, skillmap in skills_by_cat.items():
            cat_val_effective = effective_categories.get(cat, 0)
            for skill, val in skillmap.items():
                base_val = base_skill_values.get(skill, 0)
                mod_val = skill_mods.get(skill, 0)
                effective_skills[skill] = base_val + mod_val + cat_val_effective

        return {
            "categories": effective_categories,
            "skills": effective_skills,
        }

    # --- UI-Callbacks ---

    def on_character_changed(self, index):
        """Wird gerufen, wenn im DropDown ein anderer Charakter gewählt wurde."""
        if not self.characters:
            self.current_char = None
            self.skill_select.clear()
            self.endwert_display.setText("")
            return

        chosen = self.characters[index]
        self.current_char = chosen["data"]

        # effektive Werte vorberechnen
        self.char_effective = self.compute_effective_values_for_character(self.current_char)

        # Skill-Liste neu aufbauen
        # Wir bieten zuerst Kategorien, dann einen Trenner, dann Skills
        self.skill_select.blockSignals(True)
        self.skill_select.clear()

        # Kategorien
        for cat_name in self.char_effective["categories"].keys():
            self.skill_select.addItem(f"[Kategorie] {cat_name}")

        # Trenner (optional; nur wenn es beides gibt)
        if self.char_effective["categories"] and self.char_effective["skills"]:
            self.skill_select.addItem("----------")

        # Skills
        for skill_name in self.char_effective["skills"].keys():
            self.skill_select.addItem(skill_name)

        self.skill_select.blockSignals(False)

        # direkt erste sinnvolle Auswahl setzen
        if self.skill_select.count() > 0:
            self.skill_select.setCurrentIndex(0)
            self.on_skill_changed(0)
        else:
            self.endwert_display.setText("")

    def on_skill_changed(self, index):
        """Immer wenn eine andere Fertigkeit/Kategorie gewählt wird -> Endwert neu anzeigen."""
        self.update_endwert_display()
        self.update_effective_target_value()

    def current_selected_value(self):
        """
        Ermittelt den reinen Endwert (ohne 'Erleichtern um') für die aktuell
        ausgewählte Zeile der Combobox.
        """
        if not self.char_effective or self.skill_select.count() == 0:
            return 0

        sel = self.skill_select.currentText().strip()

        if sel.startswith("[Kategorie] "):
            cat_name = sel.replace("[Kategorie] ", "", 1)
            return self.char_effective["categories"].get(cat_name, 0)

        if sel == "----------":
            return 0

        # sonst ist es ein Skill
        return self.char_effective["skills"].get(sel, 0)

    def update_endwert_display(self):
        """
        Zeigt den 'Endwert' (also Chance %) ohne Bonus/Malus im readonly Feld.
        """
        base_val = self.current_selected_value()
        self.endwert_display.setText(str(base_val))

    def update_effective_target_value(self):
        """
        Diese Funktion könntest du benutzen, falls du live irgendwo anzeigen willst:
        'Effektive Zielchance nach Erleichterung'.
        Gerade schreiben wir sie nur, damit der Wert da ist, bevor evaluate_roll ruft.
        """
        # nothing to update live in UI (optional field if du's anzeigen willst)
        pass

    # --- Auswertung der Probe ---

    def evaluate_roll(self):
        """
        Liest:
          - Endwert (mit Zuständen usw.)
          - Bonus/Malus ("Erleichtern um")
          - Gewürfelte Zahl
        und bestimmt Erfolg + kritisch? + kritisch gut/schlecht?
        """

        # 1) Grundchance
        base_chance = self.current_selected_value()

        # 2) Bonus/Malus
        bonus_txt = self.bonus_input.text().strip()
        if bonus_txt == "":
            bonus_val = 0
        else:
            try:
                bonus_val = int(bonus_txt)
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Bitte eine ganze Zahl bei 'Erleichtern um' eingeben (z. B. 5 oder -10).")
                return

        final_chance = base_chance + bonus_val
        # clamp sinnvoll? In HTBAH kann man auch theoretisch über 100 kommen (= auto success?),
        # das Regelwerk lässt Spielleiter*innen da Freiheit. Wir clampen NICHT hart, aber für
        # die kritische Auswertung brauchen wir den effektiven Fähigkeitswert zwischen 0 und 100.
        # Für die Krit-Bereiche verwenden wir eine geclampte Variante:
        crit_basis = max(0, min(100, final_chance))

        # 3) Wurf lesen
        roll_txt = self.roll_input.text().strip()
        try:
            roll_val = int(roll_txt)
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Bitte das tatsächliche Würfelergebnis (1-100) als ganze Zahl eingeben.")
            return

        # Spezialfall: 0 ("0 + 00" auf den Würfeln) ist das gleiche wie 100 (kritischer Fehlschlag)
        if roll_val == 0:
            roll_val = 100

        if not (1 <= roll_val <= 100):
            QMessageBox.warning(self, "Fehler", "Würfelwert muss zwischen 1 und 100 liegen (0 zählt als 100).")
            return

        # 4) Erfolg / Fehlschlag bestimmen
        # Erfolg, wenn roll <= final_chance
        is_success = (roll_val <= final_chance)

        # 5) Kritisch?
        # laut Regel:
        # - kritischer Erfolg:
        #   * immer bei 1
        #   * oder innerhalb der ersten 10% des Fähigkeitswertes
        #     -> wenn Fähigkeitswert=70 => 7% => 1..7
        # - kritischer Fehlschlag:
        #   * immer bei 100
        #   * oder innerhalb der letzten 10% der "Unfähigkeit"
        #     Unfähigkeit = 100 - Fähigkeitswert
        #     Bei 70 => Unfähigkeit=30 => 3% kritisch => 97..100
        #
        # WICHTIG: Diese Grenzen berechnen wir mit crit_basis (geclampter final_chance 0..100)

        ability = crit_basis
        inability = 100 - ability

        crit_success_threshold = max(1, kaufmaennisch_runden(ability / 10)) # z.B. 70 -> 7
        crit_fail_threshold = max(1, kaufmaennisch_runden(inability / 10))  # z.B. 30 -> 3

        # Bereiche:
        # krit. Erfolg: 1 .. crit_success_threshold
        crit_success_low = 1
        crit_success_high = crit_success_threshold

        # krit. Fehlschlag: 100-crit_fail_threshold+1 .. 100
        crit_fail_low = 100 - crit_fail_threshold + 1
        crit_fail_high = 100

        # Immer-Sonderregeln
        if roll_val == 1:
            is_crit_success = True
        else:
            is_crit_success = (roll_val >= crit_success_low and roll_val <= crit_success_high)

        if roll_val == 100:
            is_crit_fail = True
        else:
            is_crit_fail = (roll_val >= crit_fail_low and roll_val <= crit_fail_high)

        # Falls er gleichzeitig in beiden kritischen Bereichen liegen könnte (extreme Modifikatoren),
        # geben wir harte Regeln Vorrang:
        # 1 hat immer Vorrang als krit. Erfolg
        # 100 hat immer Vorrang als krit. Fehlschlag
        # Sonst sollten sich die Bereiche eh nicht überlappen.

        # 6) Ergebnis-Text bauen
        if is_success:
            outcome_text = "Erfolg"
        else:
            outcome_text = "Fehlschlag"

        if is_crit_success:
            outcome_text = "KRITISCHER ERFOLG ✅ (" + outcome_text + ")"
        elif is_crit_fail:
            outcome_text = "KRITISCHER FEHLSCHLAG ❌ (" + outcome_text + ")"

        # Noch ein paar Debug-Infos, damit der SL alles sieht
        details = (
            f"Grundchance: {base_chance}  |  Modifikator: {bonus_val:+}  "
            f"→ Zielwert: {final_chance}\n"
            f"Wurf: {roll_val}\n"
        )

        self.result_label.setText(outcome_text + "\n\n" + details)

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

        new_item_button = QPushButton("Neues Item erstellen", self)
        new_item_button.clicked.connect(self.create_new_item)
        layout.addWidget(new_item_button)

        load_item_button = QPushButton("Bestehendes Item laden", self)
        load_item_button.clicked.connect(self.load_item)
        layout.addWidget(load_item_button)

        new_condition_button = QPushButton("Neuen Zustand erstellen", self)
        new_condition_button.clicked.connect(self.create_new_condition)
        layout.addWidget(new_condition_button)

        load_condition_button = QPushButton("Bestehenden Zustand laden", self)
        load_condition_button.clicked.connect(self.load_condition)
        layout.addWidget(load_condition_button)

        roll_button = QPushButton("Würfelprobe", self)
        roll_button.clicked.connect(self.open_roll_dialog)
        layout.addWidget(roll_button)

        combat_button = QPushButton("Kampf starten", self)
        combat_button.clicked.connect(self.start_combat)
        layout.addWidget(combat_button)

        layout.addStretch()


    def _collect_all_condition_targets_from_all_characters(self):
        """
        Sammelt aus allen gespeicherten Charakteren:
        - alle Fertigkeiten
        - alle Kategorien (Handeln / Wissen / Soziales / ...)
        - alle Geistesblitzpunkte-Kategorien

        Liefert Tupel (skill_targets, category_targets, inspiration_targets)
        so wie CharacterCreationDialog._build_condition_target_lists,
        nur eben über ALLE Chars gemergt.
        """
        skill_set = set()
        category_set = set()

        characters_dir = "characters"
        if os.path.isdir(characters_dir):
            for fname in os.listdir(characters_dir):
                if not fname.lower().endswith(".json"):
                    continue
                full_path = os.path.join(characters_dir, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue  # kaputte Datei ignorieren

                # skills ist wie:
                # {
                #   "Handeln": {"Schleichen": 35, "Klettern": 20},
                #   "Wissen": {...},
                #   "Soziales": {...}
                # }
                skills_block = data.get("skills", {})
                for category_name, skills_dict in skills_block.items():
                    # Kategorie merken
                    category_set.add(category_name)

                    # Skills merken
                    for skill_name in skills_dict.keys():
                        skill_set.add(skill_name)

        # Jetzt Listen im passenden Format bauen
        skill_targets = [f"Fertigkeit: {skill}" for skill in sorted(skill_set)]
        category_targets = [f"Kategoriewert: {cat}" for cat in sorted(category_set)]
        inspiration_targets = [f"Geistesblitzpunkte: {cat}" for cat in sorted(category_set)]

        return skill_targets, category_targets, inspiration_targets

    def start_combat(self):
        dlg = CombatDialog(self)
        dlg.exec()


    def start_character_creation(self):
        dialog = CharacterCreationDialog(self)
        dialog.char_id = str(uuid.uuid4())  # neue frische ID vergeben
        dialog.exec()


    def load_character(self):
        # Verzeichnis sicherstellen
        if not os.path.exists("characters"):
            QMessageBox.information(self, "Hinweis", "Es wurden noch keine Charaktere gespeichert.")
            return

        # Alle JSON-Dateien einsammeln
        candidates = []
        for fname in os.listdir("characters"):
            if fname.lower().endswith(".json"):
                full_path = os.path.join("characters", fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # wir erwarten ein einzelnes Charakter-Objekt (unser neues Format)
                    char_name = data.get("name", "(unbenannt)")
                    char_class = data.get("class", "?")
                    char_age = data.get("age", "?")
                    char_id = data.get("id", "???")

                    display = f"{char_name} | {char_class}, {char_age} Jahre [{char_id[:8]}...]"
                    candidates.append((display, full_path, data))
                except Exception:
                    # Datei ignorieren, wenn sie nicht lesbar ist
                    pass

        if not candidates:
            QMessageBox.information(self, "Hinweis", "Keine gültigen Charakterdateien gefunden.")
            return

        # Liste der Anzeigenamen für Auswahl
        display_names = [c[0] for c in candidates]

        choice, ok = QInputDialog.getItem(
            self,
            "Charakter wählen",
            "Welchen Charakter möchtest du laden?",
            display_names,
            0,
            False
        )
        if not ok:
            return

        idx = display_names.index(choice)
        chosen_display, chosen_path, chosen_data = candidates[idx]

        # Dialog öffnen und Daten rein
        dialog = CharacterCreationDialog(self)
        dialog.load_character_data(chosen_data, chosen_path)
        dialog.exec()


    def create_new_item(self):
        """Öffnet den Item-Editor leer für ein neues Item."""
        dlg = ItemEditorDialog(self)
        # Neue UUID direkt setzen, damit beim Speichern klar ist, wer das ist
        dlg.item_id = str(uuid.uuid4())
        dlg.exec()

    def open_roll_dialog(self):
        dlg = DiceRollDialog(self)
        dlg.exec()

    def load_item(self):
        """Lädt items.json ODER eine andere Datei, lässt den Nutzer ein Item auswählen, öffnet es im Editor."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Item-Datei öffnen",
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

        # Erwartet { "items": [ {...}, {...} ] }
        if not (isinstance(data, dict) and "items" in data and isinstance(data["items"], list)):
            QMessageBox.warning(self, "Fehler", "In der ausgewählten Datei wurden keine Items gefunden.")
            return

        items_list = data["items"]
        if not items_list:
            QMessageBox.warning(self, "Fehler", "Die Datei enthält keine Items.")
            return

        # Falls mehrere Items drin sind: den Nutzer auswählen lassen
        item_names = [f"{it.get('name','(unbenannt)')} [{it.get('id','?')}]" for it in items_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Item auswählen",
            "Welches Item möchtest du bearbeiten?",
            item_names,
            0,
            False
        )
        if not ok:
            return

        # anhand der Auswahl das konkrete Item raussuchen
        chosen_index = item_names.index(choice)
        chosen_item = items_list[chosen_index]

        # Editor öffnen und Item laden
        dlg = ItemEditorDialog(self)
        dlg.load_item_data(chosen_item, file_name)
        dlg.exec()

    def create_new_condition(self):
        """Öffnet den Zustands-Editor leer zum Erstellen eines neuen Zustands."""

        # Sammle alle sinnvollen Ziele aus ALLEN gespeicherten Charakteren
        skill_targets, cat_targets, insp_targets = self._collect_all_condition_targets_from_all_characters()

        dlg = ConditionEditorDialog(
            parent=self,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.condition_id = str(uuid.uuid4())  # direkt frische UUID vergeben
        dlg.exec()


    def load_condition(self):
        """Lädt eine conditions.json (oder andere Datei), lässt den Nutzer einen Zustand wählen und öffnet ihn im Editor."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Zustands-Datei öffnen",
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

        # erwartet { "conditions": [ {...}, {...} ] }
        if not (isinstance(data, dict) and "conditions" in data and isinstance(data["conditions"], list)):
            QMessageBox.warning(self, "Fehler", "In der ausgewählten Datei wurden keine Zustände gefunden.")
            return

        conditions_list = data["conditions"]
        if not conditions_list:
            QMessageBox.warning(self, "Fehler", "Die Datei enthält keine Zustände.")
            return

        # Auswahl anzeigen
        cond_choices = [
            f"{c.get('name', '(unbenannt)')} [{c.get('id','?')}]"
            for c in conditions_list
        ]

        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du bearbeiten?",
            cond_choices,
            0,
            False
        )
        if not ok:
            return

        chosen_index = cond_choices.index(choice)
        chosen_condition = conditions_list[chosen_index]

        dlg = ConditionEditorDialog(self)
        dlg.load_condition_data(chosen_condition, file_name)
        dlg.exec()

class CombatDialog(QDialog):
    def __init__(self, parent=None):
        self.surprised_ids = set()

        super().__init__(parent)

        self.setWindowTitle("Kampf-Übersicht")
        self.setGeometry(200, 200, 600, 500)

        # --- State ---
        # Liste aller aktiven Kämpfer im aktuellen Kampf
        # each: { "instance_id", "source_char_id", "display_name", "team", "current_hp", "max_hp" }
        self.battle_actors = []

        # Teams verwalten
        self.teams = ["Team A", "Team B"]

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Team-Auswahl
        self.team_select = QComboBox()
        self.team_select.addItems(self.teams)
        self.add_team_button = QPushButton("+ Team hinzufügen")
        self.add_team_button.clicked.connect(self.add_new_team)

        left_layout.addWidget(QLabel("Neuen Kämpfer hinzufügen:"))
        left_layout.addWidget(QLabel("Team:"))
        left_layout.addWidget(self.team_select)
        left_layout.addWidget(self.add_team_button)

        # Buttons: PC / NSC hinzufügen
        self.add_pc_button = QPushButton("Spielercharakter hinzufügen")
        self.add_pc_button.clicked.connect(lambda: self.add_combatant(from_role="pc"))
        left_layout.addWidget(self.add_pc_button)

        self.add_npc_button = QPushButton("NSC hinzufügen")
        self.add_npc_button.clicked.connect(lambda: self.add_combatant(from_role="npc"))
        left_layout.addWidget(self.add_npc_button)

        left_layout.addStretch()

        # Rechts: aktuelle Kampfteilnehmer
        right_layout.addWidget(QLabel("Teilnehmer im Kampf:"))
        self.actors_layout = QVBoxLayout()
        right_layout.addLayout(self.actors_layout)
        right_layout.addStretch()

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.start_battle_button = QPushButton("Kampf starten (Initiative bestimmen)")
        self.set_surprise_button = QPushButton("Überraschungsrunde festlegen")
        self.set_surprise_button.clicked.connect(self.set_surprise_round)
        right_layout.addWidget(self.set_surprise_button)
        self.start_battle_button.clicked.connect(self.start_battle)
        right_layout.addWidget(self.start_battle_button)

    def load_character_data(self, char_id):
        """Hilfsfunktion: Lädt Charakterdaten aus ./characters anhand der ID."""
        folder = "characters"
        if not os.path.exists(folder):
            return None

        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        return data
            except Exception:
                continue

        return None

    def set_surprise_round(self):
        """Öffnet den Dialog, um überrascht markierte Kämpfer zu wählen"""
        if not self.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = SurpriseDialog(self.battle_actors, self)
        if dlg.exec():
            self.surprised_ids = dlg.get_surprised_ids()
            if self.surprised_ids:
                names = [
                    a["display_name"]
                    for a in self.battle_actors
                    if a["instance_id"] in self.surprised_ids
                ]
                msg = "<br>".join(names)
                QMessageBox.information(
                    self, "Überraschungsrunde",
                    f"Folgende Kämpfer sind überrascht:<br><br>{msg}"
                )
            else:
                QMessageBox.information(self, "Überraschungsrunde", "Niemand ist überrascht.")

    def start_battle(self):
        if not self.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = InitiativeDialog(self.battle_actors, self, surprised_ids=self.surprised_ids)
        if dlg.exec():
            order = dlg.get_sorted_initiative()
            if order:
                self.set_initiative_order(order)

    def set_initiative_order(self, order):
        """Speichert die Reihenfolge und zeigt sie im CombatDialog an"""
        self.surprised_ids = getattr(self, "surprised_ids", set())
        self.turn_order = [r["actor"] for r in order]
        self.current_turn_index = 0
        self.round_number = 1 
        # Falls noch kein UI-Bereich existiert, erstellen wir ihn
        if not hasattr(self, "turn_area"):
            self.turn_area = QVBoxLayout()

            self.current_turn_label = QLabel()
            self.turn_area.addWidget(self.current_turn_label)

            self.order_list_widget = QTextEdit()
            self.order_list_widget.setReadOnly(True)
            self.turn_area.addWidget(self.order_list_widget)

            # Buttons
            btns = QHBoxLayout()
            self.next_turn_btn = QPushButton("▶️ Nächster Zug")
            self.next_turn_btn.clicked.connect(self.next_turn)
            btns.addWidget(self.next_turn_btn)

            self.reset_round_btn = QPushButton("🔁 Neue Runde")
            self.reset_round_btn.clicked.connect(self.reset_round)
            btns.addWidget(self.reset_round_btn)

            self.action_btn = QPushButton("⚔️ Zug ausführen")
            self.action_btn.clicked.connect(self.run_current_turn)
            btns.addWidget(self.action_btn)

            self.turn_area.addLayout(btns)

            # Füge das unten an (z. B. unter den Teilnehmern)
            self.layout().addLayout(self.turn_area)

        # Kampf-Log (Nachrichtenfeld)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Kampf-Log...")
        self.layout().addWidget(self.log_box)
        self.refresh_turn_display()

    def run_current_turn(self):
        """Führt den Zug des aktuell an der Reihe befindlichen Kämpfers aus."""
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        current_actor = self.turn_order[self.current_turn_index]

        # Den eigentlichen Zug durchführen (inkl. Überraschungs-Check)
        self.execute_turn(current_actor)


    def log_message(self, text):
        """Fügt eine Nachricht in das Kampf-Log ein."""
        self.log_box.append(f"• {text}")


    def execute_turn(self, actor):
        # 1. Check: ist der Actor in Runde 1 überrascht?
        if self.is_actor_surprised_and_blocked(actor):
            self.log_message(
                f"{actor['display_name']} ist überrascht und setzt in Runde {self.round_number} aus."
            )
            return

        current_actor = self.turn_order[self.current_turn_index]
        actor_name = current_actor["display_name"]

        # Ziel wählen
        targets = [a for a in self.battle_actors if a["instance_id"] != current_actor["instance_id"]]
        if not targets:
            QMessageBox.information(self, "Hinweis", "Keine Ziele verfügbar.")
            return

        target_names = [t["display_name"] for t in targets]
        target_choice, ok = QInputDialog.getItem(self, "Ziel wählen", f"{actor_name} greift an:", target_names, 0, False)
        if not ok:
            return

        target = next(t for t in targets if t["display_name"] == target_choice)

        # Fertigkeit / Kategorie wählen
        attack_skill = self.select_skill_dialog(current_actor)
        if not attack_skill:
            return

        # Angriffswurf
        self.log_message(f"{actor_name} greift {target['display_name']} mit {attack_skill} an...")
        success, crit = self.perform_roll(current_actor, attack_skill)

        # Ergebnis auswerten
        if not success:
            result_text = "Angriff verfehlt." if not crit else "Kritischer Fehlschlag!"
            self.log_message(f"❌ {result_text}")
            return

        # Erfolg
        result_text = "Treffer!" if not crit else "⚡ Kritischer Treffer!"
        self.log_message(f"➡️ {result_text}")

        # 🔥 Kritischer Erfolg: keine Parade erlaubt
        if crit:
            self.log_message(f"⚠️ {target['display_name']} kann den Angriff aufgrund eines kritischen Erfolgs nicht parieren!")
            return

        # Wenn kein kritischer Treffer → prüfen, ob Ziel parieren möchte
        parry_choice = QMessageBox.question(
            self,
            "Parade?",
            f"{target['display_name']} wurde getroffen. Möchte er/sie parieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if parry_choice == QMessageBox.StandardButton.No:
            self.log_message(f"{target['display_name']} entscheidet sich, nicht zu parieren.")
            return

        # Parier-Fertigkeit / Kategorie wählen
        self.log_message(f"{target['display_name']} versucht, den Angriff zu parieren...")
        parry_skill = self.select_skill_dialog(target)
        if not parry_skill:
            return

        parry_success, parry_crit = self.perform_roll(target, parry_skill)

        if parry_success:
            text = "Parade gelungen!" if not parry_crit else "💥 Kritische Parade!"
            self.log_message(f"🛡️ {text}")
        else:
            text = "Parade misslungen." if not parry_crit else "😬 Kritischer Fehlschlag bei der Parade!"
            self.log_message(f"❌ {text}")


    def select_skill_dialog(self, actor):
        # Lade Charakterdaten
        char = self.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self, "Fehler", "Charakterdaten konnten nicht geladen werden.")
            return None

        # Fertigkeiten und Kategorien zusammenstellen
        skill_names = []
        for cat, skills in char.get("skills", {}).items():
            skill_names.append(cat)  # Kategorie selbst
            skill_names.extend(skills.keys())

        choice, ok = QInputDialog.getItem(self, "Fertigkeit wählen", "Angriffs-Fertigkeit:", skill_names, 0, False)
        return choice if ok else None

    def perform_roll(self, actor, skill_name):
        """Führt eine manuelle Würfelprobe durch, die der Spielleiter eingibt."""
        char = self.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self, "Fehler", f"Konnte Charakterdaten für {actor['display_name']} nicht laden.")
            return False, False

        char.setdefault("skills", {})
        char.setdefault("category_scores", {})

        skills = char["skills"]

        # Prüfen, ob direkt auf eine Kategorie (z. B. "Handeln") gewürfelt wird
        if skill_name in char["category_scores"]:
            category = skill_name
            skill_val = 0
            category_val = char["category_scores"].get(category, 0)
        else:
            # Kategorie anhand der Fertigkeiten suchen
            category = None
            for cat, skillset in skills.items():
                if skill_name in skillset:
                    category = cat
                    break

            if category is None:
                QMessageBox.warning(self, "Fehler", f"Fertigkeit oder Kategorie '{skill_name}' nicht im Charakter gefunden.")
                return False, False

            skill_val = skills[category].get(skill_name, 0)
            category_val = char["category_scores"].get(category, 0)

        base_val = skill_val + category_val

        # 🎲 Spielleiter gibt realen Wurf ein
        roll_str, ok = QInputDialog.getText(
            self,
            f"Wurf für {actor['display_name']}",
            f"Bitte gewürfelten Wurf (1–100) für {skill_name} ({category}) eingeben:"
        )
        if not ok:
            return False, False

        try:
            roll = int(roll_str)
            if roll == 0:
                roll = 100
            if not 1 <= roll <= 100:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Ungültiger Wurfwert. Bitte 1–100 eingeben (0 = 100).")
            return False, False

        # Erfolg / Kritisch prüfen
        crit = roll in (1, 100)
        success = roll <= base_val

        # Log-Eintrag
        if hasattr(self, "log_message"):
            if skill_val > 0:
                details = f"Wurf auf {skill_name} ({category})"
            else:
                details = f"Wurf auf Kategorie {category}"
            self.log_message(
                f"{actor['display_name']} {details}: "
                f"Wurf={roll}, Zielwert={base_val} → {'✔️ Erfolg' if success else '❌ Fehlschlag'}"
                + (" (Kritisch!)" if crit else "")
            )

        return success, crit




    def handle_parry_phase(self, attacker, target):
        """Ermöglicht dem Ziel, einen Blockversuch zu starten."""
        # Paradezähler initialisieren
        if not hasattr(self, "parry_used"):
            self.parry_used = {}

        target_id = target["instance_id"]
        if self.parry_used.get(target_id, False):
            self.log_message(f"{target['display_name']} hat in dieser Runde bereits pariert.")
            return

        reply = QMessageBox.question(
            self, "Parade?", f"Soll {target['display_name']} den Angriff parieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            self.log_message(f"{target['display_name']} versucht nicht zu parieren.")
            return

        # Parier-Fertigkeit wählen
        parry_skill = self.select_skill_dialog(target)
        if not parry_skill:
            return

        success, crit = self.perform_roll(target, parry_skill)
        self.parry_used[target_id] = True

        if success:
            self.log_message(f"🛡️ {target['display_name']} pariert erfolgreich mit {parry_skill}!")
        else:
            self.log_message(f"💥 {target['display_name']} verfehlt die Parade!")


    def refresh_turn_display(self):
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        current_actor = self.turn_order[self.current_turn_index]

        # Kopfzeile mit Rundeninfo
        self.current_turn_label.setText(
            f"<b>Runde {self.round_number}</b><br>"
            f"<b>Aktuell am Zug:</b> {current_actor['display_name']} ({current_actor['team']})"
        )

        # gesamte Reihenfolge anzeigen (inkl. Überraschungs-Markierung)
        text = ""
        for i, actor in enumerate(self.turn_order, start=1):
            prefix = "➡️ " if i - 1 == self.current_turn_index else ""
            surprised = actor["instance_id"] in getattr(self, "surprised_ids", set())
            surprise_icon = " 😮" if surprised else ""
            surprise_style = (
                'style="color:gray; font-style:italic;"'
                if surprised and self.round_number == 1
                else ""
            )
            skip_note = (
                " (setzt in Runde 1 aus)" if surprised and self.round_number == 1 else ""
            )

            text += (
                f'{prefix}{i}. '
                f'<span {surprise_style}>{actor["display_name"]}{surprise_icon} ({actor["team"]}){skip_note}</span><br>'
            )

        self.order_list_widget.setHtml(text)


    def next_turn(self):
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        # Endlosschutz – z. B. wenn alle in Runde 1 überrascht wären
        max_iterations = len(self.turn_order) * 2

        while max_iterations > 0:
            max_iterations -= 1

            self.current_turn_index += 1
            if self.current_turn_index >= len(self.turn_order):
                # Neue Runde starten
                self.round_number += 1
                self.current_turn_index = 0
                QMessageBox.information(self, "Neue Runde", f"Runde {self.round_number} beginnt!")

            current_actor = self.turn_order[self.current_turn_index]

            # Überraschungsregel: In Runde 1 dürfen überraschte Kämpfer nicht handeln
            if hasattr(self.parent(), "surprised_ids") and self.round_number == 1:
                if current_actor["instance_id"] in self.parent().surprised_ids:
                    # Überspringen, Info ins Log
                    print(f"Übersprungen (überrascht): {current_actor['display_name']}")
                    continue  # direkt nächsten Kämpfer prüfen

            # Wenn kein Überspringen → regulärer Zug
            break

        self.refresh_turn_display()

    def reset_round(self):
        self.parry_used = {}
        if not hasattr(self, "turn_order") or not self.turn_order:
            return
        self.current_turn_index = 0
        QMessageBox.information(self, "Runde zurückgesetzt", "Die Initiative startet wieder bei Runde 1.")
        self.refresh_turn_display()


    def add_new_team(self):
        name, ok = QInputDialog.getText(self, "Neues Team", "Team-Name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.teams:
            QMessageBox.information(self, "Hinweis", "Team existiert bereits.")
            return
        self.teams.append(name)
        self.team_select.addItem(name)
        self.team_select.setCurrentText(name)

    def add_combatant(self, from_role):
        # from_role ist "pc" oder "npc"
        candidates = self.load_characters_by_role(from_role)
        if not candidates:
            QMessageBox.information(self, "Hinweis", f"Keine {from_role.upper()}-Charaktere gefunden.")
            return

        # Liste für User lesbar
        display_names = [c["display"] for c in candidates]

        choice, ok = QInputDialog.getItem(
            self,
            "Charakter wählen",
            "Wen willst du in den Kampf schicken?",
            display_names,
            0,
            False
        )
        if not ok:
            return

        idx = display_names.index(choice)
        chosen_char = candidates[idx]["data"]  # das echte JSON vom Charakter

        base_name = chosen_char.get("name", "Unbenannt")
        max_hp = chosen_char.get("hitpoints", 0)
        source_id = chosen_char.get("id", "???")

        team_name = self.team_select.currentText()

        # Wenn NPC → nach Anzahl fragen
        count = 1
        if from_role == "npc":
            count_txt, ok = QInputDialog.getText(
                self,
                "Anzahl",
                f"Wieviele Instanzen von '{base_name}' hinzufügen?"
            )
            if not ok:
                return
            try:
                count_val = int(count_txt)
                if count_val < 1:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Bitte eine ganze Zahl >=1 eingeben.")
                return
            count = count_val

        # Instanzen erzeugen
        for i in range(count):
            inst_name = base_name if count == 1 else f"{base_name} #{i+1}"

            actor = {
                "instance_id": str(uuid.uuid4()),
                "source_char_id": source_id,
                "display_name": inst_name,
                "team": team_name,
                "current_hp": max_hp,
                "max_hp": max_hp,
            }
            self.battle_actors.append(actor)

        # UI neu aufbauen
        self.refresh_actor_list()

    def load_characters_by_role(self, role_filter):
        """
        role_filter ist "pc" oder "npc".
        Wir durchsuchen ./characters und lesen jeden JSON.
        Gibt Liste aus Dicts zurück:
        { "display": "...", "path": "...", "data": {...} }
        """
        results = []
        if not os.path.exists("characters"):
            return results

        for fname in os.listdir("characters"):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join("characters", fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("role", "pc") != role_filter:
                continue

            char_name = data.get("name", "(unbenannt)")
            char_class = data.get("class", "?")
            char_hp = data.get("hitpoints", "?")
            display = f"{char_name} [{char_class}] HP:{char_hp}"

            results.append({
                "display": display,
                "path": full_path,
                "data": data,
            })

        return results

    def refresh_actor_list(self):
        # Erstmal alles leerräumen
        while self.actors_layout.count():
            item = self.actors_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Für jede Instanz einen kleinen Block bauen
        for actor in self.battle_actors:
            box = QGroupBox(f"{actor['display_name']} ({actor['team']})")
            box.setStyleSheet("QGroupBox { font-weight:bold; }")
            v = QVBoxLayout()

            hp_label = QLabel(f"HP: {actor['current_hp']}/{actor['max_hp']}")
            v.addWidget(hp_label)

            # Buttons für HP +/- und Entfernen
            btn_row = QHBoxLayout()

            minus_btn = QPushButton("-1 HP")
            plus_btn = QPushButton("+1 HP")
            remove_btn = QPushButton("Entfernen")

            def make_minus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = max(0, a["current_hp"] - 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_plus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = min(a["max_hp"], a["current_hp"] + 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_remove(a=actor):
                def _inner():
                    self.battle_actors = [x for x in self.battle_actors if x["instance_id"] != a["instance_id"]]
                    self.refresh_actor_list()
                return _inner

            minus_btn.clicked.connect(make_minus())
            plus_btn.clicked.connect(make_plus())
            remove_btn.clicked.connect(make_remove())

            btn_row.addWidget(minus_btn)
            btn_row.addWidget(plus_btn)
            btn_row.addWidget(remove_btn)

            v.addLayout(btn_row)
            box.setLayout(v)
            self.actors_layout.addWidget(box)

    def is_actor_surprised_and_blocked(self, actor):
        """
        True genau dann, wenn dieser Actor in DIESER Runde nicht handeln darf.
        Regel: Runde 1 + Actor ist überrascht -> blockieren.
        Ab Runde 2 nie blockieren.
        """
        return (
            self.round_number == 1
            and actor["instance_id"] in self.surprised_ids
        )

class InitiativeDialog(QDialog):
    def __init__(self, battle_actors, parent=None, surprised_ids=None):
        super().__init__(parent)
        self.setWindowTitle("Initiative bestimmen")
        self.setGeometry(300, 200, 600, 500)

        self.battle_actors = battle_actors  # aus CombatDialog
        self.surprised_ids = surprised_ids or set()
        self.initiatives = {}  # instance_id → total_initiative

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Würfe für Initiative:</b>"))
        layout.addWidget(QLabel("Für jeden Kämpfer 1W10 (0 = 10) + Handeln + Bonus/Malus"))

        self.form_layout = QFormLayout()
        self.inputs = {}

        for actor in self.battle_actors:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)

            roll_input = QLineEdit()
            roll_input.setPlaceholderText("Wurf (1-10 oder 0=10)")
            bonus_input = QLineEdit()
            bonus_input.setPlaceholderText("Bonus/Malus")

            h.addWidget(QLabel(actor["display_name"] + (" 😮" if actor["instance_id"] in self.surprised_ids else "")))
            h.addWidget(roll_input)
            h.addWidget(bonus_input)
            self.inputs[actor["instance_id"]] = {
                "roll": roll_input,
                "bonus": bonus_input
            }
            self.form_layout.addRow(row)

        layout.addLayout(self.form_layout)

        self.calc_button = QPushButton("Initiative berechnen")
        self.calc_button.clicked.connect(self.calculate_initiative)
        layout.addWidget(self.calc_button)

        # Button-Leiste unten
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK (Initiative übernehmen)")
        self.ok_button.setEnabled(False)  # wird erst aktiv nach Berechnung
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)


        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        layout.addStretch()

    def calculate_initiative(self):
        # 1. Alle Würfe auslesen
        results = []
        for actor in self.battle_actors:
            inst_id = actor["instance_id"]
            roll_txt = self.inputs[inst_id]["roll"].text().strip()
            bonus_txt = self.inputs[inst_id]["bonus"].text().strip()

            try:
                roll_val = int(roll_txt)
            except ValueError:
                QMessageBox.warning(self, "Fehler", f"Ungültiger Wurfwert für {actor['display_name']}")
                return

            # 0 = 10 interpretieren
            if roll_val == 0:
                roll_val = 10

            try:
                bonus_val = int(bonus_txt) if bonus_txt else 0
            except ValueError:
                QMessageBox.warning(self, "Fehler", f"Ungültiger Bonus/Malus bei {actor['display_name']}")
                return

            # Handeln-Wert aus Charakterdaten
            handeln_value = self.get_handeln_value(actor["source_char_id"])

            total_initiative = roll_val + handeln_value + bonus_val

            results.append({
                "actor": actor,
                "roll": roll_val,
                "bonus": bonus_val,
                "handeln": handeln_value,
                "total": total_initiative
            })

        # 2. Sortierung:
        #   - Zuerst nach total (desc)
        #   - Bei Gleichstand: PC vor NPC
        #   - Dann alphabetisch als Fallback
        def sort_key(x):
            role = self.get_character_role(x["actor"]["source_char_id"])
            return (
                -x["total"],             # absteigend
                0 if role == "pc" else 1, # pc zuerst
                x["actor"]["display_name"].lower()
            )

        results.sort(key=sort_key)

        # 3. Ergebnis anzeigen
        text = "<b>Initiative-Reihenfolge:</b><br><br>"
        for idx, r in enumerate(results, start=1):
            role = self.get_character_role(r["actor"]["source_char_id"])
            role_display = "PC" if role == "pc" else "NSC"
            text += (
                f"{idx}. {r['actor']['display_name']} "
                f"({role_display}) → Wurf {r['roll']} + Handeln {r['handeln']} "
                f"+ Bonus {r['bonus']} = <b>{r['total']}</b><br>"
            )

        # Überraschungsinfo hinzufügen (falls vorhanden)
        if getattr(self.parent(), "surprised_ids", set()):
            surprised_names = [
                r["actor"]["display_name"]
                for r in results
                if r["actor"]["instance_id"] in self.parent().surprised_ids
            ]
            if surprised_names:
                text += (
                    "<br><b>Überrascht (setzen in Runde 1 aus):</b><br>"
                    + ", ".join(surprised_names)
                    + "<br>"
                )


        self.result_area.setHtml(text)
        # Speichere Reihenfolge für Rückgabe
        self.sorted_results = results
        self.ok_button.setEnabled(True)


    def get_sorted_initiative(self):
        """Gibt die berechnete Reihenfolge zurück"""
        if hasattr(self, "sorted_results"):
            return self.sorted_results
        return []


    def get_handeln_value(self, char_id):
        """Lädt den Charakter und berechnet den aktuellen Handeln-Wert"""
        char_file = None
        folder = "characters"
        if not os.path.exists(folder):
            return 0
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        char_file = data
                        break
            except Exception:
                continue

        if not char_file:
            return 0

        # Berechne Handeln-Wert wie im Charakterdialog
        skills = char_file.get("skills", {})
        handeln_skills = skills.get("Handeln", {})
        if not handeln_skills:
            return 0

        total = sum(int(v) for v in handeln_skills.values() if str(v).isdigit())
        return kaufmaennisch_runden(total / 10)

    def get_character_role(self, char_id):
        """Liest aus dem gespeicherten Charakter, ob es ein PC oder NSC ist"""
        folder = "characters"
        if not os.path.exists(folder):
            return "npc"
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        return data.get("role", "npc")
            except Exception:
                continue
        return "npc"


class SurpriseDialog(QDialog):
    def __init__(self, battle_actors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Überraschungsrunde festlegen")
        self.setGeometry(350, 250, 500, 400)

        self.battle_actors = battle_actors
        self.checkboxes = {}
        self.team_checkboxes = {}

        layout = QVBoxLayout(self)

        # Finde alle Teams
        teams = sorted(set(a["team"] for a in battle_actors))

        for team_name in teams:
            group = QGroupBox(team_name)
            vbox = QVBoxLayout()

            # Team-Gesamt-Checkbox
            team_cb = QCheckBox(f"Gesamtes Team '{team_name}' überrascht")
            self.team_checkboxes[team_name] = team_cb
            vbox.addWidget(team_cb)

            # Einzelne Kämpfer dieses Teams
            for actor in [a for a in battle_actors if a["team"] == team_name]:
                cb = QCheckBox(actor["display_name"])
                self.checkboxes[actor["instance_id"]] = cb
                vbox.addWidget(cb)

            # Wenn Team angehakt → alle untergeordneten Kämpfer aktivieren
            def make_handler(tn=team_name):
                def handler(state):
                    checked = state == Qt.CheckState.Checked.value
                    for aid, cb in self.checkboxes.items():
                        for a in self.battle_actors:
                            if a["instance_id"] == aid and a["team"] == tn:
                                cb.setChecked(checked)
                return handler

            team_cb.stateChanged.connect(make_handler())

            group.setLayout(vbox)
            layout.addWidget(group)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def get_surprised_ids(self):
        """Gibt Menge von instance_ids zurück, die überrascht sind"""
        return {aid for aid, cb in self.checkboxes.items() if cb.isChecked()}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())
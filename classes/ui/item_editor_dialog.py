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

## eigene klassen
from classes.ui.condition_editor_dialog import ConditionEditorDialog

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

        # Zustände, die diesem Item zugeordnet sind (Liste von Condition-UUIDs)
        self.linked_conditions = []

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

    ## ZUSTÄNDE IM ITEM DISPLAY

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

    ## LADEN UND SPEICHERN VON ITEMDATEN

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
        self.toggle_weapon_fields()


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

        # --- WICHTIG: richtige Widgets verwenden ---
        is_weapon = self.is_weapon_checkbox.isChecked()
        damage_formula = self.damage_formula_input.text().strip() if self.is_weapon_checkbox.isChecked() else ""

        item_obj = {
            "id": self.item_id,
            "name": name,
            "description": description,
            "attributes": attributes,
            "is_weapon": is_weapon,
            "damage_formula": damage_formula,
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


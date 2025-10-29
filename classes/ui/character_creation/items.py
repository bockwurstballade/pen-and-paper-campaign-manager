"""
Everything realted to creating items inside the Character Creation Dialog
(besides main item functions) of course
"""
from PyQt6.QtWidgets import (
    QInputDialog, QMessageBox, QGroupBox, QVBoxLayout, QFormLayout,
    QLabel, QPushButton, QCheckBox, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt
import os
import json
import uuid
from classes.ui.attribute_dialog import AttributeDialog


class CharacterCreationDialogItems:
    def __init__(self, parent):
        self.parent = parent  # Referenz auf CharacterCreationDialog

    # -----------------------------------------------------
    # 🧩 Neues Item manuell erstellen
    # -----------------------------------------------------
    def add_item(self):
        parent = self.parent
        item_name, ok = QInputDialog.getText(parent, "Neues Item", "Item-Name:")
        if not ok or not item_name.strip():
            QMessageBox.warning(parent, "Fehler", "Item-Name darf nicht leer sein.")
            return

        item_name = item_name.strip()
        if item_name in parent.item_groups:
            QMessageBox.warning(parent, "Fehler", f"Item '{item_name}' existiert bereits.")
            return

        # Neue GroupBox
        item_group = QGroupBox(item_name)
        parent.style_groupbox(item_group)
        item_layout = QVBoxLayout()

        parent.item_groups[item_name] = {
            "attributes": {},
            "layout": item_layout,
            "group": item_group,
            "id": None,
            "linked_conditions": [],
            "is_weapon_checkbox": None,
            "damage_field": None,
        }

        # Attribute-Layout
        attr_layout = QFormLayout()
        parent.item_groups[item_name]["attr_layout"] = attr_layout
        item_layout.addLayout(attr_layout)

        # Waffenoption
        weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
        damage_input = QLineEdit()
        damage_input.setPlaceholderText("z. B. 1W6+2")
        damage_row = QHBoxLayout()
        damage_row.addWidget(QLabel("Schadensformel:"))
        damage_row.addWidget(damage_input)
        damage_input.setVisible(False)

        def on_weapon_toggle(state):
            damage_input.setVisible(state == Qt.CheckState.Checked.value)

        weapon_checkbox.stateChanged.connect(on_weapon_toggle)
        item_layout.addWidget(weapon_checkbox)
        item_layout.addLayout(damage_row)

        parent.item_groups[item_name]["is_weapon_checkbox"] = weapon_checkbox
        parent.item_groups[item_name]["damage_field"] = damage_input

        # Buttons
        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addWidget(add_attr_button)

        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item(item))
        item_layout.addWidget(remove_button)

        # In Layout einfügen
        item_group.setLayout(item_layout)
        insert_pos = max(0, parent.items_layout.count() - 2)
        parent.items_layout.insertWidget(insert_pos, item_group)

        # Optional global speichern
        if parent.save_new_items_globally_checkbox.isChecked():
            self._save_item_to_global_library(item_name)

    # -----------------------------------------------------
    # 🧩 Item in items.json speichern
    # -----------------------------------------------------
    def _save_item_to_global_library(self, item_name):
        parent = self.parent
        data = parent.item_groups[item_name]

        item_obj = {
            "id": str(uuid.uuid4()),
            "name": item_name,
            "description": "",
            "attributes": data.get("attributes", {}),
            "linked_conditions": [],
            "is_weapon": data["is_weapon_checkbox"].isChecked() if data["is_weapon_checkbox"] else False,
            "damage_formula": data["damage_field"].text().strip() if data["damage_field"] else ""
        }

        items_list = []
        if os.path.exists("items.json"):
            try:
                with open("items.json", "r", encoding="utf-8") as f:
                    content = json.load(f)
                    items_list = content.get("items", [])
            except Exception:
                pass

        for existing in items_list:
            if existing.get("name") == item_name:
                QMessageBox.information(parent, "Hinweis", f"Item '{item_name}' existiert bereits in items.json.")
                return

        items_list.append(item_obj)
        with open("items.json", "w", encoding="utf-8") as f:
            json.dump({"items": items_list}, f, indent=4, ensure_ascii=False)

        QMessageBox.information(parent, "Gespeichert", f"Item '{item_name}' wurde auch in items.json gespeichert.")

    # -----------------------------------------------------
    # 🧩 Neue Eigenschaft hinzufügen
    # -----------------------------------------------------
    def add_attribute(self, item_name):
        parent = self.parent
        dialog = AttributeDialog(parent)
        if dialog.exec() == 1:
            attr_name, attr_value = dialog.get_attribute()
            if not attr_name or not attr_value:
                QMessageBox.warning(parent, "Fehler", "Attribut-Name und -Wert dürfen nicht leer sein.")
                return
            if attr_name in parent.item_groups[item_name]["attributes"]:
                QMessageBox.warning(parent, "Fehler", f"Attribut '{attr_name}' existiert bereits für {item_name}.")
                return

            parent.item_groups[item_name]["attributes"][attr_name] = attr_value
            attr_layout = parent.item_groups[item_name]["layout"].itemAt(0).layout()
            attr_layout.addRow(f"{attr_name}:", QLabel(attr_value))

    # -----------------------------------------------------
    # 🧩 Item löschen (ohne Zustände)
    # -----------------------------------------------------
    def remove_item(self, item_name):
        parent = self.parent
        if item_name in parent.item_groups:
            item_group = parent.item_groups[item_name]["group"]
            parent.items_layout.removeWidget(item_group)
            item_group.deleteLater()
            del parent.item_groups[item_name]
            QMessageBox.information(parent, "Erfolg", f"Item '{item_name}' wurde entfernt.")

    # -----------------------------------------------------
    # 🧩 Item aus Bibliothek hinzufügen
    # -----------------------------------------------------
    def add_item_from_library(self):
        parent = self.parent

        if not os.path.exists("items.json"):
            QMessageBox.warning(parent, "Fehler", "Keine items.json gefunden.")
            return

        try:
            with open("items.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                items_list = data.get("items", [])
        except Exception as e:
            QMessageBox.warning(parent, "Fehler", f"Fehler beim Laden von items.json:\n{e}")
            return

        if not items_list:
            QMessageBox.information(parent, "Hinweis", "Es sind keine Items in items.json vorhanden.")
            return

        item_choices = [f"{it.get('name','(unbenannt)')} [{it.get('id','?')}]" for it in items_list]
        choice, ok = QInputDialog.getItem(parent, "Item auswählen", "Welches Item soll hinzugefügt werden?", item_choices, 0, False)
        if not ok:
            return

        idx = item_choices.index(choice)
        chosen_item = items_list[idx]
        item_name = chosen_item.get("name", "Unbenanntes Item")

        if item_name in parent.item_groups:
            QMessageBox.warning(parent, "Fehler", f"Item '{item_name}' existiert bereits.")
            return

        item_id = chosen_item.get("id", str(uuid.uuid4()))
        attributes = chosen_item.get("attributes", {})
        linked_conditions = chosen_item.get("linked_conditions", [])

        item_group = QGroupBox(item_name)
        parent.style_groupbox(item_group)
        item_layout = QVBoxLayout()

        # Attribute anzeigen
        attr_layout = QFormLayout()
        for attr_name, attr_value in attributes.items():
            attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))
        item_layout.addLayout(attr_layout)

        # Entfernen-Button
        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))
        item_layout.addWidget(remove_button)

        item_group.setLayout(item_layout)
        parent.items_layout.insertWidget(parent.items_layout.count() - 2, item_group)

        # Referenzen speichern
        parent.item_groups[item_name] = {
            "attributes": dict(attributes),
            "layout": item_layout,
            "group": item_group,
            "id": item_id,
            "linked_conditions": linked_conditions
        }

        parent.item_condition_links[item_name] = linked_conditions

        # Zustände aktivieren
        parent.attach_item_conditions(item_name, linked_conditions)

    # -----------------------------------------------------
    # 🧩 Item löschen + verknüpfte Zustände abtrennen
    # -----------------------------------------------------
    def remove_item_and_detach_conditions(self, item_name):
        parent = self.parent
        if item_name not in parent.item_groups:
            return

        linked_conds = parent.item_groups[item_name].get("linked_conditions", [])
        for cid in linked_conds:
            if cid in parent.condition_refcount:
                parent.condition_refcount[cid] -= 1
                if parent.condition_refcount[cid] <= 0:
                    parent.condition_refcount.pop(cid, None)
                    parent.remove_condition_widget_by_id(cid)

        item_group = parent.item_groups[item_name]["group"]
        parent.items_layout.removeWidget(item_group)
        item_group.deleteLater()
        del parent.item_groups[item_name]

        if item_name in parent.item_condition_links:
            del parent.item_condition_links[item_name]

        parent.recalculate_conditions_effects()
        QMessageBox.information(parent, "Erfolg", f"Item '{item_name}' wurde entfernt.")

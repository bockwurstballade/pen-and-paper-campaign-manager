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

from classes.ui.condition_linker_widget import ConditionLinkerWidget
from classes.core.data_manager import DataManager

# Waffenkategorien (analog zu character_creation/items.py)
WEAPON_CATEGORIES = [
    "Nahkampfwaffe",
    "Schusswaffe",
    "Explosivwaffe",
    "Natural",
    "Magie",
    "Sonstiges",
]


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

        # Waffenkategorie (nur sichtbar, wenn Waffe)
        self.weapon_category_combo = QComboBox()
        self.weapon_category_combo.addItems(WEAPON_CATEGORIES)
        self.weapon_category_combo.setVisible(False)
        form_layout.addRow("Waffenkategorie:", self.weapon_category_combo)

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

        # Zustands-Verknüpfung via ConditionLinkerWidget
        self.condition_linker = ConditionLinkerWidget(self)
        main_layout.addWidget(self.condition_linker)

        # Speichern-Button
        save_button = QPushButton("Item speichern")
        save_button.clicked.connect(self.save_item)
        main_layout.addWidget(save_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def toggle_weapon_fields(self):
        """Zeigt oder versteckt Schadensformel und Waffenkategorie."""
        visible = self.is_weapon_checkbox.isChecked()
        self.damage_formula_input.setVisible(visible)
        self.weapon_category_combo.setVisible(visible)


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

    ## LADEN UND SPEICHERN VON ITEMDATEN

    def load_item_data(self, item_data, file_path=None):
        """
        Lädt bestehendes Item in den Dialog, damit es bearbeitet werden kann.
        item_data ist ein einzelnes Item-Dict (mit 'id', 'name', ...)
        """
        self.loaded_file = file_path
        self.item_id = item_data.get("id", str(uuid.uuid4()))

        self.name_input.setText(item_data.get("name", ""))
        self.description_input.setText(item_data.get("description", ""))

        # Waffen-Checkbox, Schadensformel und Waffenkategorie laden
        is_weapon = item_data.get("is_weapon", False)
        self.is_weapon_checkbox.setChecked(is_weapon)
        self.damage_formula_input.setText(item_data.get("damage_formula", ""))
        weapon_cat = item_data.get("weapon_category") or "Sonstiges"
        if weapon_cat in WEAPON_CATEGORIES:
            self.weapon_category_combo.setCurrentText(weapon_cat)
        else:
            self.weapon_category_combo.setCurrentText("Sonstiges")
        self.damage_formula_input.setVisible(is_weapon)
        self.weapon_category_combo.setVisible(is_weapon)

        # Zustände / Links über ConditionLinkerWidget laden
        self.condition_linker.set_linked_conditions(item_data.get("linked_conditions", []))

        # Attribute rendern
        attrs = item_data.get("attributes", {})
        for attr_name, attr_value in attrs.items():
            self.add_attribute_row(preset_name=attr_name, preset_value=attr_value)
        self.toggle_weapon_fields()


    def save_item(self):
        """
        Speichert/aktualisiert das Item.
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
        damage_formula = self.damage_formula_input.text().strip() if is_weapon else ""
        weapon_category = self.weapon_category_combo.currentText() if is_weapon else None

        item_obj = {
            "id": self.item_id,
            "name": name,
            "description": description,
            "attributes": attributes,
            "is_weapon": is_weapon,
            "damage_formula": damage_formula,
            "weapon_category": weapon_category,
            "linked_conditions": self.condition_linker.get_linked_conditions()
        }

        try:
            DataManager.save_item(item_obj)
            QMessageBox.information(self, "Erfolg", f"Item '{name}' wurde gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Speichern des Items:\n{e}")

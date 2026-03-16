"""
Everything realted to creating items inside the Character Creation Dialog
(besides main item functions) of course
"""
from PyQt6.QtWidgets import (
    QInputDialog, QMessageBox, QGroupBox, QVBoxLayout, QFormLayout,
    QLabel, QPushButton, QCheckBox, QLineEdit, QHBoxLayout, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt
import os
import json
import uuid
from classes.ui.attribute_dialog import AttributeDialog
from classes.core.data_manager import DataManager
from classes.ui.ui_utils import style_groupbox
from classes.ui.weapon_state_widget import WeaponStateWidget


class CharacterCreationDialogItems:

    WEAPON_CATEGORIES = [
        "Nahkampfwaffe",
        "Schusswaffe",
        "Explosivwaffe",
        "Natural",
        "Magie",
        "Sonstiges"
    ]

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

        # --- Grundlayout ---
        group = QGroupBox(item_name)
        style_groupbox(group)
        vbox = QVBoxLayout()
        attr_layout = QFormLayout()
        vbox.addLayout(attr_layout)

        parent.item_groups[item_name] = {
            "attributes": {},
            "layout": vbox,
            "group": group,
            "linked_conditions": [],
            "id": None,
        }

        # --- Waffenoption ---
        weapon_cb = QCheckBox("Dieses Item ist eine Waffe")
        dmg_field = QLineEdit()
        dmg_field.setPlaceholderText("z. B. 1W6 + 2")
        dmg_row = QHBoxLayout()
        dmg_row.addWidget(QLabel("Schadensformel:"))
        dmg_row.addWidget(dmg_field)
        dmg_field.setVisible(False)

        # Kategorie
        cat_label = QLabel("Waffenkategorie:")
        cat_combo = QComboBox(); cat_combo.addItems(self.WEAPON_CATEGORIES)
        cat_label.setVisible(False); cat_combo.setVisible(False)

        cat_row = QHBoxLayout()
        cat_row.addWidget(cat_label)
        cat_row.addWidget(cat_combo)

        # --- Waffen-Status (modulares Widget: nur Schusswaffe = Kammern/Magazin, Natural/Explosiv = Projektile) ---
        weapon_state_widget = WeaponStateWidget(parent, title="Waffen-Status")
        weapon_state_widget.setVisible(False)

        def on_weapon_toggle(state):
            checked = state == Qt.CheckState.Checked.value
            dmg_field.setVisible(checked)
            cat_label.setVisible(checked)
            cat_combo.setVisible(checked)
            weapon_state_widget.setVisible(checked)
            if checked:
                weapon_state_widget.update_visibility(cat_combo.currentText())

        def on_category_changed(cat):
            weapon_state_widget.update_visibility(cat)

        weapon_cb.stateChanged.connect(on_weapon_toggle)
        cat_combo.currentTextChanged.connect(on_category_changed)

        # --- Buttons ---
        add_attr_btn = QPushButton("+ Neue Eigenschaft")
        add_attr_btn.clicked.connect(lambda _, n=item_name: self.add_attribute(n))
        remove_btn = QPushButton("– Item entfernen")
        remove_btn.clicked.connect(lambda _, n=item_name: self.remove_item(n))

        # --- Aufbau ---
        vbox.addWidget(weapon_cb)
        vbox.addLayout(dmg_row)
        vbox.addLayout(cat_row)
        vbox.addWidget(weapon_state_widget)
        vbox.addWidget(add_attr_btn)
        vbox.addWidget(remove_btn)

        group.setLayout(vbox)
        insert_pos = max(0, parent.items_layout.count() - 2)
        parent.items_layout.insertWidget(insert_pos, group)

        # --- Referenzen speichern ---
        parent.item_groups[item_name].update({
            "is_weapon_checkbox": weapon_cb,
            "damage_field": dmg_field,
            "weapon_category_combo": cat_combo,
            "weapon_state_widget": weapon_state_widget,
        })

        # optional global speichern
        if parent.save_new_items_globally_checkbox.isChecked():
            self._save_item_to_global_library(item_name)

    # -----------------------------------------------------
    # 🧩 Item in items.json speichern
    # -----------------------------------------------------
    def _save_item_to_global_library(self, item_name):
        parent = self.parent
        data = parent.item_groups[item_name]

        # 🔧 Waffendaten erfassen
        is_weapon = False
        damage_formula = ""
        weapon_category = None

        weapon_checkbox = data.get("is_weapon_checkbox")
        damage_field = data.get("damage_field")
        weapon_category_combo = data.get("weapon_category_combo")

        if weapon_checkbox and weapon_checkbox.isChecked():
            is_weapon = True
            if damage_field:
                damage_formula = damage_field.text().strip()
            if weapon_category_combo:
                weapon_category = weapon_category_combo.currentText()

        weapon_state = {}
        ws_widget = data.get("weapon_state_widget")
        if ws_widget:
            weapon_state = ws_widget.get_state()

        # 📦 Neues Item-Objekt vorbereiten
        item_obj = {
            "id": str(uuid.uuid4()),
            "name": item_name,
            "description": "",
            "attributes": data.get("attributes", {}),
            "linked_conditions": [],
            "is_weapon": is_weapon,
            "damage_formula": damage_formula,
            "weapon_category": weapon_category,
            "weapon_state": weapon_state,
        }

        # 🗃️ Vorhandene Items laden
        items_list = DataManager.get_all_items()

        # Doppelte vermeiden
        for existing in items_list:
            if existing.get("name") == item_name:
                QMessageBox.information(parent, "Hinweis", f"Item '{item_name}' existiert bereits in der Bibliothek.")
                return

        try:
            DataManager.save_item(item_obj)
            QMessageBox.information(parent, "Gespeichert", f"Item '{item_name}' wurde in die Bibliothek gespeichert.")
        except Exception as e:
            QMessageBox.warning(parent, "Fehler", f"Konnte Item nicht speichern:\n{e}")

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


    def upsert_items_to_global_library(self):
        """
        Schreibt alle aktuell im Dialog befindlichen Items in die items.json zurück:
        - aktualisiert bestehende Einträge (per id, Fallback per Name),
        - ergänzt neue,
        - übernimmt is_weapon, damage_formula, weapon_category und attributes.
        Nur, wenn die Checkbox 'save_new_items_globally_checkbox' aktiv ist.
        """
        parent = self.parent
        # Falls Checkbox fehlt oder deaktiviert ist: nichts tun
        if not getattr(parent, "save_new_items_globally_checkbox", None):
            return
        if not parent.save_new_items_globally_checkbox.isChecked():
            return

        items_list = DataManager.get_all_items()

        # Indizes für Update
        by_id = {it.get("id"): it for it in items_list if it.get("id")}
        by_name = {it.get("name"): it for it in items_list if it.get("name")}

        changed = False

        for item_name, data in parent.item_groups.items():
            # UI-Felder auslesen, wenn vorhanden
            cb = data.get("is_weapon_checkbox")
            dmg_field = data.get("damage_field")
            cat_combo = data.get("weapon_category_combo")

            is_weapon = bool(cb.isChecked()) if cb is not None else bool(data.get("is_weapon", False))
            damage_formula = (dmg_field.text().strip() if dmg_field is not None else data.get("damage_formula", "")) if is_weapon else ""
            weapon_category = (cat_combo.currentText() if cat_combo is not None else data.get("weapon_category")) if is_weapon else None

            weapon_state = {}
            ws_widget = data.get("weapon_state_widget")
            if ws_widget:
                weapon_state = ws_widget.get_state()

            record = {
                "id": data.get("id") or str(uuid.uuid4()),
                "name": item_name,
                "description": "",
                "attributes": data.get("attributes", {}),
                "linked_conditions": data.get("linked_conditions", []),
                "is_weapon": is_weapon,
                "damage_formula": damage_formula,
                "weapon_category": weapon_category,
                "weapon_state": weapon_state,
            }

            target = None
            if record["id"] in by_id:
                target = by_id[record["id"]]
            elif item_name in by_name:
                target = by_name[item_name]

            if target:
                target.update(record)
                DataManager.save_item(target)
            else:
                DataManager.save_item(record)

    # -----------------------------------------------------
    # 🧩 Item aus Bibliothek hinzufügen
    # -----------------------------------------------------
    def add_item_from_library(self):
        parent = self.parent

        try:
            items_list = DataManager.get_all_items()
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

        # Gleiche Struktur wie beim Laden/Bearbeiten: vollständige Item-UI inkl. Waffen
        item_info = {
            "attributes": chosen_item.get("attributes", {}),
            "id": chosen_item.get("id", str(uuid.uuid4())),
            "linked_conditions": chosen_item.get("linked_conditions", []),
            "is_weapon": chosen_item.get("is_weapon", False),
            "damage_formula": chosen_item.get("damage_formula", ""),
            "weapon_category": chosen_item.get("weapon_category"),
            "weapon_state": chosen_item.get("weapon_state", {}),
        }
        self._add_single_item_ui(item_name, item_info)

        # Zustände aktivieren
        parent.attach_item_conditions(item_name, item_info["linked_conditions"])

    # -----------------------------------------------------
    # 🧩 Item löschen + verknüpfte Zustände abtrennen
    # -----------------------------------------------------
    def remove_item_and_detach_conditions(self, item_name):
        parent = self.parent
        main_dialog = getattr(parent, "main_dialog", None) or parent # Fallback falls wir schon im MainDialog sind

        if item_name not in parent.item_groups:
            return

        linked_conds = parent.item_groups[item_name].get("linked_conditions", [])
        if hasattr(main_dialog, "condition_refcount"):
            for cid in linked_conds:
                if cid in main_dialog.condition_refcount:
                    main_dialog.condition_refcount[cid] -= 1
                    if main_dialog.condition_refcount[cid] <= 0:
                        main_dialog.condition_refcount.pop(cid, None)
                        main_dialog.remove_condition_widget_by_id(cid)

        item_group = parent.item_groups[item_name]["group"]
        parent.items_layout.removeWidget(item_group)
        item_group.deleteLater()
        del parent.item_groups[item_name]

        if item_name in parent.item_condition_links:
            del parent.item_condition_links[item_name]

        if hasattr(main_dialog, "recalculate_conditions_effects"):
            main_dialog.recalculate_conditions_effects()
        
        QMessageBox.information(parent, "Erfolg", f"Item '{item_name}' wurde entfernt.")

    def _add_single_item_ui(self, item_name, item_info):
        """
        Baut die vollständige Item-UI (inkl. Waffen-Checkbox, Schadensformel, Waffenkategorie,
        Waffen-Status) für ein einzelnes Item. Wird von restore_items_from_data und
        add_item_from_library verwendet.
        item_info: dict mit attributes, id, linked_conditions, is_weapon, damage_formula,
                   weapon_category, weapon_state (optional).
        """
        from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QFormLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QHBoxLayout, QPushButton
        from PyQt6.QtCore import Qt
        import uuid
        parent = self.parent

        attrs = item_info.get("attributes", {})
        item_uuid = item_info.get("id", str(uuid.uuid4()))
        linked_conditions = item_info.get("linked_conditions", [])

        item_group = QGroupBox(item_name)
        style_groupbox(item_group)
        item_layout = QVBoxLayout()

        attr_layout = QFormLayout()
        for attr_name, attr_value in attrs.items():
            attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))

        # --- Waffenbereich ---
        is_weapon = item_info.get("is_weapon", False)
        damage_formula = item_info.get("damage_formula", "")
        weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
        weapon_checkbox.setChecked(is_weapon)

        damage_input = QLineEdit()
        weapon_category_label = QLabel("Waffenkategorie:")
        weapon_category_combo = QComboBox()
        weapon_category_combo.addItems(self.WEAPON_CATEGORIES)

        parent.items_layout.insertWidget(parent.items_layout.count() - 2, item_group)
        weapon_category_combo.setCurrentText(item_info.get("weapon_category") or "Sonstiges")

        # --- Erstes self.item_groups-Dict anlegen ---
        parent.item_groups[item_name] = {
            "attributes": dict(attrs),
            "layout": item_layout,
            "group": item_group,
            "id": item_uuid,
            "weapon_category_combo": weapon_category_combo,
            "linked_conditions": linked_conditions
        }

        weapon_state = item_info.get("weapon_state", {})

        # Waffen-Status über modulares Widget (nur Schusswaffe: Kammern/Magazin, Natural/Explosiv: Projektile)
        weapon_state_widget = WeaponStateWidget(parent, title="Waffen-Status")
        weapon_state_widget.set_state(weapon_state)
        weapon_state_widget.update_visibility(item_info.get("weapon_category", ""))

        item_layout.addWidget(weapon_state_widget)

        # Referenzen speichern
        parent.item_groups[item_name].update({
            "weapon_state_widget": weapon_state_widget,
            "is_weapon_checkbox": weapon_checkbox,
            "damage_field": damage_input,
        })

        weapon_category_label.setVisible(is_weapon)
        weapon_category_combo.setVisible(is_weapon)
        damage_input.setPlaceholderText("z. B. 2W10+5")
        damage_input.setText(damage_formula)
        damage_row = QHBoxLayout()
        damage_row.addWidget(QLabel("Schadensformel:"))
        damage_row.addWidget(damage_input)
        weapon_cat_row = QHBoxLayout()
        weapon_cat_row.addWidget(weapon_category_label)
        weapon_cat_row.addWidget(weapon_category_combo)
        item_layout.addWidget(weapon_checkbox)
        item_layout.addLayout(damage_row)
        item_layout.addLayout(weapon_cat_row)
        damage_input.setVisible(is_weapon)

        def on_weapon_toggle(state, dmg_input=damage_input, cat_label=weapon_category_label, cat_combo=weapon_category_combo, ws_widget=weapon_state_widget):
            is_checked = state == Qt.CheckState.Checked.value
            dmg_input.setVisible(is_checked)
            cat_label.setVisible(is_checked)
            cat_combo.setVisible(is_checked)
            ws_widget.setVisible(is_checked)
            if is_checked:
                ws_widget.update_visibility(cat_combo.currentText())

        weapon_state_widget.setVisible(is_weapon)
        on_weapon_toggle(Qt.CheckState.Checked.value if is_weapon else Qt.CheckState.Unchecked.value)
        weapon_checkbox.stateChanged.connect(on_weapon_toggle)

        def on_category_changed(cat):
            weapon_state_widget.update_visibility(cat)
        weapon_category_combo.currentTextChanged.connect(on_category_changed)

        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))

        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))

        item_layout.addLayout(attr_layout)
        item_layout.addWidget(add_attr_button)
        item_layout.addWidget(remove_button)
        item_group.setLayout(item_layout)

        # Link info
        if linked_conditions:
            parent.item_condition_links[item_name] = linked_conditions

    def restore_items_from_data(self, items_saved_data):
        """Builds the UI block for items from a loaded JSON dict. Formally in CharacterCreationDialog."""
        for item_name, item_info in items_saved_data.items():
            self._add_single_item_ui(item_name, item_info)


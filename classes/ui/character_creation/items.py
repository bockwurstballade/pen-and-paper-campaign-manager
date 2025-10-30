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
        parent.style_groupbox(group)
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

        # --- Waffen-Status ---
        state_layout = QFormLayout()

        # Schusswaffen
        chambers_cap = QSpinBox(); chambers_cap.setRange(0, 10)
        chambers_loaded = QSpinBox(); chambers_loaded.setRange(0, 10)
        mag_inserted = QCheckBox("Magazin eingelegt")
        mag_cap = QSpinBox(); mag_cap.setRange(0, 200)
        mag_count = QSpinBox(); mag_count.setRange(0, 200)

        # Bögen / Schleudern
        proj_loaded = QSpinBox(); proj_loaded.setRange(0, 5)
        proj_type = QLineEdit(); proj_type.setPlaceholderText("z. B. Pfeil, Kugel …")

        for w in (chambers_cap, chambers_loaded, mag_inserted,
                  mag_cap, mag_count, proj_loaded, proj_type):
            w.setVisible(False)

        state_layout.addRow("Kammern (max):", chambers_cap)
        state_layout.addRow("Kammern geladen:", chambers_loaded)
        state_layout.addRow(mag_inserted)
        state_layout.addRow("Magazin Kapazität:", mag_cap)
        state_layout.addRow("Magazin aktuell:", mag_count)
        state_layout.addRow("Proj. geladen:", proj_loaded)
        state_layout.addRow("Proj. Typ:", proj_type)

        # --- Sichtbarkeits-Logik ---
        def on_weapon_toggle(state):
            checked = state == Qt.CheckState.Checked.value
            dmg_field.setVisible(checked)
            cat_label.setVisible(checked)
            cat_combo.setVisible(checked)
            for w in (chambers_cap, chambers_loaded, mag_inserted,
                      mag_cap, mag_count, proj_loaded, proj_type):
                w.setVisible(False)

        def on_category_changed(cat):
            # alles ausblenden, dann gezielt zeigen
            for w in (chambers_cap, chambers_loaded, mag_inserted,
                      mag_cap, mag_count, proj_loaded, proj_type):
                w.setVisible(False)
            if cat == "Schusswaffe":
                for w in (chambers_cap, chambers_loaded, mag_inserted, mag_cap, mag_count):
                    w.setVisible(True)
            elif cat in ("Natural", "Explosivwaffe"):
                for w in (proj_loaded, proj_type):
                    w.setVisible(True)

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
        vbox.addLayout(state_layout)
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
            "chambers_capacity_spin": chambers_cap,
            "chambers_loaded_spin": chambers_loaded,
            "magazine_inserted_cb": mag_inserted,
            "magazine_capacity_spin": mag_cap,
            "magazine_count_spin": mag_count,
            "projectiles_loaded_spin": proj_loaded,
            "projectile_type_input": proj_type,
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
        }

        # 🗃️ Vorhandene Items laden
        items_list = []
        if os.path.exists("items.json"):
            try:
                with open("items.json", "r", encoding="utf-8") as f:
                    content = json.load(f)
                    items_list = content.get("items", [])
            except Exception:
                pass

        # Doppelte vermeiden
        for existing in items_list:
            if existing.get("name") == item_name:
                QMessageBox.information(parent, "Hinweis", f"Item '{item_name}' existiert bereits in items.json.")
                return

        # Neues Item hinzufügen und speichern
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

        path = "items.json"
        items_list = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    items_list = content.get("items", [])
            except Exception:
                items_list = []

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

            record = {
                "id": data.get("id") or str(uuid.uuid4()),
                "name": item_name,
                "description": "",
                "attributes": data.get("attributes", {}),
                "linked_conditions": data.get("linked_conditions", []),
                "is_weapon": is_weapon,
                "damage_formula": damage_formula,
                "weapon_category": weapon_category,
            }

            target = None
            if record["id"] in by_id:
                target = by_id[record["id"]]
            elif item_name in by_name:
                target = by_name[item_name]

            if target:
                target.update(record)
                changed = True
            else:
                items_list.append(record)
                changed = True

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"items": items_list}, f, indent=4, ensure_ascii=False)

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

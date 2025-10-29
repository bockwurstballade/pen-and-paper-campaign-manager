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

## eigene Funktionen
from utils.functions.math import kaufmaennisch_runden
## eigene Klassen

from classes.ui.condition_editor_dialog import ConditionEditorDialog
from classes.ui.character_creation.armor import CharacterCreationDialogArmor
from classes.ui.character_creation.skills import CharacterCreationDialogSkills
from classes.ui.character_creation.items import CharacterCreationDialogItems
from classes.ui.character_creation.conditions import CharacterCreationDialogConditions




class CharacterCreationDialog(QDialog):

    def __init__(self, parent=None):
        self.loaded_file = None
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
        self.class_input = QLineEdit()
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Männlich", "Weiblich", "Divers"])
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Zahl eingeben")
        self.hitpoints_input = QLineEdit()
        self.hitpoints_input.setPlaceholderText("Zahl eingeben")
        self.hitpoints_input.textChanged.connect(self.update_base_hitpoints)
        self.build_input = QLineEdit()
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
        # Beschreibung (mehrzeilig)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Hier kannst du eine Hintergrundgeschichte oder Notizen eintragen...")
        self.description_input.setFixedHeight(120)  # optional: begrenzt sichtbare Höhe
        self.base_form.addRow("Beschreibung:", self.description_input)

        main_layout.addLayout(self.base_form)

        # ---------- Rüstungsmodul ----------
        self.armor_group = QGroupBox("Rüstung")
        self.style_groupbox(self.armor_group)
        armor_layout = QFormLayout()

        # Checkbox zum Aktivieren
        self.armor_enabled_checkbox = QCheckBox("Rüstungsmodul aktivieren")
        self.armor_handler = CharacterCreationDialogArmor(self)
        self.armor_enabled_checkbox.stateChanged.connect(self.armor_handler.toggle_armor_fields)
        armor_layout.addRow(self.armor_enabled_checkbox)

        # Eingabefelder für Rüstungswert & Zustand
        self.armor_value_input = QLineEdit()
        self.armor_value_input.setPlaceholderText("0–9")
        self.armor_condition_input = QLineEdit()
        self.armor_condition_input.setPlaceholderText("0–9")

        # Beide Felder erst einmal ausblenden
        self.armor_value_input.setVisible(False)
        self.armor_condition_input.setVisible(False)

        armor_layout.addRow("Rüstungswert:", self.armor_value_input)
        armor_layout.addRow("Rüstungszustand:", self.armor_condition_input)

        self.armor_group.setLayout(armor_layout)
        main_layout.addWidget(self.armor_group)
        # ---------- /Rüstungsmodul ----------

        # Fähigkeiten
        self.skills_handler = CharacterCreationDialogSkills(self)
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
            self.add_buttons[category].clicked.connect(lambda _, cat=category: self.skills_handler.add_skill(cat))
            vbox.addWidget(self.add_buttons[category])

            self.group_boxes[category].setLayout(vbox)

            main_layout.addWidget(self.group_boxes[category])

            self.category_labels[category] = QLabel(f"{category}-Wert: 0")
            self.inspiration_labels[category] = QLabel(f"Geistesblitzpunkte ({category}): 0")
            main_layout.addWidget(self.category_labels[category])
            main_layout.addWidget(self.inspiration_labels[category])


        main_layout.addWidget(self.total_points_label)

        # Items
        self.items_handler = CharacterCreationDialogItems(self)
        self.items_group = QGroupBox("Items")
        self.style_groupbox(self.items_group)
        self.items_layout = QVBoxLayout()
        self.item_groups = {}
        self.item_add_button = QPushButton("+ Neues Item")
        self.item_add_button.clicked.connect(self.items_handler.add_item)
        self.items_layout.addWidget(self.item_add_button)
        self.item_add_from_lib_button = QPushButton("+ Item aus Sammlung hinzufügen")
        self.item_add_from_lib_button.clicked.connect(self.items_handler.add_item_from_library)
        self.items_layout.addWidget(self.item_add_from_lib_button)
        self.items_group.setLayout(self.items_layout)
        main_layout.addWidget(self.items_group)
        # Checkbox: globales Speichern aktivieren
        self.save_new_items_globally_checkbox = QCheckBox("Neue Items auch in der globalen Sammlung (items.json) speichern")
        self.save_new_items_globally_checkbox.setChecked(True)
        self.items_layout.addWidget(self.save_new_items_globally_checkbox)

        # Zustände
        self.conditions_handler = CharacterCreationDialogConditions(self)
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
        self.condition_add_button.clicked.connect(self.conditions_handler.add_condition)
        self.conditions_layout.addWidget(self.condition_add_button)
        self.conditions_group.setLayout(self.conditions_layout)
        self.condition_add_from_lib_button = QPushButton("+ Zustand aus Sammlung hinzufügen")
        self.condition_add_from_lib_button.clicked.connect(self.conditions_handler.add_condition_from_library)
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
        condition_name = cond_info["name"]
        # aus Tracking entfernen
        self.active_condition_by_id.pop(cid, None)
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

        # nach allen Modifikationen Endwert-Labels updaten
        self.skills_handler.update_endwert_labels()

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
            description = self.description_input.toPlainText().strip()
            occupation = self.occupation_input.text().strip()
            base_damage = self.base_damage_input.text().strip()

            # Rüstungsdaten
            armor_enabled = self.armor_enabled_checkbox.isChecked()
            armor_value = None
            armor_condition = None

            if armor_enabled:
                try:
                    armor_value = int(self.armor_value_input.text())
                    armor_condition = int(self.armor_condition_input.text())
                    if not (0 <= armor_value <= 9) or not (0 <= armor_condition <= 9):
                        raise ValueError("Rüstungswert und Rüstungszustand müssen zwischen 0 und 9 liegen.")
                except ValueError:
                    QMessageBox.warning(self, "Fehler", "Bitte gültige Rüstungswerte (0–9) eingeben.")
                    return


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
                weapon_category = None

                weapon_cb = data.get("is_weapon_checkbox")
                dmg_field = data.get("damage_field")
                weapon_cat_combo = data.get("weapon_category_combo")

                if weapon_cb is not None and dmg_field is not None:
                    is_weapon = weapon_cb.isChecked()
                    damage_formula = dmg_field.text().strip() if is_weapon else ""
                    weapon_category = (
                        weapon_cat_combo.currentText() if (is_weapon and weapon_cat_combo is not None) else None
                    )
                else:
                    # Bibliotheksitems
                    is_weapon = bool(data.get("is_weapon", False))
                    damage_formula = data.get("damage_formula", "")
                    weapon_category = data.get("weapon_category", None)

                items_data[item_name] = {
                    "attributes": data.get("attributes", {}),
                    "id": data.get("id", None),
                    "linked_conditions": data.get("linked_conditions", []),
                    "is_weapon": is_weapon,
                    "damage_formula": damage_formula,
                    "weapon_category": weapon_category,
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
            "class": self.class_input.text(),
            "gender": self.gender_input.currentText(),
            "age": age,
            "hitpoints": hitpoints,
            "base_damage": base_damage,
            "build": self.build_input.text(),
            "religion": religion,
            "occupation": occupation,
            "marital_status": self.marital_status_input.currentText(),
            "skills": skills_data,
            "category_scores": category_scores,
            "inspiration_points": inspiration_points,
            "items": items_data,
            "conditions": conditions_data,
            "description": description,
            "role": "pc" if self.role_input.currentText().startswith("Spieler") else "npc",
            "armor_enabled": armor_enabled,
            "armor_value": armor_value,
            "armor_condition": armor_condition
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
        if hasattr(self, "items_handler"):
            self.items_handler.upsert_items_to_global_library()

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(character, f, indent=4, ensure_ascii=False)
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

        # Rüstungsmodul wiederherstellen
        armor_enabled = character.get("armor_enabled", False)
        armor_value = character.get("armor_value")
        armor_condition = character.get("armor_condition")

        # Blockiere Signale, um kein ungewolltes Toggle auszulösen
        self.armor_enabled_checkbox.blockSignals(True)
        self.armor_enabled_checkbox.setChecked(armor_enabled)
        self.armor_enabled_checkbox.blockSignals(False)

        # Eingabefelder wiederherstellen
        if armor_value is not None:
            self.armor_value_input.setText(str(armor_value))
        if armor_condition is not None:
            self.armor_condition_input.setText(str(armor_condition))

        # Jetzt manuell Sichtbarkeit / Aktivierung aktualisieren
        self.armor_handler.toggle_armor_fields(
            Qt.CheckState.Checked.value if armor_enabled else Qt.CheckState.Unchecked.value
        )


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
                input_field.textChanged.connect(self.skills_handler.update_points)

                end_label = QLabel("Endwert: 0")
                self.skill_end_labels[category][skill] = end_label

                remove_button = QPushButton("– Entfernen")
                remove_button.clicked.connect(lambda _, cat=category, skill=skill: self.skills_handler.remove_skill(cat, skill))

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

            # --- Waffenbereich ---
            is_weapon = item_info.get("is_weapon", False)
            damage_formula = item_info.get("damage_formula", "")
            weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
            weapon_checkbox.setChecked(is_weapon)

            damage_input = QLineEdit()
            weapon_category_label = QLabel("Waffenkategorie:")
            weapon_category_combo = QComboBox()
            weapon_category_combo.addItems(
                self.items_handler.WEAPON_CATEGORIES
                if hasattr(self, "items_handler")
                else ["Nahkampfwaffe", "Schusswaffe", "Explosivwaffe", "Natural", "Magie", "Sonstiges"]
            )
            self.items_layout.insertWidget(self.items_layout.count() - 2, item_group)

            weapon_category_combo.setCurrentText(item_info.get("weapon_category", "Sonstiges"))

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
            # Schadensformel nur anzeigen, wenn Checkbox aktiv ist
            damage_input.setVisible(is_weapon)

            def on_weapon_toggle(state, dmg_input=damage_input, cat_label=weapon_category_label, cat_combo=weapon_category_combo):
                is_checked = state == Qt.CheckState.Checked.value
                dmg_input.setVisible(is_checked)
                cat_label.setVisible(is_checked)
                cat_combo.setVisible(is_checked)

            # Sichtbarkeit der Waffenfelder nach dem Setzen aktualisieren
            on_weapon_toggle(Qt.CheckState.Checked.value if is_weapon else Qt.CheckState.Unchecked.value)

            weapon_checkbox.stateChanged.connect(on_weapon_toggle)


            add_attr_button = QPushButton("+ Neue Eigenschaft")
            add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))

            remove_button = QPushButton("- Item entfernen")
            remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))

            item_layout.addLayout(attr_layout)
            item_layout.addWidget(add_attr_button)
            item_layout.addWidget(remove_button)
            item_group.setLayout(item_layout)

            self.item_groups[item_name] = {
                "attributes": dict(attrs),
                "layout": item_layout,
                "group": item_group,
                "id": item_uuid,
                "weapon_category_combo": weapon_category_combo,
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
        self.skills_handler.update_points()
        # Charakter Rolle
        role = character.get("role", "pc")
        if role == "npc":
            self.role_input.setCurrentText("NSC / Gegner")
        else:
            self.role_input.setCurrentText("Spielercharakter")


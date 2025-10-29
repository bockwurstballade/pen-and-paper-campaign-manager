"""
Alles was im Charakter-Erstellungsdialog
mit Zuständen zu tun hat
"""
from PyQt6.QtWidgets import (
    QMessageBox, QGroupBox, QVBoxLayout, QLabel, QPushButton, QInputDialog
)
from PyQt6.QtCore import Qt
import os
import json
import uuid
from classes.ui.condition_editor_dialog import ConditionEditorDialog


class CharacterCreationDialogConditions:
    def __init__(self, parent):
        self.parent = parent  # CharacterCreationDialog

    # -----------------------------------------------------
    # 🧠 Hilfsmethode: prüft, ob ein Zustand auf diesen Charakter passt
    # -----------------------------------------------------
    def _is_condition_target_valid_for_this_character(self, effect_target: str) -> bool:
        parent = self.parent
        if not effect_target or effect_target == "(kein Ziel / n/a)":
            return True
        if effect_target == "Lebenspunkte":
            return True
        if effect_target.startswith("Fertigkeit: "):
            skill_name = effect_target.replace("Fertigkeit: ", "", 1).strip()
            for cat, skill_list in parent.skills.items():
                if skill_name in skill_list:
                    return True
            return False
        if effect_target.startswith("Kategoriewert: "):
            cat_name = effect_target.replace("Kategoriewert: ", "", 1).strip()
            return cat_name in parent.skills
        if effect_target.startswith("Geistesblitzpunkte: "):
            cat_name = effect_target.replace("Geistesblitzpunkte: ", "", 1).strip()
            return cat_name in parent.skills
        return True

    # -----------------------------------------------------
    # 🧩 Zustand hinzufügen (manuell)
    # -----------------------------------------------------
    def add_condition(self):
        parent = self.parent

        # verfügbare Ziele basierend auf Charakterdaten
        skill_targets, cat_targets, insp_targets = self._build_condition_target_lists()

        dlg = ConditionEditorDialog(
            parent=parent,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.condition_id = str(uuid.uuid4())
        result = dlg.exec()
        if result != dlg.DialogCode.Accepted:
            return

        # Zustand speichern oder rekonstruieren
        cond_list = []
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    cond_list = json.load(f).get("conditions", [])
            except Exception:
                pass

        saved_cond = next((c for c in cond_list if c.get("id") == dlg.condition_id), None)
        if not saved_cond:
            saved_cond = {
                "id": dlg.condition_id,
                "name": dlg.name_input.text().strip(),
                "description": dlg.description_input.text().strip(),
                "effect_type": dlg.effect_type_input.currentText(),
                "effect_target": dlg.ask_for_custom_target_if_needed(),
                "effect_value": int(dlg.effect_value_input.text() or "0"),
            }

        self._activate_condition(saved_cond, source_item=None)

    # -----------------------------------------------------
    # 🧩 Zustand aus conditions.json hinzufügen
    # -----------------------------------------------------
    def add_condition_from_library(self):
        parent = self.parent
        if not os.path.exists("conditions.json"):
            QMessageBox.warning(parent, "Fehler", "Keine conditions.json gefunden.")
            return

        try:
            with open("conditions.json", "r", encoding="utf-8") as f:
                cond_list = json.load(f).get("conditions", [])
        except Exception as e:
            QMessageBox.warning(parent, "Fehler", f"Fehler beim Laden von conditions.json:\n{e}")
            return

        if not cond_list:
            QMessageBox.information(parent, "Hinweis", "Es sind keine Zustände vorhanden.")
            return

        choices = [f"{c.get('name','(unbenannt)')} [{c.get('id','?')}]" for c in cond_list]
        choice, ok = QInputDialog.getItem(parent, "Zustand auswählen", "Welchen Zustand möchtest du hinzufügen?", choices, 0, False)
        if not ok:
            return

        idx = choices.index(choice)
        chosen = cond_list[idx]
        self._activate_condition(chosen, source_item=None)

    # -----------------------------------------------------
    # 🧩 Zustand im UI darstellen
    # -----------------------------------------------------
    def render_condition_block(self, cid, cond_data, source_item=None):
        parent = self.parent
        cond_name = cond_data.get("name", f"Zustand {cid[:8]}")
        desc = cond_data.get("description", "")
        effect_type = cond_data.get("effect_type", "keine Auswirkung")
        effect_target = cond_data.get("effect_target", "")
        effect_value = cond_data.get("effect_value", 0)

        group = QGroupBox(cond_name)
        parent.style_groupbox(group)
        layout = QVBoxLayout()

        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Effektanzeige
        if effect_type != "keine Auswirkung" and effect_target:
            target_ok = self._is_condition_target_valid_for_this_character(effect_target)
            effect_label = QLabel(
                f"{effect_type.capitalize()}e Wirkung: {effect_target} {effect_value:+}"
                + ("" if target_ok else " ⚠ (nicht vorhanden)")
            )
            effect_label.setWordWrap(True)
            effect_label.setStyleSheet("color: #b00;" if not target_ok else "color: #555; font-style: italic;")
            layout.addWidget(effect_label)

        # Item-Herkunft anzeigen
        if source_item:
            src_label = QLabel(f"Aktiv durch Item: {source_item}")
            src_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(src_label)

        # Entfernen-Button nur für manuelle Zustände
        if source_item is None:
            remove_button = QPushButton("– Zustand entfernen")
            remove_button.clicked.connect(lambda _, cid=cid: self.remove_manual_condition(cid))
            layout.addWidget(remove_button)

        group.setLayout(layout)
        insert_pos = max(0, parent.conditions_layout.count() - 2)
        parent.conditions_layout.insertWidget(insert_pos, group)
        return group

    # -----------------------------------------------------
    # 🧩 Zustand aktivieren und anzeigen
    # -----------------------------------------------------
    def _activate_condition(self, cond_data, source_item=None):
        parent = self.parent
        cid = cond_data.get("id", str(uuid.uuid4()))

        # Refcount
        parent.condition_refcount[cid] = parent.condition_refcount.get(cid, 0) + 1
        if cid in parent.active_condition_by_id:
            return  # schon aktiv → nichts tun

        group_widget = self.render_condition_block(cid, cond_data, source_item)
        cond_data["_widget"] = group_widget
        parent.active_condition_by_id[cid] = cond_data

        parent.recalculate_conditions_effects()

    # -----------------------------------------------------
    # 🧩 Manuell entfernten Zustand deaktivieren
    # -----------------------------------------------------
    def remove_manual_condition(self, cid):
        parent = self.parent
        if cid not in parent.condition_refcount:
            return

        parent.condition_refcount[cid] -= 1
        if parent.condition_refcount[cid] <= 0:
            parent.condition_refcount.pop(cid, None)
            self._remove_condition_widget(cid)
            parent.active_condition_by_id.pop(cid, None)

        parent.recalculate_conditions_effects()

    # -----------------------------------------------------
    # 🧩 Zustand-UI entfernen
    # -----------------------------------------------------
    def _remove_condition_widget(self, cid):
        parent = self.parent
        cond_info = parent.active_condition_by_id.get(cid)
        if not cond_info:
            return

        widget = cond_info.get("_widget")
        if widget:
            parent.conditions_layout.removeWidget(widget)
            widget.deleteLater()

    # -----------------------------------------------------
    # 🧩 Ziel-Listen aufbauen
    # -----------------------------------------------------
    def _build_condition_target_lists(self):
        parent = self.parent
        skill_targets = []
        category_targets = []
        insp_targets = []
        for cat, skill_list in parent.skills.items():
            for skill in skill_list:
                skill_targets.append(f"Fertigkeit: {skill}")
            category_targets.append(f"Kategoriewert: {cat}")
            insp_targets.append(f"Geistesblitzpunkte: {cat}")
        return skill_targets, category_targets, insp_targets

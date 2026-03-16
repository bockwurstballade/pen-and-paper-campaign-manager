from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QMessageBox
from typing import Dict, Any

from classes.ui.character_creation.conditions import CharacterCreationDialogConditions
from classes.core.data_manager import DataManager
from classes.ui.ui_utils import style_groupbox

class ConditionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Handle dialog requests
        self.conditions_handler = CharacterCreationDialogConditions(self)
        
        # State tracking (formerly on CharacterCreationDialog)
        self.active_condition_by_id = {}
        self.condition_refcount = {}
        self.condition_groups = {} # für recalculate_conditions_effects
        
        # UI initialisieren
        self.conditions_group = QGroupBox("Zustände")
        style_groupbox(self.conditions_group)
        self.conditions_layout = QVBoxLayout()
        
        self.condition_add_button = QPushButton("+ Neuer Zustand")
        self.condition_add_button.clicked.connect(self.conditions_handler.add_condition)
        self.conditions_layout.addWidget(self.condition_add_button)

        self.condition_add_from_lib_button = QPushButton("+ Zustand aus Sammlung hinzufügen")
        self.condition_add_from_lib_button.clicked.connect(self.conditions_handler.add_condition_from_library)
        self.conditions_layout.addWidget(self.condition_add_from_lib_button)
        
        self.conditions_group.setLayout(self.conditions_layout)
        self.layout.addWidget(self.conditions_group)

        # Referenz für Dialog (für BaseStats/Skills Effect Updates)
        self.main_dialog = parent



    def get_data(self) -> Dict[str, Any]:
        """Gibt die gespeicherten Zustandsdaten für den Save zurück."""
        conditions_data = {}
        for cid, cond_data in self.active_condition_by_id.items():
            cleaned = {
                "id": cid,
                "name": cond_data.get("name", ""),
                "description": cond_data.get("description", ""),
                "effect_type": cond_data.get("effect_type", "keine Auswirkung"),
                "effect_target": cond_data.get("effect_target", ""),
                "effect_value": cond_data.get("effect_value", 0),
            }
            conditions_data[cleaned["name"]] = cleaned
        return conditions_data


    def manual_remove_condition_by_id(self, cid):
        """
        Entfernt einen manuell erstellten Zustand endgültig.
        """
        if cid not in self.condition_refcount:
            return

        self.condition_refcount[cid] -= 1
        if self.condition_refcount[cid] <= 0:
            self.condition_refcount.pop(cid, None)
            self.remove_condition_widget_by_id(cid)

            to_delete = []
            for name, data in self.condition_groups.items():
                if data.get("id") == cid:
                    to_delete.append(name)
            for name in to_delete:
                del self.condition_groups[name]

        self.recalculate_conditions_effects()

    def remove_condition_widget_by_id(self, cid):
        """Entfernt die UI-Darstellung eines Zustands."""
        cond_info = self.active_condition_by_id.get(cid)
        if not cond_info:
            return

        widget = cond_info.get("_widget")
        if widget:
            self.conditions_layout.removeWidget(widget)
            widget.deleteLater()
        
        condition_name = cond_info["name"]
        self.active_condition_by_id.pop(cid, None)
        
        if condition_name in self.condition_groups:
            group = self.condition_groups[condition_name]["group"]
            self.conditions_layout.removeWidget(group)
            group.deleteLater()
            del self.condition_groups[condition_name]
            QMessageBox.information(self, "Erfolg", f"Zustand '{condition_name}' wurde entfernt.")
        
        self.recalculate_conditions_effects()


    def attach_item_conditions(self, item_name, condition_ids):
        conditions = DataManager.get_all_conditions()
        cond_map = {c["id"]: c for c in conditions}

        for cid in condition_ids:
            cond_data = cond_map.get(cid)
            if not cond_data:
                cond_data = {
                    "id": cid,
                    "name": f"(Unbekannter Zustand {cid[:8]}...)",
                    "description": "Originalzustand nicht gefunden.",
                    "effect_type": "keine Auswirkung",
                    "effect_target": "",
                    "effect_value": 0
                }

            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            if cid in self.active_condition_by_id:
                continue

            self.render_condition_block_from_condition_data(cid, cond_data, source_item=item_name)
            self.active_condition_by_id[cid] = cond_data

        self.recalculate_conditions_effects()


    def render_condition_block_from_condition_data(self, cid, cond_data, source_item=None):
        """Delegiert an den conditions_handler, der die gleiche Logik implementiert."""
        group = self.conditions_handler.render_condition_block(cid, cond_data, source_item)

        temp = self.active_condition_by_id.get(cid, {})
        temp["_widget"] = group
        self.active_condition_by_id[cid] = {**cond_data, **temp}


    def recalculate_conditions_effects(self):
        self.condition_groups = {}

        for cid, cond_data in self.active_condition_by_id.items():
            widget = cond_data.get("_widget")
            if widget is None:
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

        if hasattr(self.main_dialog, "apply_all_mission_effects"):
            self.main_dialog.apply_all_mission_effects()


    def load_data(self, character: Dict[str, Any], items_widget):
        """Loads data from Save. Needs reference to ItemsWidget for item linking."""
        # Clears old condition groups
        for cid, cond_data in list(self.active_condition_by_id.items()):
             if "_widget" in cond_data:
                 self.conditions_layout.removeWidget(cond_data["_widget"])
                 cond_data["_widget"].deleteLater()

        self.active_condition_by_id = {}
        self.condition_refcount = {}

        # 1) Zustände aus Items anhängen
        for item_name, cond_ids in items_widget.item_condition_links.items():
            self.attach_item_conditions(item_name, cond_ids)

        # 2) Zustände aus dem Save explizit wiederherstellen (manuell aktivierte)
        import uuid
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

            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            if cid not in self.active_condition_by_id:
                self.active_condition_by_id[cid] = cond_data
                self.render_condition_block_from_condition_data(cid, cond_data, source_item=None)

        self.recalculate_conditions_effects()

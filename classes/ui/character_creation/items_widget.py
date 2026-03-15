from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QCheckBox
from typing import Dict, Any

from classes.ui.character_creation.items import CharacterCreationDialogItems

class ItemsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.items_handler = CharacterCreationDialogItems(self)
        
        # State tracking (formerly on CharacterCreationDialog)
        self.item_groups = {}
        self.item_condition_links = {}

        # UI initialisieren
        self.items_group = QGroupBox("Items")
        self.style_groupbox(self.items_group)
        self.items_layout = QVBoxLayout()
        
        self.item_add_button = QPushButton("+ Neues Item")
        self.item_add_button.clicked.connect(self.items_handler.add_item)
        self.items_layout.addWidget(self.item_add_button)
        
        self.item_add_from_lib_button = QPushButton("+ Item aus Sammlung hinzufügen")
        self.item_add_from_lib_button.clicked.connect(self.items_handler.add_item_from_library)
        self.items_layout.addWidget(self.item_add_from_lib_button)
        
        self.items_group.setLayout(self.items_layout)
        self.layout.addWidget(self.items_group)

        self.save_new_items_globally_checkbox = QCheckBox("Neue Items auch in der globalen Sammlung (items.json) speichern")
        self.save_new_items_globally_checkbox.setChecked(True)
        self.items_layout.addWidget(self.save_new_items_globally_checkbox)

        # Referenz für Conditions: Wir brauchen oft Zugriff auf den Parent-Dialog
        # um die Mission Effects zu triggern, wenn Item-Zustände aktiv werden.
        # Der Handler ruft `self.parent.attach_item_conditions`,
        # was wir auf den echten Dialog durchleiten müssen.
        self.main_dialog = parent

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

    def attach_item_conditions(self, item_name, condition_ids):
        """Leitet den Request vom Item-Handler an den Hauptdialog (oder später ConditionsWidget) weiter."""
        if hasattr(self.main_dialog, "attach_item_conditions"):
            self.main_dialog.attach_item_conditions(item_name, condition_ids)

    def remove_condition_widget_by_id(self, cid):
        """Leitet weiter."""
        if hasattr(self.main_dialog, "remove_condition_widget_by_id"):
            self.main_dialog.remove_condition_widget_by_id(cid)

    def load_data(self, character: Dict[str, Any]):
        # Alle alten Item-Widgets löschen, bevor wir neu laden
        for item_name, data in self.item_groups.items():
            if "group" in data:
                self.items_layout.removeWidget(data["group"])
                data["group"].deleteLater()

        self.item_groups = {}
        self.item_condition_links = {}

        # Der ehemals riesige Block aus dem Dialog für das Rendern der Items
        self.items_handler.restore_items_from_data(character.get("items", {}))

    def get_data(self) -> Dict[str, Any]:
        """Sammelt alle Items zusammen, so wie es vorher `save_character` gemacht hat."""
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
                "weapon_state": {
                    "chambers": data.get("chambers_loaded_spin").value() if data.get("chambers_loaded_spin") else 0,
                    "chambers_capacity": data.get("chambers_capacity_spin").value() if data.get("chambers_capacity_spin") else 0,
                    "magazine": {
                        "inserted": data.get("magazine_inserted_cb").isChecked() if data.get("magazine_inserted_cb") else False,
                        "count": data.get("magazine_count_spin").value() if data.get("magazine_count_spin") else 0,
                        "capacity": data.get("magazine_capacity_spin").value() if data.get("magazine_capacity_spin") else 0,
                    },
                    "projectiles_loaded": data.get("projectiles_loaded_spin").value() if data.get("projectiles_loaded_spin") else 0,
                    "projectile_type": data.get("projectile_type_input").text().strip() if data.get("projectile_type_input") else "",
                }
            }
        return items_data

    # Delegation Methoden für den Dialog (z.B. fürs globale Speichern)
    def upsert_items_to_global_library(self):
        self.items_handler.upsert_items_to_global_library()

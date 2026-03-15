from PyQt6.QtWidgets import QGroupBox, QFormLayout, QCheckBox, QLineEdit
from typing import Dict, Any, Optional
from PyQt6.QtCore import Qt

class ArmorWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Rüstung", parent)
        
        # Das CSS Styling lag früher im Dialog, wir setzen es hier
        self.setStyleSheet("""
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
        
        armor_layout = QFormLayout(self)

        self.armor_enabled_checkbox = QCheckBox("Rüstungsmodul aktivieren")
        self.armor_enabled_checkbox.stateChanged.connect(self.toggle_armor_fields)
        armor_layout.addRow(self.armor_enabled_checkbox)

        self.armor_value_input = QLineEdit()
        self.armor_value_input.setPlaceholderText("0–9")
        self.armor_condition_input = QLineEdit()
        self.armor_condition_input.setPlaceholderText("0–9")

        self.armor_value_input.setVisible(False)
        self.armor_condition_input.setVisible(False)

        armor_layout.addRow("Rüstungswert:", self.armor_value_input)
        armor_layout.addRow("Rüstungszustand:", self.armor_condition_input)

    def set_fields_visibility(self, visible: bool):
        self.armor_value_input.setVisible(visible)
        self.armor_condition_input.setVisible(visible)

    def toggle_armor_fields(self, state):
        is_active = state == Qt.CheckState.Checked.value
        self.set_fields_visibility(is_active)

    def load_data(self, character: Dict[str, Any]):
        armor_enabled = character.get("armor_enabled", False)
        armor_value = character.get("armor_value")
        armor_condition = character.get("armor_condition")

        # Block Signals
        self.armor_enabled_checkbox.blockSignals(True)
        self.armor_enabled_checkbox.setChecked(armor_enabled)
        self.armor_enabled_checkbox.blockSignals(False)

        if armor_value is not None:
            self.armor_value_input.setText(str(armor_value))
        if armor_condition is not None:
            self.armor_condition_input.setText(str(armor_condition))

        # Update visibility
        self.set_fields_visibility(armor_enabled)

    def get_data(self) -> Dict[str, Any]:
        armor_enabled = self.armor_enabled_checkbox.isChecked()
        armor_val = None
        armor_cond = None

        if armor_enabled:
            val_text = self.armor_value_input.text()
            cond_text = self.armor_condition_input.text()
            
            # Simple validation, will be re-validated by Builder
            armor_val = int(val_text) if val_text else 0
            armor_cond = int(cond_text) if cond_text else 0

        return {
            "armor_enabled": armor_enabled,
            "armor_value": armor_val,
            "armor_condition": armor_cond
        }

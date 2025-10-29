"""
Alles was mit Rüstung innerhalb des Charakter Erstellbildschirmes zu tun hat
"""
# imports
from PyQt6.QtCore import Qt

class CharacterCreationDialogArmor:
    def __init__(self, dialog):
        self.dialog = dialog

    def toggle_armor_fields(self, state):
        is_active = state == Qt.CheckState.Checked.value
        self.dialog.armor_value_input.setVisible(is_active)
        self.dialog.armor_condition_input.setVisible(is_active)

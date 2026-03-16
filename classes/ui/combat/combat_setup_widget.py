from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QInputDialog
)
import uuid
from classes.core.data_manager import DataManager

class CombatSetupWidget(QWidget):
    def __init__(self, main_dialog, parent=None):
        super().__init__(parent)
        self.main_dialog = main_dialog
        self.teams = ["Team A", "Team B"]

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Team Auswahl
        self.team_select = QComboBox()
        self.team_select.addItems(self.teams)
        self.add_team_button = QPushButton("+ Team hinzufügen")
        self.add_team_button.clicked.connect(self.add_new_team)

        self.layout.addWidget(QLabel("Neuen Kämpfer hinzufügen:"))
        self.layout.addWidget(QLabel("Team:"))
        self.layout.addWidget(self.team_select)
        self.layout.addWidget(self.add_team_button)

        # Buttons: PC / NSC hinzufügen
        self.add_pc_button = QPushButton("Spielercharakter hinzufügen")
        self.add_pc_button.clicked.connect(lambda: self.add_combatant(from_role="pc"))
        self.layout.addWidget(self.add_pc_button)

        self.add_npc_button = QPushButton("NSC hinzufügen")
        self.add_npc_button.clicked.connect(lambda: self.add_combatant(from_role="npc"))
        self.layout.addWidget(self.add_npc_button)

        self.layout.addStretch()

    def add_new_team(self):
        name, ok = QInputDialog.getText(self, "Neues Team", "Team-Name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.teams:
            QMessageBox.information(self, "Hinweis", "Team existiert bereits.")
            return
        self.teams.append(name)
        self.team_select.addItem(name)
        self.team_select.setCurrentText(name)

    def load_characters_by_role(self, role_filter):
        """
        role_filter ist "pc" oder "npc".
        Gibt Liste aus Dicts zurück:
        { "display": "...", "path": "...", "data": {...} }
        """
        return DataManager.get_characters_by_role(role_filter)

    def add_combatant(self, from_role):
        # from_role ist "pc" oder "npc"
        candidates = self.load_characters_by_role(from_role)
        if not candidates:
            QMessageBox.information(self, "Hinweis", f"Keine {from_role.upper()}-Charaktere gefunden.")
            return

        # Liste für User lesbar
        display_names = [c["display"] for c in candidates]

        choice, ok = QInputDialog.getItem(
            self,
            "Charakter wählen",
            "Wen willst du in den Kampf schicken?",
            display_names,
            0,
            False
        )
        if not ok:
            return

        idx = display_names.index(choice)
        chosen_char = candidates[idx]["data"]  # das echte JSON vom Charakter

        base_name = chosen_char.get("name", "Unbenannt")
        max_hp = chosen_char.get("hitpoints", 0)
        source_id = chosen_char.get("id", "???")

        team_name = self.team_select.currentText()

        # Wenn NPC → nach Anzahl fragen
        count = 1
        if from_role == "npc":
            count_txt, ok = QInputDialog.getText(
                self,
                "Anzahl",
                f"Wieviele Instanzen von '{base_name}' hinzufügen?"
            )
            if not ok:
                return
            try:
                count_val = int(count_txt)
                if count_val < 1:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Bitte eine ganze Zahl >=1 eingeben.")
                return
            count = count_val

        # Instanzen erzeugen
        for i in range(count):
            inst_name = base_name if count == 1 else f"{base_name} #{i+1}"

            actor = {
                "instance_id": str(uuid.uuid4()),
                "source_char_id": source_id,
                "display_name": inst_name,
                "team": team_name,
                "current_hp": max_hp,
                "max_hp": max_hp,
                "unconscious": False, # Bewusstlos-Status
                "dead": False,  # Neu: Tot-Status
            }
            self.main_dialog.combat_manager.add_combatant(actor)

        # UI neu aufbauen auf dem main_dialog (oder via list widget)
        self.main_dialog.refresh_actor_list()

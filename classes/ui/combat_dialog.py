import os
import json
import uuid

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

from classes.ui.surprise_dialog import SurpriseDialog
from classes.ui.initiative_dialog import InitiativeDialog
from classes.core.data_manager import DataManager
from classes.core.combat_manager import CombatManager

# Neue Komponenten
from classes.ui.combat.combat_setup_widget import CombatSetupWidget
from classes.ui.combat.combat_actor_list_widget import CombatActorListWidget
from classes.ui.combat.combat_turn_widget import CombatTurnWidget
from classes.ui.combat.combat_log_widget import CombatLogWidget
from classes.ui.combat.combat_action_handler import CombatActionHandler

class CombatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Kampf-Übersicht")
        self.setGeometry(200, 200, 800, 600)

        # --- State & Logic ---
        self.combat_manager = CombatManager()
        self.action_handler = CombatActionHandler(self)

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        
        # Obere Hälfte: 3 Spalten
        top_layout = QHBoxLayout()
        
        # 1. Setup Widget (Links)
        self.setup_widget = CombatSetupWidget(self)
        top_layout.addWidget(self.setup_widget)

        # 2. Actor List (Mitte)
        middle_layout = QVBoxLayout()
        self.actor_list_widget = CombatActorListWidget(self)
        middle_layout.addWidget(self.actor_list_widget)
        
        self.set_surprise_button = QPushButton("Überraschungsrunde festlegen")
        self.set_surprise_button.clicked.connect(self.set_surprise_round)
        middle_layout.addWidget(self.set_surprise_button)
        
        self.start_battle_button = QPushButton("Kampf starten (Initiative bestimmen)")
        self.start_battle_button.clicked.connect(self.start_battle)
        middle_layout.addWidget(self.start_battle_button)

        top_layout.addLayout(middle_layout)

        # 3. Turn Widget (Rechts)
        self.turn_widget = CombatTurnWidget(self)
        top_layout.addWidget(self.turn_widget)

        main_layout.addLayout(top_layout)

        # Untere Hälfte: Kampf-Log
        self.log_widget = CombatLogWidget(self)
        main_layout.addWidget(self.log_widget)


    def load_character_data(self, char_id):
        """Hilfsfunktion: Lädt Charakterdaten über den DataManager anhand der ID."""
        return DataManager.get_character_by_id(char_id)

    def refresh_actor_list(self):
        """Passthrough zu ActorListWidget, wird oft von Setup aufgerufen."""
        self.actor_list_widget.refresh_actor_list()

    def set_surprise_round(self):
        """Öffnet den Dialog, um überrascht markierte Kämpfer zu wählen"""
        if not self.combat_manager.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = SurpriseDialog(self.combat_manager.battle_actors, self)
        if dlg.exec():
            # Update the manager's surprised list directly for now
            self.combat_manager.surprised_ids = dlg.get_surprised_ids()
            if self.combat_manager.surprised_ids:
                names = [
                    a["display_name"]
                    for a in self.combat_manager.battle_actors
                    if a["instance_id"] in self.combat_manager.surprised_ids
                ]
                msg = "<br>".join(names)
                QMessageBox.information(
                    self, "Überraschungsrunde",
                    f"Folgende Kämpfer sind überrascht:<br><br>{msg}"
                )
            else:
                QMessageBox.information(self, "Überraschungsrunde", "Niemand ist überrascht.")

    def start_battle(self):
        if not self.combat_manager.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = InitiativeDialog(self.combat_manager.battle_actors, self, surprised_ids=self.combat_manager.surprised_ids)
        if dlg.exec():
            order = dlg.get_sorted_initiative()
            if order:
                self.set_initiative_order(order)

    def set_initiative_order(self, order):
        """Speichert die Reihenfolge und zeigt sie im CombatTurnWidget an"""
        self.combat_manager.set_initiative_order(
            order=[r["actor"] for r in order],
            surprised_ids=self.combat_manager.surprised_ids
        )
        
        self.turn_widget.show_turn_area()
        self.turn_widget.refresh_turn_display()

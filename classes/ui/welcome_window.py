import sys
import json
import os
import uuid
# Qt Frontend
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

## eigene Klassen
### Untermenüs (einzelne Buttons)
from classes.ui.dice_roll_dialog import DiceRollDialog
from classes.ui.combat_dialog import CombatDialog
from classes.ui.character_creation_dialog import CharacterCreationDialog
from classes.ui.item_editor_dialog import ItemEditorDialog
from classes.ui.condition_editor_dialog import ConditionEditorDialog
from classes.ui.campaign_creation_dialog import CampaignCreationDialog
from classes.ui.player_editor_dialog import PlayerEditorDialog
from classes.core.data_manager import DataManager

class WelcomeWindow(QMainWindow):
    """
        Diese Klasse zeichnet über Qt das Hauptmenü
    """

    # Konfigurationsliste: (Button-Beschriftung, Callback-Methode)
    BUTTON_CONFIG = [
        ("Neuen Charakter erstellen", "start_character_creation"),
        ("Bestehenden Charakter laden", "load_character"),
        ("Neuen Spieler erstellen", "create_new_player"),
        ("Bestehenden Spieler laden", "load_player"),
        ("Neues Item erstellen", "create_new_item"),
        ("Bestehendes Item laden", "load_item"),
        ("Neuen Zustand erstellen", "create_new_condition"),
        ("Bestehenden Zustand laden", "load_condition"),
        ("Neue Kampagne erstellen", "start_campaign_creation"),
        ("Würfelprobe", "open_roll_dialog"),
        ("Kampf starten", "start_combat"),
    ]
    # Titel des Fensters in der UI
    WINDOW_TITLE = "How To Be A Hero Charakterverwaltung"

    ## METHODEN ZUM DARSTELLEN DAS HAUPTMENÜS
    def __init__(self):
        """
        Initialisiert das Hauptmenü mit zentraler Widget- und Layoutstruktur.
        Buttons werden datengetrieben über eine Konfigurationsliste erzeugt.
        """
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        """Konfiguriert Fenstergröße und Titel."""
        self.setWindowTitle(self.WINDOW_TITLE)
        # Etwas breiteres Standardfenster und sinnvolle Mindestgröße
        self.setMinimumSize(600, 400)
        self.resize(800, 500)
    def _setup_ui(self) -> None:
        """Erstellt zentrale Widgets, Layout und Inhalte."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self._add_header_labels(layout)
        self._add_configured_buttons(layout)
        layout.addStretch()
    def _add_header_labels(self, layout: QVBoxLayout) -> None:
        """Fügt Überschrift und Untertitel hinzu."""
        welcome_label = QLabel("Willkommen zur Charakterverwaltung!", self)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome_label)

        subtitle_label = QLabel(
            "Verwalten Sie Ihre Pen-and-Paper-Charaktere für 'How to Be a Hero'", self
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

    def _add_configured_buttons(self, layout: QVBoxLayout) -> None:
        """Erstellt und fügt alle Buttons basierend auf BUTTON_CONFIG hinzu."""
        for button_text, callback_name in self.BUTTON_CONFIG:
            button = self._create_button(button_text, callback_name)
            layout.addWidget(button)

    def _create_button(self, text: str, callback_name: str) -> QPushButton:
        """
        Erzeugt einen QPushButton mit gegebenem Text und verbindet ihn
        mit der entsprechenden Methode der Instanz.
        """
        button = QPushButton(text, self)
        callback = getattr(self, callback_name)
        button.clicked.connect(callback)
        return button

    def _collect_all_condition_targets_from_all_characters(self):
        """
        Sammelt aus allen gespeicherten Charakteren:
        - alle Fertigkeiten
        - alle Kategorien (Handeln / Wissen / Soziales / ...)
        - alle Geistesblitzpunkte-Kategorien

        Liefert Tupel (skill_targets, category_targets, inspiration_targets)
        so wie CharacterCreationDialog._build_condition_target_lists,
        nur eben über ALLE Chars gemergt.
        """
        skill_set = set()
        category_set = set()

        # Nutze den neuen DataManager
        chars = DataManager.get_all_characters()
        for char_info in chars:
            data = char_info["data"]
            # skills ist wie:
            # {
            #   "Handeln": {"Schleichen": 35, "Klettern": 20},
            #   "Wissen": {...},
            #   "Soziales": {...}
            # }
            skills_block = data.get("skills", {})
            for category_name, skills_dict in skills_block.items():
                # Kategorie merken
                category_set.add(category_name)

                # Skills merken
                for skill_name in skills_dict.keys():
                    skill_set.add(skill_name)

        # Jetzt Listen im passenden Format bauen
        skill_targets = [f"Fertigkeit: {skill}" for skill in sorted(skill_set)]
        category_targets = [f"Kategoriewert: {cat}" for cat in sorted(category_set)]
        inspiration_targets = [f"Geistesblitzpunkte: {cat}" for cat in sorted(category_set)]

        return skill_targets, category_targets, inspiration_targets

    ## METHODEN ZUM AUFRUF DER MENÜS HINTER EINEM BUTTON
    def start_combat(self):
        dlg = CombatDialog(self)
        dlg.exec()


    def start_character_creation(self):
        dialog = CharacterCreationDialog(self)
        dialog.char_id = str(uuid.uuid4())  # neue frische ID vergeben
        dialog.exec()

    def start_campaign_creation(self):
        dialog = CampaignCreationDialog(self)
        dialog.exec()

    def create_new_player(self):
        """Öffnet den Spieler-Editor leer für einen neuen Spieler."""
        dlg = PlayerEditorDialog(self)
        dlg.player_id = str(uuid.uuid4())
        dlg.exec()

    def load_player(self):
        """Lädt alle Spieler aus dem data/players/ Ordner, lässt den Nutzer einen wählen und öffnet ihn im Editor."""
        players_list = DataManager.get_all_players()
        if not players_list:
            QMessageBox.information(
                self,
                "Hinweis",
                "Es wurden noch keine Spieler gespeichert oder sie konnten nicht geladen werden.",
            )
            return

        player_names = [p["display"] for p in players_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Spieler auswählen",
            "Welchen Spieler möchtest du bearbeiten?",
            player_names,
            0,
            False,
        )
        if not ok:
            return

        chosen_index = player_names.index(choice)
        chosen_player = players_list[chosen_index]

        dlg = PlayerEditorDialog(self)
        dlg.load_player_data(chosen_player["data"], chosen_player["path"])
        dlg.exec()

    def load_character(self):
        candidates = DataManager.get_all_characters()
        if not candidates:
            QMessageBox.information(self, "Hinweis", "Es wurden noch keine Charaktere gespeichert oder sie konnten nicht geladen werden.")
            return

        # Liste der Anzeigenamen für Auswahl
        display_names = [c["display"] for c in candidates]

        choice, ok = QInputDialog.getItem(
            self,
            "Charakter wählen",
            "Welchen Charakter möchtest du laden?",
            display_names,
            0,
            False
        )
        if not ok:
            return

        idx = display_names.index(choice)
        chosen = candidates[idx]
        chosen_display, chosen_path, chosen_data = chosen["display"], chosen["path"], chosen["data"]

        # Dialog öffnen und Daten rein
        dialog = CharacterCreationDialog(self)
        dialog.load_character_data(chosen_data, chosen_path)
        dialog.exec()


    def create_new_item(self):
        """Öffnet den Item-Editor leer für ein neues Item."""
        dlg = ItemEditorDialog(self)
        # Neue UUID direkt setzen, damit beim Speichern klar ist, wer das ist
        dlg.item_id = str(uuid.uuid4())
        dlg.exec()

    def open_roll_dialog(self):
        dlg = DiceRollDialog(self)
        dlg.exec()

    def load_item(self):
        """Lädt alle Items aus dem data/items/ Ordner, lässt den Nutzer eines auswählen und öffnet es im Editor."""
        items_list = DataManager.get_all_items()
        if not items_list:
            QMessageBox.information(self, "Hinweis", "Es wurden noch keine Items gespeichert oder sie konnten nicht geladen werden.")
            return

        # Auswahl anzeigen
        item_names = [f"{it.get('name','(unbenannt)')} [{it.get('id','?')}]" for it in items_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Item auswählen",
            "Welches Item möchtest du bearbeiten?",
            item_names,
            0,
            False
        )
        if not ok:
            return

        chosen_index = item_names.index(choice)
        chosen_item = items_list[chosen_index]

        # Editor öffnen und Item laden
        dlg = ItemEditorDialog(self)
        dlg.load_item_data(chosen_item)
        dlg.exec()

    def create_new_condition(self):
        """Öffnet den Zustands-Editor leer zum Erstellen eines neuen Zustands."""

        # Sammle alle sinnvollen Ziele aus ALLEN gespeicherten Charakteren
        skill_targets, cat_targets, insp_targets = self._collect_all_condition_targets_from_all_characters()

        dlg = ConditionEditorDialog(
            parent=self,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.condition_id = str(uuid.uuid4())  # direkt frische UUID vergeben
        dlg.exec()


    def load_condition(self):
        """Lädt alle Zustände aus dem data/conditions/ Ordner, lässt den Nutzer einen wählen und öffnet ihn im Editor."""
        conditions_list = DataManager.get_all_conditions()
        if not conditions_list:
            QMessageBox.information(self, "Hinweis", "Es wurden noch keine Zustände gespeichert oder sie konnten nicht geladen werden.")
            return

        # Auswahl anzeigen
        cond_choices = [
            f"{c.get('name', '(unbenannt)')} [{c.get('id','?')}]"
            for c in conditions_list
        ]

        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du bearbeiten?",
            cond_choices,
            0,
            False
        )
        if not ok:
            return

        chosen_index = cond_choices.index(choice)
        chosen_condition = conditions_list[chosen_index]

        # Ziele für den ConditionEditorDialog sammeln
        skill_targets, cat_targets, insp_targets = self._collect_all_condition_targets_from_all_characters()

        dlg = ConditionEditorDialog(
            parent=self,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.load_condition_data(chosen_condition)
        dlg.exec()
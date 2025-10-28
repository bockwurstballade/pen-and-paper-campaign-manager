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

class WelcomeWindow(QMainWindow):
    """
        Diese Klasse zeichnet über Qt das Hauptmenü
    """

    # Konfigurationsliste: (Button-Beschriftung, Callback-Methode)
    BUTTON_CONFIG = [
        ("Neuen Charakter erstellen", "start_character_creation"),
        ("Bestehenden Charakter laden", "load_character"),
        ("Neues Item erstellen", "create_new_item"),
        ("Bestehendes Item laden", "load_item"),
        ("Neuen Zustand erstellen", "create_new_condition"),
        ("Bestehenden Zustand laden", "load_condition"),
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
        self.setGeometry(100, 100, 400, 300)
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

        characters_dir = "characters"
        if os.path.isdir(characters_dir):
            for fname in os.listdir(characters_dir):
                if not fname.lower().endswith(".json"):
                    continue
                full_path = os.path.join(characters_dir, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue  # kaputte Datei ignorieren

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


    def load_character(self):
        # Verzeichnis sicherstellen
        if not os.path.exists("characters"):
            QMessageBox.information(self, "Hinweis", "Es wurden noch keine Charaktere gespeichert.")
            return

        # Alle JSON-Dateien einsammeln
        candidates = []
        for fname in os.listdir("characters"):
            if fname.lower().endswith(".json"):
                full_path = os.path.join("characters", fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # wir erwarten ein einzelnes Charakter-Objekt (unser neues Format)
                    char_name = data.get("name", "(unbenannt)")
                    char_class = data.get("class", "?")
                    char_age = data.get("age", "?")
                    char_id = data.get("id", "???")

                    display = f"{char_name} | {char_class}, {char_age} Jahre [{char_id[:8]}...]"
                    candidates.append((display, full_path, data))
                except Exception:
                    # Datei ignorieren, wenn sie nicht lesbar ist
                    pass

        if not candidates:
            QMessageBox.information(self, "Hinweis", "Keine gültigen Charakterdateien gefunden.")
            return

        # Liste der Anzeigenamen für Auswahl
        display_names = [c[0] for c in candidates]

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
        chosen_display, chosen_path, chosen_data = candidates[idx]

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
        """Lädt items.json ODER eine andere Datei, lässt den Nutzer ein Item auswählen, öffnet es im Editor."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Item-Datei öffnen",
            "",
            "JSON Dateien (*.json);;Alle Dateien (*)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden der Datei:\n{e}")
            return

        # Erwartet { "items": [ {...}, {...} ] }
        if not (isinstance(data, dict) and "items" in data and isinstance(data["items"], list)):
            QMessageBox.warning(self, "Fehler", "In der ausgewählten Datei wurden keine Items gefunden.")
            return

        items_list = data["items"]
        if not items_list:
            QMessageBox.warning(self, "Fehler", "Die Datei enthält keine Items.")
            return

        # Falls mehrere Items drin sind: den Nutzer auswählen lassen
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

        # anhand der Auswahl das konkrete Item raussuchen
        chosen_index = item_names.index(choice)
        chosen_item = items_list[chosen_index]

        # Editor öffnen und Item laden
        dlg = ItemEditorDialog(self)
        dlg.load_item_data(chosen_item, file_name)
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
        """Lädt eine conditions.json (oder andere Datei), lässt den Nutzer einen Zustand wählen und öffnet ihn im Editor."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Zustands-Datei öffnen",
            "",
            "JSON Dateien (*.json);;Alle Dateien (*)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden der Datei:\n{e}")
            return

        # erwartet { "conditions": [ {...}, {...} ] }
        if not (isinstance(data, dict) and "conditions" in data and isinstance(data["conditions"], list)):
            QMessageBox.warning(self, "Fehler", "In der ausgewählten Datei wurden keine Zustände gefunden.")
            return

        conditions_list = data["conditions"]
        if not conditions_list:
            QMessageBox.warning(self, "Fehler", "Die Datei enthält keine Zustände.")
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

        dlg = ConditionEditorDialog(self)
        dlg.load_condition_data(chosen_condition, file_name)
        dlg.exec()
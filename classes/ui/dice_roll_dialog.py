# benötigte Imports

## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt


## eigene klassen
from classes.core.character_calculator import CharacterCalculator
from classes.core.dice.roll.evaluate import DiceRollEvaluator

## eigene Funktionen
from utils.functions.metadata import load_all_characters_from_folder
from utils.functions.math import kaufmaennisch_runden

class DiceRollDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Würfelprobe")
        self.setGeometry(300, 300, 400, 300)

        self.characters = load_all_characters_from_folder()
        self.current_char = None  # dict mit allen Daten des ausgewählten Charakters
        self.char_effective = None  # vorberechnete Strukturen (siehe unten)

        # Widgets
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 1) Charakter-Auswahl
        self.char_select = QComboBox()
        if self.characters:
            for c in self.characters:
                self.char_select.addItem(c["display"])
        else:
            self.char_select.addItem("<<kein Charakter gefunden>>")
        self.char_select.currentIndexChanged.connect(self.on_character_changed)
        form.addRow("Charakter:", self.char_select)

        # 2) Fertigkeit / Kategorie Auswahl
        self.skill_select = QComboBox()
        self.skill_select.currentIndexChanged.connect(self.on_skill_changed)
        form.addRow("Fertigkeit / Kategorie:", self.skill_select)

        # 3) Endwert-Anzeige (read only)
        self.endwert_display = QLineEdit()
        self.endwert_display.setReadOnly(True)
        form.addRow("Endwert:", self.endwert_display)

        # 4) Bonus/Malus Eingabe (Erleichtern um ...)
        self.bonus_input = QLineEdit()
        self.bonus_input.setPlaceholderText("z. B. 5 oder -10")
        self.bonus_input.textChanged.connect(self.update_effective_target_value)
        form.addRow("Erleichtern um:", self.bonus_input)

        # 5) Wurf-Ergebnis Eingabe (1-100)
        self.roll_input = QLineEdit()
        self.roll_input.setPlaceholderText("z. B. 42 oder 100")
        form.addRow("Gewürfelter Wert:", self.roll_input)

        layout.addLayout(form)

        # Ergebnisfeld
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        # Button "Auswerten"
        self.eval_button = QPushButton("Auswerten")
        self.eval_button.clicked.connect(self.evaluate_roll)
        layout.addWidget(self.eval_button)

        layout.addStretch()

        # Initial: ersten Charakter laden (falls vorhanden)
        if self.characters:
            self.on_character_changed(0)

    # --- UI-Callbacks ---

    def on_character_changed(self, index):
        """Wird gerufen, wenn im DropDown ein anderer Charakter gewählt wurde."""
        if not self.characters:
            self.current_char = None
            self.skill_select.clear()
            self.endwert_display.setText("")
            return

        chosen = self.characters[index]
        self.current_char = chosen["data"]

        # effektive Werte vorberechnen
        self.char_effective = CharacterCalculator.compute_effective_values(self.current_char)

        # Skill-Liste neu aufbauen
        # Wir bieten zuerst Kategorien, dann einen Trenner, dann Skills
        self.skill_select.blockSignals(True)
        self.skill_select.clear()

        # Kategorien
        for cat_name in self.char_effective["categories"].keys():
            self.skill_select.addItem(f"[Kategorie] {cat_name}")

        # Trenner (optional; nur wenn es beides gibt)
        if self.char_effective["categories"] and self.char_effective["skills"]:
            self.skill_select.addItem("----------")

        # Skills
        for skill_name in self.char_effective["skills"].keys():
            self.skill_select.addItem(skill_name)

        self.skill_select.blockSignals(False)

        # direkt erste sinnvolle Auswahl setzen
        if self.skill_select.count() > 0:
            self.skill_select.setCurrentIndex(0)
            self.on_skill_changed(0)
        else:
            self.endwert_display.setText("")

    def on_skill_changed(self, index):
        """Immer wenn eine andere Fertigkeit/Kategorie gewählt wird -> Endwert neu anzeigen."""
        self.update_endwert_display()
        self.update_effective_target_value()

    def current_selected_value(self):
        """
        Ermittelt den reinen Endwert (ohne 'Erleichtern um') für die aktuell
        ausgewählte Zeile der Combobox.
        """
        if not self.char_effective or self.skill_select.count() == 0:
            return 0

        sel = self.skill_select.currentText().strip()

        if sel.startswith("[Kategorie] "):
            cat_name = sel.replace("[Kategorie] ", "", 1)
            return self.char_effective["categories"].get(cat_name, 0)

        if sel == "----------":
            return 0

        # sonst ist es ein Skill
        return self.char_effective["skills"].get(sel, 0)

    def update_endwert_display(self):
        """
        Zeigt den 'Endwert' (also Chance %) ohne Bonus/Malus im readonly Feld.
        """
        base_val = self.current_selected_value()
        self.endwert_display.setText(str(base_val))

    def update_effective_target_value(self):
        """
        Diese Funktion könntest du benutzen, falls du live irgendwo anzeigen willst:
        'Effektive Zielchance nach Erleichterung'.
        Gerade schreiben wir sie nur, damit der Wert da ist, bevor evaluate_roll ruft.
        """
        # nothing to update live in UI (optional field if du's anzeigen willst)
        pass

    # --- Auswertung der Probe ---

    def evaluate_roll(self):
            """
            Liest: 
            - Endwert (mit Zuständen usw.)
            - Bonus/Malus ("Erleichtern um")
            - Gewürfelte Zahl
            und bestimmt Erfolg + kritisch? + kritisch gut/schlecht?
            """
            # 1) Grundchance
            base_chance = self.current_selected_value()

            # 2) Bonus/Malus
            bonus_txt = self.bonus_input.text().strip()
            if bonus_txt == "":
                bonus_val = 0
            else:
                try:
                    bonus_val = int(bonus_txt)
                except ValueError:
                    QMessageBox.warning(self, "Fehler", "Bitte eine ganze Zahl bei 'Erleichtern um' eingeben (z. B. 5 oder -10).")
                    return
            
            # WICHTIG: Berechne final_chance hier nur für das Logging
            # Der Evaluator macht die Berechnung selbst.
            final_chance = base_chance + bonus_val

            # 3) Wurf lesen
            roll_txt = self.roll_input.text().strip()
            try:
                roll_val = int(roll_txt)
            except ValueError:
                QMessageBox.warning(self, "Fehler", "Bitte das tatsächliche Würfelergebnis (1-100) als ganze Zahl eingeben.")
                return

            # Spezialfall: 0 ("0 + 00" auf den Würfeln) ist das gleiche wie 100 (kritischer Fehlschlag)
            if roll_val == 0:
                roll_val = 100

            if not (1 <= roll_val <= 100):
                QMessageBox.warning(self, "Fehler", "Würfelwert muss zwischen 1 und 100 liegen (0 zählt als 100).")
                return
            
            # --- HIER IST DIE KORREKTUR ---

            # 1. Erstelle eine Instanz des Evaluators
            evaluator = DiceRollEvaluator()

            # 2. Rufe die Methode auf der *Instanz* auf und übergib die Rohdaten
            result = evaluator.evaluate_roll({
                "base_chance": base_chance,  # Übergib die Basis-Chance
                "bonus": bonus_val,          # Übergib den Bonus separat
                "rolled": roll_val
            })

            # 3. Greife auf das Ergebnis als Dictionary (TypedDict) zu
            success = result['success']
            crit = result['crit']

            # --- ENDE DER KORREKTUR ---

            # Ergebnis-Text bauen
            if success:
                outcome_text = "Erfolg ✅"
            else:
                outcome_text = "Fehlschlag ❌"

            if crit and success:
                outcome_text = "KRITISCHER ERFOLG 🏅 (" + outcome_text + ")"
            elif not success and crit:
                outcome_text = "KRITISCHER FEHLSCHLAG 💥 (" + outcome_text + ")"

            # Noch ein paar Debug-Infos, damit der SL alles sieht
            details = (
                f"Grundchance: {base_chance}  |  Modifikator: {bonus_val:+}  "
                f"→ Zielwert: {final_chance}\n"  # final_chance von oben verwenden
                f"Wurf: {roll_val}\n"
            )

            self.result_label.setText(outcome_text + "\n\n" + details)
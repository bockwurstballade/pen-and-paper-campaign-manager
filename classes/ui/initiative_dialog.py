# benötigte Imports
import os
import json
## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

## eigene Funktionen
from utils.functions.math import kaufmaennisch_runden


class InitiativeDialog(QDialog):
    def __init__(self, battle_actors, parent=None, surprised_ids=None):
        super().__init__(parent)
        self.setWindowTitle("Initiative bestimmen")
        self.setGeometry(300, 200, 600, 500)

        self.battle_actors = battle_actors  # aus CombatDialog
        self.surprised_ids = surprised_ids or set()
        self.initiatives = {}  # instance_id → total_initiative

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Würfe für Initiative:</b>"))
        layout.addWidget(QLabel("Für jeden Kämpfer 1W10 (0 = 10) + Handeln + Bonus/Malus"))

        self.form_layout = QFormLayout()
        self.inputs = {}

        for actor in self.battle_actors:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)

            roll_input = QLineEdit()
            roll_input.setPlaceholderText("Wurf (1-10 oder 0=10)")
            bonus_input = QLineEdit()
            bonus_input.setPlaceholderText("Bonus/Malus")

            h.addWidget(QLabel(actor["display_name"] + (" 😮" if actor["instance_id"] in self.surprised_ids else "")))
            h.addWidget(roll_input)
            h.addWidget(bonus_input)
            self.inputs[actor["instance_id"]] = {
                "roll": roll_input,
                "bonus": bonus_input
            }
            self.form_layout.addRow(row)

        layout.addLayout(self.form_layout)

        self.calc_button = QPushButton("Initiative berechnen")
        self.calc_button.clicked.connect(self.calculate_initiative)
        layout.addWidget(self.calc_button)

        # Button-Leiste unten
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK (Initiative übernehmen)")
        self.ok_button.setEnabled(False)  # wird erst aktiv nach Berechnung
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)


        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        layout.addStretch()

    def calculate_initiative(self):
        # 1. Alle Würfe auslesen
        results = []
        for actor in self.battle_actors:
            inst_id = actor["instance_id"]
            roll_txt = self.inputs[inst_id]["roll"].text().strip()
            bonus_txt = self.inputs[inst_id]["bonus"].text().strip()

            try:
                roll_val = int(roll_txt)
            except ValueError:
                QMessageBox.warning(self, "Fehler", f"Ungültiger Wurfwert für {actor['display_name']}")
                return

            # 0 = 10 interpretieren
            if roll_val == 0:
                roll_val = 10

            try:
                bonus_val = int(bonus_txt) if bonus_txt else 0
            except ValueError:
                QMessageBox.warning(self, "Fehler", f"Ungültiger Bonus/Malus bei {actor['display_name']}")
                return

            # Handeln-Wert aus Charakterdaten
            handeln_value = self.get_handeln_value(actor["source_char_id"])

            total_initiative = roll_val + handeln_value + bonus_val

            results.append({
                "actor": actor,
                "roll": roll_val,
                "bonus": bonus_val,
                "handeln": handeln_value,
                "total": total_initiative
            })

        # 2. Sortierung:
        #   - Zuerst nach total (desc)
        #   - Bei Gleichstand: PC vor NPC
        #   - Dann alphabetisch als Fallback
        def sort_key(x):
            role = self.get_character_role(x["actor"]["source_char_id"])
            return (
                -x["total"],             # absteigend
                0 if role == "pc" else 1, # pc zuerst
                x["actor"]["display_name"].lower()
            )

        results.sort(key=sort_key)

        # 3. Ergebnis anzeigen
        text = "<b>Initiative-Reihenfolge:</b><br><br>"
        for idx, r in enumerate(results, start=1):
            role = self.get_character_role(r["actor"]["source_char_id"])
            role_display = "PC" if role == "pc" else "NSC"
            text += (
                f"{idx}. {r['actor']['display_name']} "
                f"({role_display}) → Wurf {r['roll']} + Handeln {r['handeln']} "
                f"+ Bonus {r['bonus']} = <b>{r['total']}</b><br>"
            )

        # Überraschungsinfo hinzufügen (falls vorhanden)
        if getattr(self.parent(), "surprised_ids", set()):
            surprised_names = [
                r["actor"]["display_name"]
                for r in results
                if r["actor"]["instance_id"] in self.parent().surprised_ids
            ]
            if surprised_names:
                text += (
                    "<br><b>Überrascht (setzen in Runde 1 aus):</b><br>"
                    + ", ".join(surprised_names)
                    + "<br>"
                )


        self.result_area.setHtml(text)
        # Speichere Reihenfolge für Rückgabe
        self.sorted_results = results
        self.ok_button.setEnabled(True)


    def get_sorted_initiative(self):
        """Gibt die berechnete Reihenfolge zurück"""
        if hasattr(self, "sorted_results"):
            return self.sorted_results
        return []


    def get_handeln_value(self, char_id):
        """Lädt den Charakter und berechnet den aktuellen Handeln-Wert"""
        char_file = None
        folder = "characters"
        if not os.path.exists(folder):
            return 0
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        char_file = data
                        break
            except Exception:
                continue

        if not char_file:
            return 0

        # Berechne Handeln-Wert wie im Charakterdialog
        skills = char_file.get("skills", {})
        handeln_skills = skills.get("Handeln", {})
        if not handeln_skills:
            return 0

        total = sum(int(v) for v in handeln_skills.values() if str(v).isdigit())
        return kaufmaennisch_runden(total / 10)

    def get_character_role(self, char_id):
        """Liest aus dem gespeicherten Charakter, ob es ein PC oder NSC ist"""
        folder = "characters"
        if not os.path.exists(folder):
            return "npc"
        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        return data.get("role", "npc")
            except Exception:
                continue
        return "npc"

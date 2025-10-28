# benötigte Imports
import os
import json
import uuid
## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

## eigene Klassen
from classes.ui.surprise_dialog import SurpriseDialog
from classes.ui.initiative_dialog import InitiativeDialog

class CombatDialog(QDialog):
    def __init__(self, parent=None):
        self.surprised_ids = set()
        super().__init__(parent)

        self.setWindowTitle("Kampf-Übersicht")
        self.setGeometry(200, 200, 600, 500)

        # --- State ---
        # Liste aller aktiven Kämpfer im aktuellen Kampf
        # each: { "instance_id", "source_char_id", "display_name", "team", "current_hp", "max_hp" }
        self.battle_actors = []

        # Teams verwalten
        self.teams = ["Team A", "Team B"]

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Team-Auswahl
        self.team_select = QComboBox()
        self.team_select.addItems(self.teams)
        self.add_team_button = QPushButton("+ Team hinzufügen")
        self.add_team_button.clicked.connect(self.add_new_team)

        left_layout.addWidget(QLabel("Neuen Kämpfer hinzufügen:"))
        left_layout.addWidget(QLabel("Team:"))
        left_layout.addWidget(self.team_select)
        left_layout.addWidget(self.add_team_button)

        # Buttons: PC / NSC hinzufügen
        self.add_pc_button = QPushButton("Spielercharakter hinzufügen")
        self.add_pc_button.clicked.connect(lambda: self.add_combatant(from_role="pc"))
        left_layout.addWidget(self.add_pc_button)

        self.add_npc_button = QPushButton("NSC hinzufügen")
        self.add_npc_button.clicked.connect(lambda: self.add_combatant(from_role="npc"))
        left_layout.addWidget(self.add_npc_button)

        left_layout.addStretch()

        # Rechts: aktuelle Kampfteilnehmer
        right_layout.addWidget(QLabel("Teilnehmer im Kampf:"))
        self.actors_layout = QVBoxLayout()
        right_layout.addLayout(self.actors_layout)
        right_layout.addStretch()

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.start_battle_button = QPushButton("Kampf starten (Initiative bestimmen)")
        self.set_surprise_button = QPushButton("Überraschungsrunde festlegen")
        self.set_surprise_button.clicked.connect(self.set_surprise_round)
        right_layout.addWidget(self.set_surprise_button)
        self.start_battle_button.clicked.connect(self.start_battle)
        right_layout.addWidget(self.start_battle_button)

    def load_character_data(self, char_id):
        """Hilfsfunktion: Lädt Charakterdaten aus ./characters anhand der ID."""
        folder = "characters"
        if not os.path.exists(folder):
            return None

        for fname in os.listdir(folder):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join(folder, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        return data
            except Exception:
                continue

        return None

    def set_surprise_round(self):
        """Öffnet den Dialog, um überrascht markierte Kämpfer zu wählen"""
        if not self.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = SurpriseDialog(self.battle_actors, self)
        if dlg.exec():
            self.surprised_ids = dlg.get_surprised_ids()
            if self.surprised_ids:
                names = [
                    a["display_name"]
                    for a in self.battle_actors
                    if a["instance_id"] in self.surprised_ids
                ]
                msg = "<br>".join(names)
                QMessageBox.information(
                    self, "Überraschungsrunde",
                    f"Folgende Kämpfer sind überrascht:<br><br>{msg}"
                )
            else:
                QMessageBox.information(self, "Überraschungsrunde", "Niemand ist überrascht.")

    def start_battle(self):
        if not self.battle_actors:
            QMessageBox.information(self, "Hinweis", "Keine Kämpfer im Kampf.")
            return

        dlg = InitiativeDialog(self.battle_actors, self, surprised_ids=self.surprised_ids)
        if dlg.exec():
            order = dlg.get_sorted_initiative()
            if order:
                self.set_initiative_order(order)

    def set_initiative_order(self, order):
        """Speichert die Reihenfolge und zeigt sie im CombatDialog an"""
        self.surprised_ids = getattr(self, "surprised_ids", set())
        self.turn_order = [r["actor"] for r in order]
        self.current_turn_index = 0
        self.parry_used = {}
        self.round_damage = {}  # Gesamtschaden pro Charakter in der aktuellen Runde {instance_id: damage}
        self.round_number = 1 
        # Falls noch kein UI-Bereich existiert, erstellen wir ihn
        if not hasattr(self, "turn_area"):
            self.turn_area = QVBoxLayout()

            self.current_turn_label = QLabel()
            self.turn_area.addWidget(self.current_turn_label)

            self.order_list_widget = QTextEdit()
            self.order_list_widget.setReadOnly(True)
            self.turn_area.addWidget(self.order_list_widget)

            # Buttons
            btns = QHBoxLayout()
            self.next_turn_btn = QPushButton("▶️ Nächster Zug")
            self.next_turn_btn.clicked.connect(self.next_turn)
            btns.addWidget(self.next_turn_btn)

            self.reset_round_btn = QPushButton("🔁 Neue Runde")
            self.reset_round_btn.clicked.connect(self.reset_round)
            btns.addWidget(self.reset_round_btn)

            self.action_btn = QPushButton("⚔️ Zug ausführen")
            self.action_btn.clicked.connect(self.run_current_turn)
            btns.addWidget(self.action_btn)

            self.turn_area.addLayout(btns)

            # Füge das unten an (z. B. unter den Teilnehmern)
            self.layout().addLayout(self.turn_area)

        # Kampf-Log (Nachrichtenfeld)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Kampf-Log...")
        self.layout().addWidget(self.log_box)
        self.refresh_turn_display()

    def run_current_turn(self):
        """Führt den Zug des aktuell an der Reihe befindlichen Kämpfers aus."""
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        current_actor = self.turn_order[self.current_turn_index]

        # --- Tot / Bewusstlosigkeit prüfen und überspringen ---
        if current_actor.get("dead", False):
            self.log_message(f"💀 {current_actor['display_name']} ist tot und wird übersprungen.")
            self.current_turn_index += 1
            if self.current_turn_index >= len(self.turn_order):
                self.next_turn()
            else:
                self.refresh_turn_display()
            return
        elif current_actor.get("unconscious", False):
            self.log_message(f"⭕ {current_actor['display_name']} ist bewusstlos und setzt in dieser Runde aus.")
            self.current_turn_index += 1
            if self.current_turn_index >= len(self.turn_order):
                self.next_turn()
            else:
                self.refresh_turn_display()
            return  # Wichtig: Zug sofort beenden
        # --- Ende Bewusstlos-Check ---

        # Den eigentlichen Zug durchführen (inkl. Überraschungs-Check)
        self.execute_turn(current_actor)

    def append_battle_log(self, message: str):
        """Schreibt eine Nachricht in das Kampf-Log-Feld."""
        if not hasattr(self, "log_box"):
            return  # falls das Log-Feld noch nicht existiert (z. B. beim Start)
        self.log_box.append(message)


    def log_message(self, text):
        """Fügt eine Nachricht in das Kampf-Log ein."""
        self.log_box.append(f"• {text}")

    def execute_turn(self, actor):
        # 1. Check: ist der Actor in Runde 1 überrascht?
        if self.is_actor_surprised_and_blocked(actor):
            self.log_message(
                f"{actor['display_name']} ist überrascht und setzt in Runde {self.round_number} aus."
            )
            return

        current_actor = self.turn_order[self.current_turn_index]
        actor_name = current_actor["display_name"]

        # Ziel wählen
        targets = [a for a in self.battle_actors if a["instance_id"] != current_actor["instance_id"]]
        if not targets:
            QMessageBox.information(self, "Hinweis", "Keine Ziele verfügbar.")
            return

        target_names = [t["display_name"] for t in targets]
        target_choice, ok = QInputDialog.getItem(self, "Ziel wählen", f"{actor_name} greift an:", target_names, 0, False)
        if not ok:
            return

        target = next(t for t in targets if t["display_name"] == target_choice)

        # Fertigkeit / Kategorie wählen
        attack_skill = self.select_skill_dialog(current_actor)
        if not attack_skill:
            return

        # Angriffswurf
        self.log_message(f"{actor_name} greift {target['display_name']} mit {attack_skill} an...")
        success, crit = self.perform_roll(current_actor, attack_skill)

         # Erfolg
        if success: 
            result_text = "💥Treffer!" if not crit else "⚡💥 Kritischer Treffer!"
            self.log_message(f"➡️ {result_text}")
        else:
            result_text = "🍃Fehlschlag!" if not crit else "⚡🍃 Kritischer Fehlschlag!"
            self.log_message(f"➡️ {result_text}")

        # Bei kritischem Treffer: keine Parade möglich → direkt Schaden
        if success and crit:
            self.log_message(f"⚠️ {target['display_name']} kann den Angriff aufgrund eines kritischen Erfolgs nicht parieren!")
            self.calculate_damage(current_actor, target)
            return

        if success and not crit:
            # Normale Treffer: Ziel kann parieren
            # --- Einmal pro Runde Parry-Check ---
            target_id = target["instance_id"]
            if self.parry_used.get(target_id, False):
                self.log_message(f"⚠️ {target['display_name']} hat in dieser Runde bereits pariert und kann nicht erneut parieren.")
                self.calculate_damage(current_actor, target)
                return

        if success:
            parry_choice = QMessageBox.question(
                self,
                "Parade?",
                f"{target['display_name']} wurde getroffen. Möchte er/sie parieren?\n(Hinweis: Nur 1x pro Runde möglich)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if parry_choice == QMessageBox.StandardButton.No:
                self.log_message(f"{target['display_name']} entscheidet sich, nicht zu parieren.")
                self.calculate_damage(current_actor, target)
                return

            # Markiere: hat pariert
            self.parry_used[target_id] = True

            if parry_choice == QMessageBox.StandardButton.No:
                self.log_message(f"{target['display_name']} entscheidet sich, nicht zu parieren.")
                self.calculate_damage(current_actor, target)
                return

            # Ziel versucht zu parieren
            self.log_message(f"{target['display_name']} versucht, den Angriff zu parieren...")
            parry_skill = self.select_skill_dialog(target)
            if not parry_skill:
                return

            parry_success, parry_crit = self.perform_roll(target, parry_skill)

            if parry_success:
                text = "Parade gelungen!" if not parry_crit else "💥 Kritische Parade!"
                self.log_message(f"🛡️ {text}")
            else:
                text = "Parade misslungen." if not parry_crit else "😬 Kritischer Fehlschlag bei der Parade!"
                self.log_message(f"❌ {text}")
                self.calculate_damage(current_actor, target)  # Schaden bei misslungener Parade

    def calculate_damage(self, attacker, target):
        """Berechnet Schaden nach einem erfolgreichen Treffer."""
        attacker_name = attacker["display_name"]
        target_name = target["display_name"]

        char_data = self.load_character_data(attacker["source_char_id"])
        base_damage = char_data.get("base_damage", "1W6")

        # Waffen im Inventar mit is_weapon=True
        weapons = []
        items_dict = char_data.get("items", {})
        for iname, item_data in items_dict.items():
            if isinstance(item_data, dict) and item_data.get("is_weapon"):
                formula = item_data.get("damage_formula", "")
                weapons.append((iname, formula))

        # Auswahlmöglichkeiten
        options = [f"Basis-Schaden ({base_damage})"] + [
            f"{iname} ({formel})" for iname, formel in weapons
        ]

        # Waffe oder Basis-Schaden auswählen
        weapon_choice, ok = QInputDialog.getItem(
            self, "Waffe wählen", f"Womit greift {attacker_name} an?", options, 0, False
        )
        if not ok:
            self.log_message(f"{attacker_name} bricht den Angriff ab.")
            return

        # Schadensformel bestimmen
        if weapon_choice.startswith("Basis-Schaden"):
            damage_formula = base_damage
            weapon_name = "Basis-Schaden"
        else:
            weapon_name = weapon_choice.split(" (")[0]
            damage_formula = dict(weapons).get(weapon_name, base_damage)

        # Würfelwurf eingeben
        roll_txt, ok = QInputDialog.getText(self, "Schadenswurf", f"Was wurde für {damage_formula} gewürfelt?")
        if not ok:
            return

        try:
            rolled_val = int(roll_txt.strip())
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Ungültige Eingabe für Wurf.")
            return

        # Optionaler Bonus/Malus
        bonus_txt, ok = QInputDialog.getText(
            self, "Bonus/Malus", "Bonus oder Malus auf den Schaden? (z. B. +3 oder -2)"
        )
        if not ok:
            bonus_txt = "0"
        try:
            bonus_val = int(bonus_txt.strip())
        except ValueError:
            bonus_val = 0

        # Fixer Bonus aus Formel extrahieren, z. B. 2W10+5
        fixed_bonus = 0
        if "+" in damage_formula:
            try:
                bonus_part = damage_formula.split("+")[1].strip()
                # Nur die Zahl vor einem möglichen Leerzeichen oder Buchstaben nehmen
                fixed_bonus = int(''.join(filter(str.isdigit, bonus_part.split()[0])))
            except (ValueError, IndexError):
                self.log_message(f"Warnung: Ungültiger Bonus in Schadensformel '{damage_formula}' – wird ignoriert.")
                fixed_bonus = 0

        total_damage = rolled_val + fixed_bonus + bonus_val

        # Schaden anwenden
        target["current_hp"] = max(0, target["current_hp"] - total_damage)
        # --- Bewusstlosigkeits-Prüfung ---
        target_id = target["instance_id"]

        # 1. Runden-Schaden tracken
        if target_id not in self.round_damage:
            self.round_damage[target_id] = 0
        self.round_damage[target_id] += total_damage

        # 2. Bewusstlos, wenn HP < 10 ODER Runden-Schaden > 60
        if (0 < target["current_hp"] < 10) or (self.round_damage[target_id] > 60):
            target["unconscious"] = True
            self.log_message(
                f"⚠️ {target_name} ist bewusstlos! "
                f"(HP: {target['current_hp']}, Runden-Schaden: {self.round_damage[target_id]})"
            )

        # Neu: Tot-Prüfung (nach Bewusstlos, falls HP <= 0)
        if target["current_hp"] <= 0:
            target["dead"] = True
            target["unconscious"] = True  # Tot impliziert auch bewusstlos
            self.log_message(f"💀 {target_name} ist tot! (HP: {target['current_hp']})")

        self.refresh_actor_list()

        # Log-Eintrag
        self.log_message(
            f"{attacker_name} verursacht {total_damage} Schaden an {target_name} "
            f"({weapon_name}, {damage_formula}, Wurf: {rolled_val}, Bonus: {bonus_val}). "
            f"{target_name} hat jetzt {target['current_hp']} / {target['max_hp']} HP."
        )


    def select_skill_dialog(self, actor):
        # Lade Charakterdaten
        char = self.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self, "Fehler", "Charakterdaten konnten nicht geladen werden.")
            return None

        # Fertigkeiten und Kategorien zusammenstellen
        skill_names = []
        for cat, skills in char.get("skills", {}).items():
            skill_names.append(cat)  # Kategorie selbst
            skill_names.extend(skills.keys())

        choice, ok = QInputDialog.getItem(self, "Fertigkeit wählen", "Angriffs-Fertigkeit:", skill_names, 0, False)
        return choice if ok else None

    def perform_roll(self, actor, skill_name):
        """Führt eine manuelle Würfelprobe durch, die der Spielleiter eingibt."""
        char = self.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self, "Fehler", f"Konnte Charakterdaten für {actor['display_name']} nicht laden.")
            return False, False

        char.setdefault("skills", {})
        char.setdefault("category_scores", {})

        skills = char["skills"]

        # Prüfen, ob direkt auf eine Kategorie (z. B. "Handeln") gewürfelt wird
        if skill_name in char["category_scores"]:
            category = skill_name
            skill_val = 0
            category_val = char["category_scores"].get(category, 0)
        else:
            # Kategorie anhand der Fertigkeiten suchen
            category = None
            for cat, skillset in skills.items():
                if skill_name in skillset:
                    category = cat
                    break

            if category is None:
                QMessageBox.warning(self, "Fehler", f"Fertigkeit oder Kategorie '{skill_name}' nicht im Charakter gefunden.")
                return False, False

            skill_val = skills[category].get(skill_name, 0)
            category_val = char["category_scores"].get(category, 0)

        base_val = skill_val + category_val

        # 🎲 Spielleiter gibt realen Wurf ein
        roll_str, ok = QInputDialog.getText(
            self,
            f"Wurf für {actor['display_name']}",
            f"Bitte gewürfelten Wurf (1–100) für {skill_name} ({category}) eingeben:"
        )
        if not ok:
            return False, False

        try:
            roll = int(roll_str)
            if roll == 0:
                roll = 100
            if not 1 <= roll <= 100:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Ungültiger Wurfwert. Bitte 1–100 eingeben (0 = 100).")
            return False, False

        # Erfolg / Kritisch prüfen
        crit = roll in (1, 100)
        success = roll <= base_val

        # Log-Eintrag
        if hasattr(self, "log_message"):
            if skill_val > 0:
                details = f"Wurf auf {skill_name} ({category})"
            else:
                details = f"Wurf auf Kategorie {category}"
            self.log_message(
                f"{actor['display_name']} {details}: "
                f"Wurf={roll}, Zielwert={base_val} → {'✔️ Erfolg' if success else '❌ Fehlschlag'}"
                + (" (Kritisch!)" if crit else "")
            )

        return success, crit




    def handle_parry_phase(self, attacker, target):
        """Ermöglicht dem Ziel, einen Blockversuch zu starten."""
        # Paradezähler initialisieren
        if not hasattr(self, "parry_used"):
            self.parry_used = {}

        target_id = target["instance_id"]
        if self.parry_used.get(target_id, False):
            self.log_message(f"{target['display_name']} hat in dieser Runde bereits pariert.")
            return

        reply = QMessageBox.question(
            self, "Parade?", f"Soll {target['display_name']} den Angriff parieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            self.log_message(f"{target['display_name']} versucht nicht zu parieren.")
            return

        # Parier-Fertigkeit wählen
        parry_skill = self.select_skill_dialog(target)
        if not parry_skill:
            return

        success, crit = self.perform_roll(target, parry_skill)
        self.parry_used[target_id] = True

        if success:
            self.log_message(f"🛡️ {target['display_name']} pariert erfolgreich mit {parry_skill}!")
        else:
            self.log_message(f"💥 {target['display_name']} verfehlt die Parade!")


    def refresh_turn_display(self):
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        current_actor = self.turn_order[self.current_turn_index]

        # Kopfzeile mit Rundeninfo
        self.current_turn_label.setText(
            f"<b>Runde {self.round_number}</b><br>"
            f"<b>Aktuell am Zug:</b> {current_actor['display_name']} ({current_actor['team']})"
        )

        # gesamte Reihenfolge anzeigen
        text = ""
        for i, actor in enumerate(self.turn_order, start=1):
            # --- Status bestimmen (Hierarchie: Tot > Bewusstlos > Überrascht) ---
            status_icon = ""
            status_style = ""
            skip_note = ""

            if actor.get("dead", False):
                status_icon = " [TOT]"
                status_style = 'style="color:red; font-weight:bold;"'
            elif actor.get("unconscious", False):
                status_icon = " [BEWUSSTLOS]"
                status_style = 'style="color:orange; font-style:italic;"'
                skip_note = " (setzt aus)" if not actor.get("dead", False) else ""
            elif actor["instance_id"] in getattr(self, "surprised_ids", set()):
                status_icon = " [ÜBERRASCHT]"
                status_style = 'style="color:gray; font-style:italic;"'
                skip_note = " (setzt in Runde 1 aus)" if self.round_number == 1 else ""
            else:
                status_style = ""

            # Aktueller Zug fett
            prefix = " " if i - 1 == self.current_turn_index else ""

            text += (
                f'{prefix}{i}. '
                f'<span {status_style}>{actor["display_name"]}{status_icon} ({actor["team"]}){skip_note}</span><br>'
            )

        self.order_list_widget.setHtml(text)


    def next_turn(self):
        if not hasattr(self, "turn_order") or not self.turn_order:
            return

        # Endlosschutz – z. B. wenn alle in Runde 1 überrascht wären
        max_iterations = len(self.turn_order) * 2

        while max_iterations > 0:
            max_iterations -= 1

            self.current_turn_index += 1
            if self.current_turn_index >= len(self.turn_order):
                # Neue Runde starten
                self.round_number += 1
                self.current_turn_index = 0
                QMessageBox.information(self, "Neue Runde", f"Runde {self.round_number} beginnt!")

            current_actor = self.turn_order[self.current_turn_index]

            # Überraschungsregel: In Runde 1 dürfen überraschte Kämpfer nicht handeln
            if hasattr(self.parent(), "surprised_ids") and self.round_number == 1:
                if current_actor["instance_id"] in self.parent().surprised_ids:
                    # Überspringen, Info ins Log
                    print(f"Übersprungen (überrascht): {current_actor['display_name']}")
                    continue  # direkt nächsten Kämpfer prüfen

            # Wenn kein Überspringen → regulärer Zug
            break

        self.refresh_turn_display()

    def reset_round(self):
        # WICHTIG: Parry-Tracking pro Runde zurücksetzen
        self.parry_used = {}
        self.round_damage = {}  # Gesamtschaden pro Charakter in der aktuellen Runde {instance_id: damage}
        if not hasattr(self, "turn_order") or not self.turn_order:
            return
        self.current_turn_index = 0
        QMessageBox.information(self, "Runde zurückgesetzt", "Die Initiative startet wieder bei Runde 1.")
        self.refresh_turn_display()


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
            self.battle_actors.append(actor)

        # UI neu aufbauen
        self.refresh_actor_list()

    def load_characters_by_role(self, role_filter):
        """
        role_filter ist "pc" oder "npc".
        Wir durchsuchen ./characters und lesen jeden JSON.
        Gibt Liste aus Dicts zurück:
        { "display": "...", "path": "...", "data": {...} }
        """
        results = []
        if not os.path.exists("characters"):
            return results

        for fname in os.listdir("characters"):
            if not fname.lower().endswith(".json"):
                continue
            full_path = os.path.join("characters", fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("role", "pc") != role_filter:
                continue

            char_name = data.get("name", "(unbenannt)")
            char_class = data.get("class", "?")
            char_hp = data.get("hitpoints", "?")
            display = f"{char_name} [{char_class}] HP:{char_hp}"

            results.append({
                "display": display,
                "path": full_path,
                "data": data,
            })

        return results

    def refresh_actor_list(self):
        # Erstmal alles leerräumen
        while self.actors_layout.count():
            item = self.actors_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Für jede Instanz einen kleinen Block bauen
        for actor in self.battle_actors:
            box = QGroupBox(f"{actor['display_name']} ({actor['team']})")
            box.setStyleSheet("QGroupBox { font-weight:bold; }")
            v = QVBoxLayout()

            hp_label = QLabel(f"HP: {actor['current_hp']}/{actor['max_hp']}")
            v.addWidget(hp_label)

            # Buttons für HP +/- und Entfernen
            btn_row = QHBoxLayout()

            minus_btn = QPushButton("-1 HP")
            plus_btn = QPushButton("+1 HP")
            remove_btn = QPushButton("Entfernen")

            def make_minus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = max(0, a["current_hp"] - 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_plus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = min(a["max_hp"], a["current_hp"] + 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_remove(a=actor):
                def _inner():
                    self.battle_actors = [x for x in self.battle_actors if x["instance_id"] != a["instance_id"]]
                    self.refresh_actor_list()
                return _inner

            minus_btn.clicked.connect(make_minus())
            plus_btn.clicked.connect(make_plus())
            remove_btn.clicked.connect(make_remove())

            btn_row.addWidget(minus_btn)
            btn_row.addWidget(plus_btn)
            btn_row.addWidget(remove_btn)

            v.addLayout(btn_row)
            box.setLayout(v)
            self.actors_layout.addWidget(box)

    def is_actor_surprised_and_blocked(self, actor):
        """
        True genau dann, wenn dieser Actor in DIESER Runde nicht handeln darf.
        Regel: Runde 1 + Actor ist überrascht -> blockieren.
        Ab Runde 2 nie blockieren.
        """
        return (
            self.round_number == 1
            and actor["instance_id"] in self.surprised_ids
        )

from PyQt6.QtWidgets import QMessageBox, QInputDialog

class CombatActionHandler:
    def __init__(self, main_dialog):
        self.main_dialog = main_dialog

    def log_message(self, text: str):
        if hasattr(self.main_dialog, "log_widget"):
            self.main_dialog.log_widget.log_message(text)
        elif hasattr(self.main_dialog, "log_box"):
            self.main_dialog.log_box.append(f"• {text}") # Fallback

    def run_current_turn(self):
        """Führt den Zug des aktuell an der Reihe befindlichen Kämpfers aus."""
        manager = self.main_dialog.combat_manager
        actor = manager.get_current_actor()
        if not actor:
            return

        skipped, reason = manager.check_and_skip_if_incapacitated()
        if skipped:
            self.log_message(reason)
            # Advance to next natively via the UI button handler or directly:
            if hasattr(self.main_dialog, "turn_widget"):
                self.main_dialog.turn_widget.next_turn()
            elif hasattr(self.main_dialog, "next_turn"):
                self.main_dialog.next_turn()
            return

        self.execute_turn(actor)

    def execute_turn(self, actor):
        manager = self.main_dialog.combat_manager
        skipped, reason = manager.check_and_skip_if_incapacitated()
        if skipped:
            self.log_message(reason)
            return

        actor_name = actor["display_name"]

        targets = [a for a in manager.battle_actors if a["instance_id"] != actor["instance_id"]]
        if not targets:
            QMessageBox.information(self.main_dialog, "Hinweis", "Keine Ziele verfügbar.")
            return

        target_names = [t["display_name"] for t in targets]
        target_choice, ok = QInputDialog.getItem(self.main_dialog, "Ziel wählen", f"{actor_name} greift an:", target_names, 0, False)
        if not ok:
            return

        target = next(t for t in targets if t["display_name"] == target_choice)

        attack_skill = self.select_skill_dialog(actor)
        if not attack_skill:
            return

        self.log_message(f"{actor_name} greift {target['display_name']} mit {attack_skill} an...")
        success, crit = self.perform_roll(actor, attack_skill)

        if success: 
            result_text = "💥Treffer!" if not crit else "⚡💥 Kritischer Treffer!"
            self.log_message(f"➡️ {result_text}")
        else:
            result_text = "🍃Fehlschlag!" if not crit else "⚡🍃 Kritischer Fehlschlag!"
            self.log_message(f"➡️ {result_text}")

        if success and crit:
            self.log_message(f"⚠️ {target['display_name']} kann den Angriff aufgrund eines kritischen Erfolgs nicht parieren!")
            self.calculate_damage(actor, target)
            return

        if success and not crit:
            target_id = target["instance_id"]
            if not manager.can_actor_parry(target_id):
                self.log_message(f"⚠️ {target['display_name']} hat in dieser Runde bereits pariert und kann nicht erneut parieren.")
                self.calculate_damage(actor, target)
                return

        if success:
            parry_choice = QMessageBox.question(
                self.main_dialog,
                "Parade?",
                f"{target['display_name']} wurde getroffen. Möchte er/sie parieren?\n(Hinweis: Nur 1x pro Runde möglich)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if parry_choice == QMessageBox.StandardButton.No:
                self.log_message(f"{target['display_name']} entscheidet sich, nicht zu parieren.")
                self.calculate_damage(actor, target)
                return

            manager.mark_parry_used(target_id)
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
                self.calculate_damage(actor, target)


    def calculate_damage(self, attacker, target):
        attacker_name = attacker["display_name"]
        target_name = target["display_name"]

        # Access DataManager via main_dialog's helper if needed, or directly
        char_data = self.main_dialog.load_character_data(attacker["source_char_id"])
        base_damage = char_data.get("base_damage", "1W6")

        weapons = []
        items_dict = char_data.get("items", {})
        for iname, item_data in items_dict.items():
            if isinstance(item_data, dict) and item_data.get("is_weapon"):
                formula = item_data.get("damage_formula", "")
                weapons.append((iname, formula))

        options = [f"Basis-Schaden ({base_damage})"] + [
            f"{iname} ({formel})" for iname, formel in weapons
        ]

        weapon_choice, ok = QInputDialog.getItem(
            self.main_dialog, "Waffe wählen", f"Womit greift {attacker_name} an?", options, 0, False
        )
        if not ok:
            self.log_message(f"{attacker_name} bricht den Angriff ab.")
            return

        if weapon_choice.startswith("Basis-Schaden"):
            damage_formula = base_damage
            weapon_name = "Basis-Schaden"
        else:
            weapon_name = weapon_choice.split(" (")[0]
            damage_formula = dict(weapons).get(weapon_name, base_damage)

        roll_txt, ok = QInputDialog.getText(self.main_dialog, "Schadenswurf", f"Was wurde für {damage_formula} gewürfelt?")
        if not ok:
            return

        try:
            rolled_val = int(roll_txt.strip())
        except ValueError:
            QMessageBox.warning(self.main_dialog, "Fehler", "Ungültige Eingabe für Wurf.")
            return

        bonus_txt, ok = QInputDialog.getText(
            self.main_dialog, "Bonus/Malus", "Bonus oder Malus auf den Schaden? (z. B. +3 oder -2)"
        )
        if not ok:
            bonus_txt = "0"
        try:
            bonus_val = int(bonus_txt.strip())
        except ValueError:
            bonus_val = 0

        fixed_bonus = 0
        if "+" in damage_formula:
            try:
                bonus_part = damage_formula.split("+")[1].strip()
                fixed_bonus = int(''.join(filter(str.isdigit, bonus_part.split()[0])))
            except (ValueError, IndexError):
                self.log_message(f"Warnung: Ungültiger Bonus in Schadensformel '{damage_formula}' – wird ignoriert.")
                fixed_bonus = 0

        total_damage = rolled_val + fixed_bonus + bonus_val

        target, logs = self.main_dialog.combat_manager.apply_damage_and_check_status(target["instance_id"], total_damage)
        if not target:
            self.log_message("Fehler: Ziel konnte nicht für Schaden gefunden werden.")
            return

        for log_msg in logs:
            self.log_message(log_msg)

        if hasattr(self.main_dialog, "actor_list_widget"):
             self.main_dialog.actor_list_widget.refresh_actor_list()
        elif hasattr(self.main_dialog, "refresh_actor_list"):
             self.main_dialog.refresh_actor_list()

        self.log_message(
            f"{attacker_name} verursacht {total_damage} Schaden an {target_name} "
            f"({weapon_name}, {damage_formula}, Wurf: {rolled_val}, Bonus: {bonus_val}). "
            f"{target_name} hat jetzt {target['current_hp']} / {target['max_hp']} HP."
        )

    def select_skill_dialog(self, actor):
        char = self.main_dialog.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self.main_dialog, "Fehler", "Charakterdaten konnten nicht geladen werden.")
            return None

        skill_names = []
        for cat, skills in char.get("skills", {}).items():
            skill_names.append(cat)
            skill_names.extend(skills.keys())

        choice, ok = QInputDialog.getItem(self.main_dialog, "Fertigkeit wählen", "Angriffs-Fertigkeit:", skill_names, 0, False)
        return choice if ok else None

    def perform_roll(self, actor, skill_name):
        char = self.main_dialog.load_character_data(actor["source_char_id"])
        if not char:
            QMessageBox.warning(self.main_dialog, "Fehler", f"Konnte Charakterdaten für {actor['display_name']} nicht laden.")
            return False, False

        char.setdefault("skills", {})
        char.setdefault("category_scores", {})
        skills = char["skills"]

        if skill_name in char["category_scores"]:
            category = skill_name
            skill_val = 0
            category_val = char["category_scores"].get(category, 0)
        else:
            category = None
            for cat, skillset in skills.items():
                if skill_name in skillset:
                    category = cat
                    break

            if category is None:
                QMessageBox.warning(self.main_dialog, "Fehler", f"Fertigkeit oder Kategorie '{skill_name}' nicht im Charakter gefunden.")
                return False, False

            skill_val = skills[category].get(skill_name, 0)
            category_val = char["category_scores"].get(category, 0)

        base_val = skill_val + category_val

        roll_str, ok = QInputDialog.getText(
            self.main_dialog,
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
            QMessageBox.warning(self.main_dialog, "Fehler", "Ungültiger Wurfwert. Bitte 1–100 eingeben (0 = 100).")
            return False, False

        crit = roll in (1, 100)
        success = roll <= base_val

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

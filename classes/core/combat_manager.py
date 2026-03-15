from typing import List, Dict, Optional, Tuple

class CombatManager:
    """
    Verwaltet die Logik und den Zustand eines Kampfes.
    Trennt Datenhaltung und Regeln von der Benutzeroberfläche (PyQt).
    """

    def __init__(self):
        # Aktive Kämpfer (Spieler und NSCs)
        # Struktur jedes Kämpfers (wie bisher im UI):
        # { "instance_id", "source_char_id", "display_name", "team", "current_hp", "max_hp", "unconscious", "dead" }
        self.battle_actors: List[Dict] = []
        
        # Initiative-Reihenfolge (Referenzen auf Dicts in battle_actors)
        self.turn_order: List[Dict] = []
        
        # State
        self.round_number: int = 1
        self.current_turn_index: int = 0
        
        # Trackt den in dieser Runde erlittenen Schaden pro instance_id
        # Resets auf {} beim Rundenwechsel
        self.round_damage: Dict[str, int] = {}
        
        # Trackt, wer in dieser Runde bereits pariert hat
        # Resets auf {} beim Rundenwechsel
        self.parry_used: Dict[str, bool] = {}

        # Trackt, wer an der Überraschungsrunde (Runde 1) nicht teilnehmen darf
        self.surprised_ids: set = set()

    # ==========================
    # Initialization / Setup
    # ==========================
    def add_combatant(self, actor: Dict):
        """Fügt einen Kämpfer zur aktuellen Schlacht hinzu."""
        self.battle_actors.append(actor)

    def remove_combatant(self, instance_id: str):
        """Entfernt einen Kämpfer komplett aus der Schlacht (z.B. UI-Löschung)."""
        self.battle_actors = [a for a in self.battle_actors if a["instance_id"] != instance_id]

    def set_initiative_order(self, order: List[Dict], surprised_ids: set):
        """
        Startet den eigentlichen Kampf.
        - order ist eine sortierte Liste aller teilnehmenden Kämpfer.
        - surprised_ids ist ein Set aus instance_ids, die überrascht sind.
        """
        self.turn_order = order
        self.surprised_ids = set(surprised_ids)
        self.round_number = 1
        self.current_turn_index = 0
        self.round_damage = {}
        self.parry_used = {}

    # ==========================
    # Turn Flow Management
    # ==========================
    def get_current_actor(self) -> Optional[Dict]:
        """Gibt den Kämpfer zurück, der gerade am Zug ist."""
        if not self.turn_order or self.current_turn_index >= len(self.turn_order):
            return None
        return self.turn_order[self.current_turn_index]

    def is_current_actor_surprised_and_blocked(self) -> bool:
        """Checkt, ob der aktuelle Kämpfer wegen Überraschung am Zug gehindert ist."""
        actor = self.get_current_actor()
        if not actor:
            return False
        return self.round_number == 1 and (actor["instance_id"] in self.surprised_ids)

    def check_and_skip_if_incapacitated(self) -> Tuple[bool, str]:
        """
        Prüft, ob der aktuelle Kämpfer agieren kann.
        Gibt (skipped, log_reason) zurück. Wenn skipped=True, sollte das UI direkt next_turn() aufrufen.
        """
        actor = self.get_current_actor()
        if not actor:
            return True, "Kein Kämpfer am Zug."

        if actor.get("dead", False):
            return True, f"💀 {actor['display_name']} ist tot und wird übersprungen."
        if actor.get("unconscious", False):
            return True, f"⭕ {actor['display_name']} ist bewusstlos und setzt aus."
        
        if self.is_current_actor_surprised_and_blocked():
            return True, f"👀 {actor['display_name']} ist überrascht und setzt in Runde {self.round_number} aus."

        return False, ""

    def next_turn(self) -> bool:
        """
        Geht zum nächsten Kämpfer über.
        Rückgabe: True, wenn eine NEUE Runde begonnen hat; False sonst.
        """
        if not self.turn_order:
            return False

        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_order):
            self._start_new_round()
            return True
        return False

    def _start_new_round(self):
        """Interne Logik für Rundenbeginn."""
        self.round_number += 1
        self.current_turn_index = 0
        self.round_damage = {}
        self.parry_used = {}

    # ==========================
    # Combat Mechanics
    # ==========================
    def can_actor_parry(self, target_id: str) -> bool:
        """Prüft, ob ein Ziel in dieser Runde noch parieren darf."""
        return not self.parry_used.get(target_id, False)

    def mark_parry_used(self, target_id: str):
        """Markiert, dass das Ziel seine Parade für diese Runde verbraucht hat."""
        self.parry_used[target_id] = True

    def apply_damage_and_check_status(self, target_id: str, total_damage: int) -> Tuple[Dict, List[str]]:
        """
        Zieht dem Ziel HP ab und checkt auf Bewusstlosigkeit/Tod.
        Returns:
            - Die Target-Dictionay Referenz
            - Eine Liste von Log-Nachrichten (was passiert ist)
        """
        logs = []
        target = next((a for a in self.battle_actors if a["instance_id"] == target_id), None)
        if not target:
            return None, ["Fehler: Ziel nicht gefunden."]

        target["current_hp"] = max(0, target["current_hp"] - total_damage)
        
        # Runden-Schaden tracken
        if target_id not in self.round_damage:
            self.round_damage[target_id] = 0
        self.round_damage[target_id] += total_damage

        # Check für Bewusstlosigkeit (HP < 10 oder Rundenschaden > 60)
        # und Tod (HP <= 0)
        target_name = target["display_name"]
        
        was_unconscious = target.get("unconscious", False)
        was_dead = target.get("dead", False)

        # Tod (dominiert alles andere)
        if target["current_hp"] <= 0:
            target["dead"] = True
            target["unconscious"] = True
            if not was_dead:
                logs.append(f"💀 {target_name} ist tot! (HP: {target['current_hp']})")
        
        # Bewusstlos (wenn nicht tot)
        elif not target.get("dead"):
            if (target["current_hp"] < 10) or (self.round_damage[target_id] > 60):
                target["unconscious"] = True
                if not was_unconscious:
                    logs.append(
                        f"⚠️ {target_name} ist bewusstlos! "
                        f"(HP: {target['current_hp']}, Runden-Schaden: {self.round_damage[target_id]})"
                    )

        return target, logs

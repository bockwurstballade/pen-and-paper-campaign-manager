from typing import Dict, TypedDict
from typing_extensions import TypedDict  # Falls TypedDict in älteren Python-Versionen benötigt

import logging

# Konfiguration des Loggers (einmalig im Modul oder in der Anwendung)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('DiceRollEvaluator')

## eigene Funktionen
from utils.functions.math import kaufmaennisch_runden

class DiceRollEvaluator:
    """
    Eine Klasse zur Bewertung von Würfelwürfen und Chancenberechnungen.
    Enthält Methoden zur Bestimmung von Erfolg und kritischen Treffern.

    Grundlage ist das Regelwerk: 
    https://howtobeahero.de/index.php/W%C3%BCrfe_%26_Proben_(kritische_Erfolge_%26_Fehlschl%C3%A4ge)/de
    """
    class ChanceResult(TypedDict):
            """
            TypedDict für das Ergebnis der Chancenberechnung.
            Wird als innere Klasse definiert, um enge Kopplung an DiceRollEvaluator zu gewährleisten.
            """
            success: bool # war die würfelprobe an sich erfolgreich oder ein Fehlschlag
            crit: bool # war es ein kritischer Erfolg / Fehlschlag?

    def evaluate_roll(self, input_dict: Dict[str, int]) -> "DiceRollEvaluator.ChanceResult":
        """
        Berechnet Erfolg und kritischen Treffer basierend auf base_chance und rolled.

        Args:
        :param input_dict: Dict mit 'base_chance' (0–500) und 'rolled' (1–100).
            base_chance: 
                Der letztendliche Endwert, der gewürfelt werden muss 
                (also Fertigkeitswert + Kategoriewert + Bonus/Malus durch Effekte und Spielleiter).
                Beispiel: Kämpfen geskillt auf 50, Handeln Wert 10, Bonus 10
                also ist der Endwert für base_chance 70. Man muss 70 oder niedriger würfeln
                um die Würfelprobe zu schaffen. Diesen Wert gibt man an die Funktion.
            rolled:
                Welcher Wert wurde letztendlich gewürfelt.
                In How To Be a Hero gibt es keine 0.
                Wenn man 0 eingibt, wird dies automatisch als 100 gewertet,
                also immer ein kritischer Misserfolg
            bonus (optional):
                Optional kann hier ein Bonus angegeben werden, den der spielleiter vergibt.
                Ein positiver Wert wird als Bonus interpretiert,
                ein negativer Wert als Malus.
                In den meisten fällen kann man einfach im Voraus
                eventuelle Boni und Mali verrechnen und direkt
                den korrekten Endwert als base_chance übergeben.
                Die Angabe eines bonus ist also optional.
        :return: ChanceResult mit 'success' und 'crit'.
            success:
                war die Würfelprobe an sich erfolgreich
            crit:
                war es ein kritischer Erfolg oder Fehlschlag
        """
       # 1) Grundchance
        try:
            base_chance = int(input_dict["base_chance"]) if input_dict["base_chance"] != "" else 0
        except (ValueError, TypeError):
            # Falls der Wert kein gültiger String für int ist, fallback auf 0
            base_chance = 0


        # 2) Bonus
        try:
            bonus = int(input_dict["bonus"]) if input_dict["bonus"] != "" else 0
        except (ValueError, TypeError):
            # Falls der Wert kein gültiger String für int ist, fallback auf 0
            bonus = 0

        # 3) Wurf
        try:
            rolled = int(input_dict["rolled"]) if input_dict["rolled"] != "" else 0
        except (ValueError, TypeError):
            # Falls der Wert kein gültiger String für int ist, fallback auf 0
            rolled = 0

        final_chance = base_chance + bonus
        # clamp sinnvoll? In HTBAH kann man auch theoretisch über 100 kommen (= auto success?),
        # das Regelwerk lässt Spielleiter*innen da Freiheit. Wir clampen NICHT hart, aber für
        # die kritische Auswertung brauchen wir den effektiven Fähigkeitswert zwischen 0 und 100.
        # Für die Krit-Bereiche verwenden wir eine geclampte Variante:
        crit_basis = max(0, min(100, final_chance))


        # Spezialfall: 0 ("0 + 00" auf den Würfeln) ist das gleiche wie 100 (kritischer Fehlschlag)
        if rolled == 0:
            rolled = 100

        if not (1 <= rolled <= 100):
            logger.debug(
                    "Ungültiger Würfelwert: rolled=%d. Erwartet: 1 ≤ rolled ≤ 100 (0 wird als 100 interpretiert). "
                    "Benutzer wird per QMessageBox gewarnt.",
                    rolled
                )
            return

        # 4) Erfolg / Fehlschlag bestimmen
        # Erfolg, wenn roll <= final_chance
        is_success = (rolled <= final_chance)

        # 5) Kritisch?
        # laut Regel:
        # - kritischer Erfolg:
        #   * immer bei 1
        #   * oder innerhalb der ersten 10% des Fähigkeitswertes
        #     -> wenn Fähigkeitswert=70 => 7% => 1..7
        # - kritischer Fehlschlag:
        #   * immer bei 100
        #   * oder innerhalb der letzten 10% der "Unfähigkeit"
        #     Unfähigkeit = 100 - Fähigkeitswert
        #     Bei 70 => Unfähigkeit=30 => 3% kritisch => 97..100
        #
        # WICHTIG: Diese Grenzen berechnen wir mit crit_basis (geclampter final_chance 0..100)

        ability = crit_basis
        inability = 100 - ability

        crit_success_threshold = max(1, kaufmaennisch_runden(ability / 10)) # z.B. 70 -> 7
        crit_fail_threshold = max(1, kaufmaennisch_runden(inability / 10))  # z.B. 30 -> 3

        # Bereiche:
        # krit. Erfolg: 1 .. crit_success_threshold
        crit_success_low = 1
        crit_success_high = crit_success_threshold

        # krit. Fehlschlag: 100-crit_fail_threshold+1 .. 100
        crit_fail_low = 100 - crit_fail_threshold + 1
        crit_fail_high = 100

        # Immer-Sonderregeln
        if rolled == 1:
            is_crit_success = True
        else:
            is_crit_success = (rolled >= crit_success_low and rolled <= crit_success_high)

        if rolled == 100:
            is_crit_fail = True
        else:
            is_crit_fail = (rolled >= crit_fail_low and rolled <= crit_fail_high)

        if (is_success and is_crit_success) or (not is_success and is_crit_fail):
            is_crit = True
        else:
            is_crit = False
  
        # Falls er gleichzeitig in beiden kritischen Bereichen liegen könnte (extreme Modifikatoren),
        # geben wir harte Regeln Vorrang:
        # 1 hat immer Vorrang als krit. Erfolg
        # 100 hat immer Vorrang als krit. Fehlschlag
        # Sonst sollten sich die Bereiche eh nicht überlappen.

        return self.ChanceResult(
            success=is_success,
            crit=is_crit,
        )
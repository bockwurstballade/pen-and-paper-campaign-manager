import uuid
from typing import Dict, Any, List, Optional
from utils.functions.math import kaufmaennisch_runden

class CharacterBuilder:
    """
    Diese Klasse kapselt das Wissen über die interne JSON-Struktur eines Charakters.
    Sie nimmt Rohdaten (meist aus dem UI) entgegen, validiert sie und baut das finale Dictionary.
    """
    
    @staticmethod
    def build_character(
        char_id: Optional[str],
        campaign_id: Optional[str],
        name: str,
        role: str,
        char_class: str,
        gender: str,
        age: int,
        hitpoints: int,
        base_damage: str,
        build: str,
        religion: str,
        occupation: str,
        marital_status: str,
        description: str,
        armor_enabled: bool,
        armor_value: Optional[int],
        armor_condition: Optional[int],
        skills_raw: Dict[str, Dict[str, int]],
        items_raw: Dict[str, dict],
        conditions_raw: Dict[str, dict]
    ) -> Dict[str, Any]:
        
        # Basis-Validierungen (falls das UI das übersehen hat)
        if not name:
            raise ValueError("Name darf nicht leer sein.")
        if not 1 <= age <= 120:
            raise ValueError("Alter muss zwischen 1 und 120 liegen.")
        if not 1 <= hitpoints <= 100:
            raise ValueError("Lebenspunkte müssen zwischen 1 und 100 liegen.")
        
        if armor_enabled:
            if armor_value is None or armor_condition is None:
                raise ValueError("Rüstungswert und Zustand dürfen nicht leer sein.")
            if not (0 <= armor_value <= 9) or not (0 <= armor_condition <= 9):
                raise ValueError("Rüstungswert und Rüstungszustand müssen zwischen 0 und 9 liegen.")

        # Skills / Categories / Inspiration Points berechnen
        skills_data = {}
        category_scores = {}
        inspiration_points = {}
        total_used = 0

        for category, skills in skills_raw.items():
            skills_data[category] = {}
            category_sum = 0
            for skill, val in skills.items():
                if not 0 <= val <= 100:
                    raise ValueError(f"{skill}: Wert muss zwischen 0 und 100 liegen.")
                skills_data[category][skill] = val
                category_sum += val

            total_used += category_sum
            category_scores[category] = kaufmaennisch_runden(category_sum / 10)
            inspiration_points[category] = kaufmaennisch_runden(category_scores[category] / 10)

        # Je nach Regeledition kann man diese Schranke hier an/abschalten
        if total_used > 400:
            raise ValueError(f"Gesamtpunkte überschreiten 400! (Du hast {total_used})")

        # ID sicherstellen
        final_id = char_id if char_id else str(uuid.uuid4())

        return {
            "id": final_id,
            "campaign_id": campaign_id,
            "name": name,
            "class": char_class,
            "gender": gender,
            "age": age,
            "hitpoints": hitpoints,
            "base_damage": base_damage,
            "build": build,
            "religion": religion,
            "occupation": occupation,
            "marital_status": marital_status,
            "skills": skills_data,
            "category_scores": category_scores,
            "inspiration_points": inspiration_points,
            "items": items_raw,
            "conditions": conditions_raw,
            "description": description,
            "role": role,
            "armor_enabled": armor_enabled,
            "armor_value": armor_value,
            "armor_condition": armor_condition
        }

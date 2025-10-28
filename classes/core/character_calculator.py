from typing import Dict, Any

from utils.functions.math import kaufmaennisch_runden

class CharacterCalculator:
    """
    Enthält rein logische Berechnungen für Charaktere.
    Zum Beispiel effektive Skillwerte, die bei Würfelproben gewürfelt werden müssen.
    """
    @staticmethod
    def compute_effective_values(char_data: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """
        Berechnet effektive Kategorie- und Fertigkeitswerte unter Berücksichtigung
        missionsweiter Zustände (conditions).

        Args:
            char_data: Vollständiges Charakter-Dictionary (wie aus JSON geladen).

            Erwartet ein Dict mit:
            {
            "categories": {cat: effective_cat_value, ...},
            "skills": {skill: effective_skill_value, ...}
            }
            z. B.
            char_data = {
                "id": "44c36ed7-0a40-43c4-ba00-3500f2dfad1f",
                "name": "Zombie - generisch",
                "class": "Krieger",
                "gender": "Divers",
                "age": 100,
                "hitpoints": 80,
                "base_damage": "2W10",
                "build": "Schlank",
                "religion": "",
                "occupation": "",
                "marital_status": "Ledig",
                "skills": {
                    "Handeln": {
                        "Hauen": 50,
                        "Beißen": 50
                    },
                    "Wissen": {},
                    "Soziales": {}
                },
                "category_scores": {
                    "Handeln": 10,
                    "Wissen": 0,
                    "Soziales": 0
                },
                "inspiration_points": {
                    "Handeln": 1,
                    "Wissen": 0,
                    "Soziales": 0
                },
                "items": {},
                "conditions": {},
                "role": "npc"
            }
            Zustände ('missionsweit') werden eingerechnet.

        Returns:
            Dict mit:
                - "categories": {cat: effective_value}
                - "skills": {skill: effective_value
        """
        # 1. Basiswerte sammeln (aus gespeichertem Charakter)
        #    -> base_skill_values[skill], base_category_base[cat]
        base_skill_values = {}
        base_category_sum = {}   # cat -> sum der rohen skill-werte
        base_category_values = {}  # cat -> kaufmännisch gerundet(sum/10)

        skills_by_cat = char_data.get("skills", {})
        for cat, skillmap in skills_by_cat.items():
            total = 0
            for skill, val in skillmap.items():
                try:
                    val_int = int(val)
                except:
                    val_int = 0
                base_skill_values[skill] = val_int
                total += val_int
            # Kategorie-Basiswert wie im Editor: kaufmännisch_runden(total/10)
            base_category_values[cat] = kaufmaennisch_runden(total / 10)
            base_category_sum[cat] = total  # nur falls wir's mal brauchen später

        # 2. Zustands-Modifikatoren sammeln
        #    Wir schauen NUR auf effect_type == "missionsweit"
        skill_mods = {}
        category_mods = {}

        conds = char_data.get("conditions", {})
        for cond_name, cond in conds.items():
            if cond.get("effect_type") != "missionsweit":
                continue

            target = cond.get("effect_target", "")
            val = cond.get("effect_value", 0)
            try:
                val = int(val)
            except:
                val = 0

            # Fertigkeit: XYZ
            if target.startswith("Fertigkeit: "):
                skill_name = target.replace("Fertigkeit: ", "", 1).strip()
                skill_mods[skill_name] = skill_mods.get(skill_name, 0) + val

            # Kategoriewert: XYZ
            elif target.startswith("Kategoriewert: "):
                cat_name = target.replace("Kategoriewert: ", "", 1).strip()
                category_mods[cat_name] = category_mods.get(cat_name, 0) + val

            # Hinweis: Geistesblitzpunkte buffen wir fürs Würfeln erstmal nicht separat,
            # da du gesagt hast, wir können auf Kategorien/Skills würfeln.
            # Falls du später auch direkte Geistesblitzpunkte-Würfe willst,
            # müssten wir die hier berücksichtigen.

        # 3. effektive Kategorien anwenden
        effective_categories = {}
        for cat, base_val in base_category_values.items():
            effective_categories[cat] = base_val + category_mods.get(cat, 0)

        # 4. effektive Skills:
        #    effektiver Skillwert = Basis Skill + Skill-Mods + effektiver Kategorienwert (der Kategorie, zu der der Skill gehört)
        effective_skills = {}
        for cat, skillmap in skills_by_cat.items():
            cat_val_effective = effective_categories.get(cat, 0)
            for skill, val in skillmap.items():
                base_val = base_skill_values.get(skill, 0)
                mod_val = skill_mods.get(skill, 0)
                effective_skills[skill] = base_val + mod_val + cat_val_effective

        return {
            "categories": effective_categories,
            "skills": effective_skills,
        }
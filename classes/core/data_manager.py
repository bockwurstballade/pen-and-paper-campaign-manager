import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataManager:
    """
    Zentrale Klasse für Datenzugriff (Datei-I/O) von Charakteren, Items und Zuständen.
    Ersetzt direkte os.listdir und json.load Aufrufe in UI-Klassen.
    """
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CHARACTERS_DIR = os.path.join(BASE_DIR, "data", "characters")
    CAMPAIGNS_DIR = os.path.join(BASE_DIR, "data", "campaigns")
    ITEMS_DIR = os.path.join(BASE_DIR, "data", "items")
    LEGACY_ITEMS_FILE = os.path.join(BASE_DIR, "items.json")
    CONDITIONS_DIR = os.path.join(BASE_DIR, "data", "conditions")
    LEGACY_CONDITIONS_FILE = os.path.join(BASE_DIR, "conditions.json")
    PLAYERS_DIR = os.path.join(BASE_DIR, "data", "players")

    @classmethod
    def _ensure_dirs(cls):
        os.makedirs(cls.CHARACTERS_DIR, exist_ok=True)
        os.makedirs(cls.CAMPAIGNS_DIR, exist_ok=True)
        os.makedirs(cls.ITEMS_DIR, exist_ok=True)
        os.makedirs(cls.CONDITIONS_DIR, exist_ok=True)
        os.makedirs(cls.PLAYERS_DIR, exist_ok=True)

    # --- helpers ---

    @staticmethod
    def _safe_name(name: str, fallback: str = "Unbenannt") -> str:
        safe = "".join(c for c in (name or "") if c.isalnum() or c in (" ", "-", "_")).strip()
        return safe or fallback

    @classmethod
    def _copy_entity_image(
        cls,
        *,
        entity_safe_name: str,
        entity_id: str,
        target_folder_path: str,
        image_source_path: Optional[str],
    ) -> Optional[str]:
        """
        Kopiert ein Bild in den Zielordner und liefert den gespeicherten Dateinamen zurück.
        Akzeptiert: png/jpg/jpeg/webp
        """
        if not image_source_path or not os.path.exists(image_source_path):
            return None

        import shutil

        _, ext = os.path.splitext(image_source_path)
        ext = ext.lower()
        allowed_exts = {".png", ".jpg", ".jpeg", ".webp"}
        if ext not in allowed_exts:
            logger.warning(f"Nicht unterstütztes Bildformat: {image_source_path}")
            return None

        image_filename = f"{entity_safe_name} - {entity_id}{ext}"
        image_target_path = os.path.join(target_folder_path, image_filename)
        try:
            shutil.copyfile(image_source_path, image_target_path)
            return image_filename
        except Exception as e:
            logger.error(f"Fehler beim Kopieren des Bildes nach {image_target_path}: {e}")
            return None

    @classmethod
    def _find_campaign_base_dir(cls, campaign_id: str) -> str:
        """
        Kampagnen können (neu) als Ordner '<Titel> - <UUID>/' oder (legacy) als '<UUID>/' existieren.
        Diese Funktion liefert den passenden Basispfad für kampagnenspezifische Charaktere.
        """
        if not campaign_id:
            return cls.CAMPAIGNS_DIR

        cls._ensure_dirs()

        # 1) exakte legacy-Struktur: data/campaigns/<campaign_id>/
        legacy = os.path.join(cls.CAMPAIGNS_DIR, str(campaign_id))
        if os.path.isdir(legacy):
            return legacy

        # 2) neue Struktur: Ordner, dessen Name die UUID enthält
        try:
            for entry in os.listdir(cls.CAMPAIGNS_DIR):
                entry_path = os.path.join(cls.CAMPAIGNS_DIR, entry)
                if os.path.isdir(entry_path) and str(campaign_id) in entry:
                    return entry_path
        except Exception:
            pass

        # Fallback: legacy anlegen
        os.makedirs(legacy, exist_ok=True)
        return legacy

    # --- CHARACTER MANAGEMENT ---
    
    @classmethod
    def _get_all_character_files(cls) -> List[str]:
        """
        Sammelt alle Charakter-JSON-Dateien.
        Berücksichtigt:
        - Einzelne Dateien direkt in data/characters
        - Charakter-Unterordner (Name - UUID/...) in data/characters
        - Kampagnen-Ordner unter data/campaigns (inkl. dortiger Unterordner)
        """
        cls._ensure_dirs()
        files: List[str] = []

        dirs_to_search = [cls.CHARACTERS_DIR, cls.CAMPAIGNS_DIR]

        for base_dir in dirs_to_search:
            if not os.path.exists(base_dir):
                continue
            # rekursiv durchlaufen, um auch Unterordner mit Charakteren zu finden
            for root, _, filenames in os.walk(base_dir):
                for fname in filenames:
                    if fname.lower().endswith(".json"):
                        files.append(os.path.join(root, fname))
        return files

    @classmethod
    def get_all_characters(cls) -> List[Dict[str, Any]]:
        """Lädt alle Charaktereigenschaften inklusive Dateipfad und Anzeigetext."""
        chars = []
        for full_path in cls._get_all_character_files():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Überspringe eventuell andere JSONs, die in diesen Ordnern liegen (wie Kampagnen-JSONs)
                if "hitpoints" not in data and "age" not in data:
                    continue
                    
                char_name = data.get("name", "(unbenannt)")
                char_class = data.get("class", "?")
                char_age = data.get("age", "?")
                char_id = data.get("id", "???")
                
                display = f"{char_name} | {char_class}, {char_age} Jahre [{char_id[:8]}...]"
                
                chars.append({
                    "data": data,
                    "path": full_path,
                    "display": display,
                })
            except Exception as e:
                logger.error(f"Fehler beim Laden von Charakter {full_path}: {e}")
        return chars

    @classmethod
    def get_character_by_id(cls, char_id: str) -> Optional[Dict[str, Any]]:
        """Sucht einen Charakter anhand seiner ID."""
        for full_path in cls._get_all_character_files():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("id") == char_id:
                        return data
            except Exception as e:
                logger.error(f"Fehler beim Lesen von {full_path}: {e}")
        return None

    @classmethod
    def get_characters_by_role(cls, role_filter: str) -> List[Dict[str, Any]]:
        """Gibt alle Charaktere zurück, die eine bestimmte Rolle besitzen (z.B. 'pc' oder 'npc')."""
        results = []
        for full_path in cls._get_all_character_files():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if "hitpoints" not in data and "age" not in data:
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
            except Exception as e:
                logger.error(f"Fehler beim Laden von {full_path}: {e}")
        return results

    @classmethod
    def save_character(cls, character_data: dict, file_path: str = None, image_source_path: Optional[str] = None) -> str:
        """
        Speichert einen Charakter ab.
        - Legt (falls nötig) einen Unterordner für diesen Charakter an: "<Name> - <UUID>/"
        - Speichert die JSON-Datei in diesem Ordner.
        - Optional: kopiert ein übergebenes Bild in diesen Ordner und merkt sich den Dateinamen
          im Feld "image_filename" des Charakter-Dictionaries.
        """
        cls._ensure_dirs()
        char_id = character_data.get("id", "undefined_id")
        char_name = character_data.get("name", "Unbenannt")
        campaign_id = character_data.get("campaign_id")

        safe_name = cls._safe_name(char_name, fallback="Unbenannt")

        # Basisziel: Charaktere entweder global oder kampagnenspezifisch
        if campaign_id:
            base_target_dir = cls._find_campaign_base_dir(str(campaign_id))
        else:
            base_target_dir = cls.CHARACTERS_DIR

        # Unterordner pro Charakter: "<Name> - <UUID>/"
        char_folder_name = f"{safe_name} - {char_id}"
        char_folder_path = os.path.join(base_target_dir, char_folder_name)
        os.makedirs(char_folder_path, exist_ok=True)

        # JSON-Dateiname weiterhin "<Name> - <UUID>.json"
        filename = f"{safe_name} - {char_id}.json"
        expected_path = os.path.join(char_folder_path, filename)

        # Aufräumen einer alten JSON-Datei, falls sich Pfad geändert hat
        if file_path and file_path != expected_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        # Optional: Bild kopieren
        copied = cls._copy_entity_image(
            entity_safe_name=safe_name,
            entity_id=str(char_id),
            target_folder_path=char_folder_path,
            image_source_path=image_source_path,
        )
        if copied:
            character_data["image_filename"] = copied

        try:
            with open(expected_path, "w", encoding="utf-8") as f:
                json.dump(character_data, f, indent=4, ensure_ascii=False)
            return expected_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Charakters nach {expected_path}: {e}")
            raise

    # --- ITEM MANAGEMENT ---
    
    @classmethod
    def _migrate_items_if_needed(cls):
        """Migriert die alte items.json in Einzeldateien, falls sie noch existiert."""
        if not os.path.exists(cls.LEGACY_ITEMS_FILE):
            return
            
        cls._ensure_dirs()
        try:
            with open(cls.LEGACY_ITEMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            items = data.get("items", [])
            for item in items:
                cls.save_item(item)
                
            # Nach erfolgreicher Migration umbenennen, um mehrfache Migrationen zu vermeiden
            backup_path = cls.LEGACY_ITEMS_FILE + ".bak"
            if os.path.exists(backup_path):
                os.remove(backup_path) # Falls schon ein Backup existiert
            os.rename(cls.LEGACY_ITEMS_FILE, backup_path)
            logger.info(f"Erfolgreich {len(items)} Items nach {cls.ITEMS_DIR} migriert.")
        except Exception as e:
            logger.error(f"Fehler bei der Migration von items.json: {e}")

    @classmethod
    def get_all_items(cls) -> List[Dict[str, Any]]:
        """Lädt alle Items aus dem data/items/ Ordner."""
        return [it["data"] for it in cls.get_all_items_meta()]

    @classmethod
    def get_all_items_meta(cls) -> List[Dict[str, Any]]:
        """Lädt alle Items inkl. Dateipfad und Anzeigetext (unterstützt Unterordner)."""
        cls._migrate_items_if_needed()
        cls._ensure_dirs()

        items: List[Dict[str, Any]] = []
        if not os.path.exists(cls.ITEMS_DIR):
            return items

        for root, _, filenames in os.walk(cls.ITEMS_DIR):
            for fname in filenames:
                if not fname.lower().endswith(".json"):
                    continue
                full_path = os.path.join(root, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        item_data = json.load(f)
                    # Heuristik: Item muss id und name besitzen
                    if "id" not in item_data or "name" not in item_data:
                        continue
                    item_id = item_data.get("id", "???")
                    item_name = item_data.get("name", "(unbenannt)")
                    display = f"{item_name} [{item_id[:8]}...]"
                    items.append({"data": item_data, "path": full_path, "display": display})
                except Exception as e:
                    logger.error(f"Fehler beim Laden von Item {full_path}: {e}")

        return items

    @classmethod
    def save_item(cls, item_data: Dict[str, Any], file_path: str = None, image_source_path: Optional[str] = None) -> str:
        """
        Speichert ein Item:
        - Unterordner pro Item: "<Name> - <UUID>/"
        - JSON in diesem Ordner: "<Name> - <UUID>.json"
        - Optional: Bild in diesem Ordner, Referenz in "image_filename"
        """
        cls._ensure_dirs()
        
        item_id = item_data.get("id")
        if not item_id:
            import uuid
            item_id = str(uuid.uuid4())
            item_data["id"] = item_id
            
        item_name = item_data.get("name", "Unbenannt")
        safe_name = cls._safe_name(item_name, fallback="Unbenannt")

        item_folder_name = f"{safe_name} - {item_id}"
        item_folder_path = os.path.join(cls.ITEMS_DIR, item_folder_name)
        os.makedirs(item_folder_path, exist_ok=True)

        filename = f"{safe_name} - {item_id}.json"
        expected_path = os.path.join(item_folder_path, filename)

        if file_path and file_path != expected_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        copied = cls._copy_entity_image(
            entity_safe_name=safe_name,
            entity_id=str(item_id),
            target_folder_path=item_folder_path,
            image_source_path=image_source_path,
        )
        if copied:
            item_data["image_filename"] = copied
        
        try:
            with open(expected_path, "w", encoding="utf-8") as f:
                json.dump(item_data, f, indent=4, ensure_ascii=False)
            return expected_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Items nach {expected_path}: {e}")
            raise

    @classmethod
    def delete_item(cls, item_id: str) -> bool:
        """Löscht ein Item anhand seiner ID."""
        if not os.path.exists(cls.ITEMS_DIR):
            return False
            
        deleted_any = False
        # rekursiv, da Items nun in Unterordnern liegen können
        for root, _, filenames in os.walk(cls.ITEMS_DIR):
            for fname in filenames:
                if item_id in fname:
                    filepath = os.path.join(root, fname)
                    try:
                        os.remove(filepath)
                        deleted_any = True
                    except Exception as e:
                        logger.error(f"Fehler beim Löschen des Items {filepath}: {e}")
        return deleted_any

    # --- CONDITION MANAGEMENT ---
    
    @classmethod
    def _migrate_conditions_if_needed(cls):
        """Migriert die alte conditions.json in Einzeldateien, falls sie noch existiert."""
        if not os.path.exists(cls.LEGACY_CONDITIONS_FILE):
            return
            
        cls._ensure_dirs()
        try:
            with open(cls.LEGACY_CONDITIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            conditions = data.get("conditions", [])
            for cond in conditions:
                cls.save_condition(cond)
                
            backup_path = cls.LEGACY_CONDITIONS_FILE + ".bak"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(cls.LEGACY_CONDITIONS_FILE, backup_path)
            logger.info(f"Erfolgreich {len(conditions)} Zustände nach {cls.CONDITIONS_DIR} migriert.")
        except Exception as e:
            logger.error(f"Fehler bei der Migration von conditions.json: {e}")

    @classmethod
    def get_all_conditions(cls) -> List[Dict[str, Any]]:
        """Lädt alle Zustände aus dem data/conditions/ Ordner."""
        return [c["data"] for c in cls.get_all_conditions_meta()]

    @classmethod
    def get_all_conditions_meta(cls) -> List[Dict[str, Any]]:
        """Lädt alle Zustände inkl. Dateipfad und Anzeigetext (unterstützt Unterordner)."""
        cls._migrate_conditions_if_needed()
        cls._ensure_dirs()

        conditions: List[Dict[str, Any]] = []
        if not os.path.exists(cls.CONDITIONS_DIR):
            return conditions

        for root, _, filenames in os.walk(cls.CONDITIONS_DIR):
            for fname in filenames:
                if not fname.lower().endswith(".json"):
                    continue
                full_path = os.path.join(root, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        cond_data = json.load(f)
                    if "id" not in cond_data or "name" not in cond_data:
                        continue
                    cond_id = cond_data.get("id", "???")
                    cond_name = cond_data.get("name", "(unbenannt)")
                    display = f"{cond_name} [{cond_id[:8]}...]"
                    conditions.append({"data": cond_data, "path": full_path, "display": display})
                except Exception as e:
                    logger.error(f"Fehler beim Laden von Zustand {full_path}: {e}")

        return conditions

    @classmethod
    def save_condition(cls, cond_data: Dict[str, Any], file_path: str = None, image_source_path: Optional[str] = None) -> str:
        """
        Speichert einen Zustand:
        - Unterordner pro Zustand: "<Name> - <UUID>/"
        - JSON in diesem Ordner: "<Name> - <UUID>.json"
        - Optional: Bild in diesem Ordner, Referenz in "image_filename"
        """
        cls._ensure_dirs()
        
        cond_id = cond_data.get("id")
        if not cond_id:
            import uuid
            cond_id = str(uuid.uuid4())
            cond_data["id"] = cond_id
            
        cond_name = cond_data.get("name", "Unbenannt")
        safe_name = cls._safe_name(cond_name, fallback="Unbenannt")

        cond_folder_name = f"{safe_name} - {cond_id}"
        cond_folder_path = os.path.join(cls.CONDITIONS_DIR, cond_folder_name)
        os.makedirs(cond_folder_path, exist_ok=True)

        filename = f"{safe_name} - {cond_id}.json"
        expected_path = os.path.join(cond_folder_path, filename)

        if file_path and file_path != expected_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        copied = cls._copy_entity_image(
            entity_safe_name=safe_name,
            entity_id=str(cond_id),
            target_folder_path=cond_folder_path,
            image_source_path=image_source_path,
        )
        if copied:
            cond_data["image_filename"] = copied
        
        try:
            with open(expected_path, "w", encoding="utf-8") as f:
                json.dump(cond_data, f, indent=4, ensure_ascii=False)
            return expected_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Zustands nach {expected_path}: {e}")
            raise

    @classmethod
    def delete_condition(cls, cond_id: str) -> bool:
        """Löscht einen Zustand anhand seiner ID."""
        if not os.path.exists(cls.CONDITIONS_DIR):
            return False
            
        deleted_any = False
        # rekursiv, da Zustände nun in Unterordnern liegen können
        for root, _, filenames in os.walk(cls.CONDITIONS_DIR):
            for fname in filenames:
                if cond_id in fname:
                    filepath = os.path.join(root, fname)
                    try:
                        os.remove(filepath)
                        deleted_any = True
                    except Exception as e:
                        logger.error(f"Fehler beim Löschen des Zustands {filepath}: {e}")
        return deleted_any

    # --- CAMPAIGN MANAGEMENT ---
    
    @classmethod
    def get_all_campaigns(cls) -> List[Dict[str, Any]]:
        """Lädt alle Kampagnen aus dem data/campaigns Ordner."""
        cls._ensure_dirs()
        campaigns = []
        if not os.path.exists(cls.CAMPAIGNS_DIR):
            return campaigns

        for root, _, filenames in os.walk(cls.CAMPAIGNS_DIR):
            for fname in filenames:
                if not fname.lower().endswith(".json"):
                    continue

                full_path = os.path.join(root, fname)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Kampagnen von Charakteren unterscheiden
                    if "title" not in data or "type" not in data or "id" not in data:
                        continue
                    if "hitpoints" in data or "age" in data:
                        continue

                    title = data.get("title", "(unbenannt)")
                    c_type = data.get("type", "Unknown")
                    c_id = data.get("id", "???")

                    display = f"[{c_type}] {title} ({c_id[:8]}...)"

                    campaigns.append(
                        {
                            "data": data,
                            "path": full_path,
                            "display": display,
                        }
                    )
                except Exception as e:
                    logger.error(f"Fehler beim Laden der Kampagne {full_path}: {e}")
        return campaigns

    @classmethod
    def save_campaign(cls, campaign_data: dict, file_path: str = None, image_source_path: Optional[str] = None) -> str:
        """
        Speichert eine Kampagne:
        - Unterordner pro Kampagne: "<Titel> - <UUID>/"
        - JSON in diesem Ordner: "<Titel> - <UUID>.json"
        - Optional: Bild in diesem Ordner, Referenz in "image_filename"
        """
        cls._ensure_dirs()
        c_id = campaign_data.get("id", "undefined_id")
        title = campaign_data.get("title", "Unbenannt")

        safe_title = cls._safe_name(title, fallback="Unbenannt")
        camp_folder_name = f"{safe_title} - {c_id}"
        camp_folder_path = os.path.join(cls.CAMPAIGNS_DIR, camp_folder_name)
        os.makedirs(camp_folder_path, exist_ok=True)

        filename = f"{safe_title} - {c_id}.json"
        expected_path = os.path.join(camp_folder_path, filename)

        if file_path and file_path != expected_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        copied = cls._copy_entity_image(
            entity_safe_name=safe_title,
            entity_id=str(c_id),
            target_folder_path=camp_folder_path,
            image_source_path=image_source_path,
        )
        if copied:
            campaign_data["image_filename"] = copied
            
        try:
            with open(expected_path, "w", encoding="utf-8") as f:
                json.dump(campaign_data, f, indent=4, ensure_ascii=False)
            return expected_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Kampagne nach {expected_path}: {e}")
            raise

    # --- PLAYER MANAGEMENT ---

    @classmethod
    def get_all_players(cls) -> List[Dict[str, Any]]:
        """
        Lädt alle Spieler aus dem data/players Ordner und liefert eine Liste von
        Dictionaires mit Daten, Dateipfad und Anzeigetext.
        """
        cls._ensure_dirs()
        players: List[Dict[str, Any]] = []

        if not os.path.exists(cls.PLAYERS_DIR):
            return players

        for fname in os.listdir(cls.PLAYERS_DIR):
            if not fname.lower().endswith(".json"):
                continue

            full_path = os.path.join(cls.PLAYERS_DIR, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                player_id = data.get("id", "???")
                name = data.get("name", "(unbenannt)")
                nickname = data.get("nickname", "")
                discord = data.get("discord", "")

                parts = [name]
                if nickname:
                    parts.append(f"'{nickname}'")
                if discord:
                    parts.append(f"[{discord}]")
                display = " ".join(parts) + f" ({player_id[:8]}...)"

                players.append(
                    {
                        "data": data,
                        "path": full_path,
                        "display": display,
                    }
                )
            except Exception as e:
                logger.error(f"Fehler beim Laden von Spieler {full_path}: {e}")

        return players

    @classmethod
    def get_player_by_id(cls, player_id: str) -> Optional[Dict[str, Any]]:
        """Sucht einen Spieler anhand seiner ID."""
        cls._ensure_dirs()
        if not os.path.exists(cls.PLAYERS_DIR):
            return None

        for fname in os.listdir(cls.PLAYERS_DIR):
            if not fname.lower().endswith(".json"):
                continue

            full_path = os.path.join(cls.PLAYERS_DIR, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("id") == player_id:
                    return data
            except Exception as e:
                logger.error(f"Fehler beim Lesen von Spieler {full_path}: {e}")

        return None

    @classmethod
    def save_player(cls, player_data: Dict[str, Any]) -> str:
        """
        Speichert einen Spieler als eigene JSON-Datei in data/players.
        Die Datei wird anhand von Spielername und UUID benannt.
        """
        cls._ensure_dirs()

        player_id = player_data.get("id")
        if not player_id:
            import uuid

            player_id = str(uuid.uuid4())
            player_data["id"] = player_id

        name = player_data.get("name", "Unbenannt")
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
        filename = f"{safe_name} - {player_id}.json"
        expected_path = os.path.join(cls.PLAYERS_DIR, filename)

        # Alte Dateien mit derselben ID entfernen (Namensänderung etc.)
        for fname in os.listdir(cls.PLAYERS_DIR):
            if player_id in fname and fname != filename:
                try:
                    os.remove(os.path.join(cls.PLAYERS_DIR, fname))
                except OSError:
                    pass

        try:
            with open(expected_path, "w", encoding="utf-8") as f:
                json.dump(player_data, f, indent=4, ensure_ascii=False)
            return expected_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Spielers nach {expected_path}: {e}")
            raise

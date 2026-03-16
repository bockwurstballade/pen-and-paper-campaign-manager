# benötigte Imports
import os
import json
import uuid
## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

## eigene Funktionen
from utils.functions.math import kaufmaennisch_runden
## eigene Klassen
from classes.core.data_manager import DataManager
from classes.core.character_builder import CharacterBuilder

from classes.ui.character_creation.base_stats_widget import BaseStatsWidget
from classes.ui.character_creation.armor_widget import ArmorWidget
from classes.ui.character_creation.skills_widget import SkillsWidget
from classes.ui.character_creation.items_widget import ItemsWidget
from classes.ui.character_creation.conditions_widget import ConditionsWidget




class CharacterCreationDialog(QDialog):

    def __init__(self, parent=None):
        self.loaded_file = None
        self.char_id = None          # UUID des Charakters
        self._selected_image_source_path = None  # lokaler Pfad, den der User gewählt hat
        self._current_image_filename = None  # Dateiname im Charakter-Ordner (aus geladenem Charakter)

        super().__init__(parent)
        self.setWindowTitle("Neuen Charakter erstellen")
        # Großzügigere Mindest- und Startgröße, damit der Inhalt nicht gequetscht wird.
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        # ---------- SCROLL WRAPPER ----------
        # Das äußere Layout gehört dem Dialog selbst
        outer_layout = QVBoxLayout(self)

        # ScrollArea, in der der eigentliche Content wohnt
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Widget innerhalb der ScrollArea
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        # Das echte Content-Layout (das früher main_layout war)
        content_layout = QVBoxLayout(self.scroll_widget)

        # ScrollArea ins äußere Layout einhängen
        outer_layout.addWidget(self.scroll_area)

        # Ab hier benutzen wir main_layout so wie vorher
        main_layout = content_layout
        # ---------- /SCROLL WRAPPER ----------
        # Spieler-Zuweisung
        self.player_combo = QComboBox()
        self._player_id_by_index = {}
        self._reload_players_into_combo()
        player_group = QGroupBox("Spieler")
        player_layout = QFormLayout()
        player_layout.addRow("Zugewiesener Spieler:", self.player_combo)
        player_group.setLayout(player_layout)
        main_layout.addWidget(player_group)

        # Charakterbild
        image_group = QGroupBox("Charakterbild")
        image_layout = QVBoxLayout()
        self.portrait_label = QLabel("Kein Bild ausgewählt.")
        self.portrait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.portrait_label.setMinimumHeight(160)
        self.portrait_label.setStyleSheet("border: 1px solid gray;")
        self.portrait_label.setWordWrap(True)

        self.select_image_button = QPushButton("Bild auswählen …")
        self.select_image_button.clicked.connect(self.choose_character_image)

        image_layout.addWidget(self.portrait_label)
        image_layout.addWidget(self.select_image_button)
        image_group.setLayout(image_layout)
        main_layout.addWidget(image_group)

        # Base Stats Modul
        self.base_stats = BaseStatsWidget()
        main_layout.addWidget(self.base_stats)

        # Rüstungsmodul
        self.armor = ArmorWidget()
        main_layout.addWidget(self.armor)

        # Fähigkeiten
        self.skills = SkillsWidget()
        main_layout.addWidget(self.skills)

        # Items
        self.items = ItemsWidget(self)
        main_layout.addWidget(self.items)

        # Zustände
        self.conditions = ConditionsWidget(self)
        main_layout.addWidget(self.conditions)

        # Werte werden nun in BaseStatsWidget und SkillsWidget gehalten.

        # Speichern-Button
        save_button = QPushButton("Charakter speichern")
        save_button.clicked.connect(self.save_character)
        main_layout.addWidget(save_button)

        main_layout.addStretch()


    def _show_placeholder_image(self, text: str = "Kein Bild verfügbar."):
        """Zeigt einen einfachen Platzhaltertext im Bildbereich."""
        self.portrait_label.setPixmap(QPixmap())
        self.portrait_label.setText(text)

    def _show_image_from_path(self, path: str):
        """Lädt ein Bild von einem Pfad und zeigt es skaliert in der Vorschau an."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._show_placeholder_image("Bild konnte nicht geladen werden.")
            return
        scaled = pixmap.scaled(
            self.portrait_label.width() if self.portrait_label.width() > 0 else 200,
            self.portrait_label.height() if self.portrait_label.height() > 0 else 200,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.portrait_label.setText("")
        self.portrait_label.setPixmap(scaled)

    def choose_character_image(self):
        """Öffnet einen File-Chooser, um ein Charakterbild auszuwählen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charakterbild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.webp)",
        )
        if not file_path:
            return

        self._selected_image_source_path = file_path
        # Wenn ein neues Bild gewählt wird, überschreiben wir bewusst die alte Referenz
        self._current_image_filename = None
        self._show_image_from_path(file_path)

    def _reload_players_into_combo(self, selected_player_id: str = None):
        """
        Lädt die Liste aller Spieler und befüllt die ComboBox.
        """
        self.player_combo.clear()
        self._player_id_by_index.clear()

        # Default-Eintrag: kein Spieler
        self.player_combo.addItem("— Kein Spieler zugewiesen —", userData=None)
        self._player_id_by_index[0] = None

        players = DataManager.get_all_players()
        selected_index = 0
        for idx_offset, player_info in enumerate(players, start=1):
            pdata = player_info["data"]
            pid = pdata.get("id")
            display = player_info.get("display") or pdata.get("name", "(unbenannt)")
            self.player_combo.addItem(display, userData=pid)
            self._player_id_by_index[idx_offset] = pid
            if selected_player_id and pid == selected_player_id:
                selected_index = idx_offset

        self.player_combo.setCurrentIndex(selected_index)

    def attach_item_conditions(self, item_name, condition_ids):
        """
        Nimmt die Zustands-UUIDs eines Items, schaut nach,
        und sorgt dafür, dass diese Zustände im Charakter sichtbar/aktiv sind.
        Falls ein Zustand schon da ist (z.B. durch ein anderes Item), erhöhen wir nur den Refcount.
        """
        conditions = DataManager.get_all_conditions()
        cond_map = {c["id"]: c for c in conditions}

        for cid in condition_ids:
            cond_data = cond_map.get(cid)
            if not cond_data:
                # Zustand ungekannt? -> wir hängen trotzdem nen Platzhalter ein, aber ohne Wirkung
                cond_data = {
                    "id": cid,
                    "name": f"(Unbekannter Zustand {cid[:8]}...)",
                    "description": "Originalzustand nicht gefunden.",
                    "effect_type": "keine Auswirkung",
                    "effect_target": "",
                    "effect_value": 0
                }

            # Refcount erhöhen
            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            # Wenn Zustand schon im UI ist, nicht doppelt zeichnen
            if cid in self.active_condition_by_id:
                continue

            # Zustand im UI darstellen
            self.render_condition_block_from_condition_data(cid, cond_data, source_item=item_name)

            # merken
            self.active_condition_by_id[cid] = cond_data

        # Effekte neu anwenden (falls missionsweit etc.)
        self.recalculate_conditions_effects()

    def render_condition_block_from_condition_data(self, cid, cond_data, source_item=None):
        """
        Zeichnet einen Zustand in die Zustands-UI (self.conditions_layout),
        basierend auf einem cond_data-Dict im Format aus conditions.json.
        cid = eindeutige Zustands-ID (UUID)
        source_item = optionaler Item-Name, das diesen Zustand liefert
        """

    def manual_remove_condition_by_id(self, cid):
        self.conditions.manual_remove_condition_by_id(cid)

    def recalculate_conditions_effects(self):
        self.conditions.recalculate_conditions_effects()

    def apply_mission_effects(self):
        """Aktualisiert alle missionsweiten Effekte auf den Charakterwerten."""
        base_hp = self.base_stats.base_hitpoints
        total_hp_modifier = 0
        affecting_conditions = []

        for cond_name, cond in self.conditions.condition_groups.items():
            if cond["type"] == "missionsweit" and cond["effect_target"] == "Lebenspunkte":
                total_hp_modifier += cond["effect_value"]
                affecting_conditions.append(f"{cond_name} ({cond['effect_value']:+})")

        modified_hp = base_hp + total_hp_modifier

        hp_input = self.base_stats.hitpoints_input
        if affecting_conditions:
            hp_input.setStyleSheet("color: red; font-weight: bold;")
            tooltip = " | ".join(affecting_conditions)
            hp_input.setToolTip(f"Modifiziert durch: {tooltip}")
            hp_input.blockSignals(True)
            hp_input.setText(str(modified_hp))
            hp_input.blockSignals(False)
        else:
            hp_input.blockSignals(True)
            hp_input.setText(str(base_hp))
            hp_input.blockSignals(False)
            hp_input.setStyleSheet("")
            hp_input.setToolTip("")

    def apply_all_mission_effects(self):
        """Wendet alle missionsweiten Zustände auf Lebenspunkte, Kategorien, Geistesblitzpunkte und Fertigkeiten an."""
        self.apply_mission_effects()

        for category, base_val in self.skills.base_values["Kategorien"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.conditions.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Kategoriewert: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            cat_label = self.skills.category_labels[category]
            if affecting:
                cat_label.setText(f"{category}-Wert: {modified_val} (Mod: {'; '.join(affecting)})")
                cat_label.setStyleSheet("color: darkred; font-weight: bold;")
            else:
                cat_label.setText(f"{category}-Wert: {base_val}")
                cat_label.setStyleSheet("")

        for category, base_val in self.skills.base_values["Geistesblitzpunkte"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.conditions.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Geistesblitzpunkte: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            insp_label = self.skills.inspiration_labels[category]
            if affecting:
                insp_label.setText(f"Geistesblitzpunkte ({category}): {modified_val} (Mod: {'; '.join(affecting)})")
                insp_label.setStyleSheet("color: darkblue; font-weight: bold;")
            else:
                insp_label.setText(f"Geistesblitzpunkte ({category}): {base_val}")
                insp_label.setStyleSheet("")

        for skill, base_val in self.skills.base_values["Fertigkeiten"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.conditions.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Fertigkeit: {skill}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier

            for category, skills_dict in self.skills.skill_inputs.items():
                if skill in skills_dict:
                    field = skills_dict[skill]
                    field.blockSignals(True)
                    field.setText(str(modified_val))
                    field.blockSignals(False)
                    if affecting:
                        field.setStyleSheet("color: darkgreen; font-weight: bold;")
                        tooltip = " | ".join(affecting)
                        field.setToolTip(f"Modifiziert durch: {tooltip}")
                    else:
                        field.setStyleSheet("")
                        field.setToolTip("")
                    break

        self.skills.skills_handler.update_endwert_labels()


    def save_character(self):
        try:
            # Lade strukturierte Teilbereiche aus den neuen Widgets
            base_data = self.base_stats.get_data()
            armor_data = self.armor.get_data()
            skills_raw = self.skills.get_data()

            items_data = self.items.get_data()
            conditions_data = self.conditions.get_data()

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e) if str(e) != "" else "Bitte gültige Zahlen eingeben.")
            return

        try:
            builder_args = {
                "char_id": self.char_id,
                **base_data,
                **armor_data,
                "skills_raw": skills_raw,
                "items_raw": items_data,
                "conditions_raw": conditions_data,
            }
            selected_player_id = self.player_combo.currentData()
            selected_player_obj = None
            if selected_player_id:
                selected_player_obj = DataManager.get_player_by_id(selected_player_id)
            builder_args["player_id"] = selected_player_id
            builder_args["player"] = selected_player_obj
            character = CharacterBuilder.build_character(**builder_args)
            # Update our UI state with the stable ID the builder ensured
            self.char_id = character["id"]
        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e))
            return

        target_path = self.loaded_file if hasattr(self, "loaded_file") else None

        if hasattr(self, "items_handler"):
            self.items_handler.upsert_items_to_global_library()

        try:
            # Falls kein neues Bild ausgewählt wurde, aber ein Bild bereits existiert,
            # muss die Referenz in der JSON erhalten bleiben.
            if not self._selected_image_source_path and self._current_image_filename:
                character["image_filename"] = self._current_image_filename

            target_path = DataManager.save_character(
                character,
                file_path=target_path,
                image_source_path=self._selected_image_source_path,
            )
            # Das merken wir uns für zukünftige Saves in dieser Session
            self.loaded_file = target_path
            
            # Aus dem returned Character das saubere "Name" field fürs Popup holen
            saved_name = character["name"]
            QMessageBox.information(self, "Erfolg", f"Charakter '{saved_name}' wurde gespeichert:\n{target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Charakter nicht speichern:\n{str(e)}")
            return
        self.accept()



    def load_character_data(self, character, file_path):
        """Befüllt das Formular mit den Daten eines geladenen Charakters."""
        self.loaded_file = file_path

        # Datei & ID merken
        self.loaded_file = file_path
        self.char_id = character.get("id", str(uuid.uuid4()))
        # Zugewiesenen Spieler wiederherstellen
        char_player_id = character.get("player_id")
        self._reload_players_into_combo(selected_player_id=char_player_id)

        # Charakterbild laden (falls vorhanden)
        image_filename = character.get("image_filename")
        if image_filename:
            char_dir = os.path.dirname(file_path)
            image_path = os.path.join(char_dir, image_filename)
            if os.path.exists(image_path):
                self._show_image_from_path(image_path)
                self._current_image_filename = image_filename
                self._selected_image_source_path = None
                # keine neue Quelle gesetzt -> vorhandenes Bild bleibt, solange der User nichts Neues auswählt
            else:
                self._show_placeholder_image("Bilddatei nicht gefunden.")
                self._current_image_filename = None
        else:
            self._show_placeholder_image("Kein Bild verfügbar.")
            self._current_image_filename = None

        # Basisfelder via Component laden
        self.base_stats.load_data(character)

        # Rüstungsmodul via Component laden
        self.armor.load_data(character)


        # Fähigkeiten via Component laden
        self.skills.load_data(character)

        # Items und Conditions laden
        self.items.load_data(character)
        self.conditions.load_data(character, self.items)

        # Skills / Endwerte aktualisieren
        self.skills.skills_handler.update_points()


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

## eigene Funktionen
from utils.functions.math import kaufmaennisch_runden
## eigene Klassen

from classes.ui.attribute_dialog import AttributeDialog
from classes.ui.condition_editor_dialog import ConditionEditorDialog


class CharacterCreationDialog(QDialog):

    def __init__(self, parent=None):
        self.loaded_file = None
        self.loaded_file = None      # Pfad zur Datei auf Platte (wenn geladen/gespeichert)
        self.char_id = None          # UUID des Charakters

        super().__init__(parent)
        self.setWindowTitle("Neuen Charakter erstellen")
        self.setGeometry(150, 150, 500, 700)

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


        # Basisdaten-Formular
        self.base_form = QFormLayout()
        self.name_input = QLineEdit()
        self.class_input = QComboBox()
        self.class_input.addItems(["Krieger", "Magier", "Dieb"])
        self.gender_input = QComboBox()
        self.gender_input.addItems(["Männlich", "Weiblich", "Divers"])
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Zahl eingeben")
        self.hitpoints_input = QLineEdit()
        self.hitpoints_input.setPlaceholderText("Zahl eingeben")
        self.hitpoints_input.textChanged.connect(self.update_base_hitpoints)
        self.build_input = QComboBox()
        self.build_input.addItems(["Schlank", "Durchschnittlich", "Kräftig"])
        self.religion_input = QLineEdit()
        self.occupation_input = QLineEdit()
        self.marital_status_input = QComboBox()
        self.marital_status_input.addItems(["Ledig", "Verheiratet", "Verwitwet"])

        self.base_form.addRow("Name:", self.name_input)
        self.base_form.addRow("Klasse:", self.class_input)
        self.base_form.addRow("Geschlecht:", self.gender_input)
        self.base_form.addRow("Alter:", self.age_input)
        self.base_form.addRow("Lebenspunkte:", self.hitpoints_input)
        self.base_form.addRow("Statur:", self.build_input)
        self.base_form.addRow("Religion:", self.religion_input)
        self.base_form.addRow("Beruf:", self.occupation_input)
        self.base_form.addRow("Familienstand:", self.marital_status_input)
        self.role_input = QComboBox()
        self.role_input.addItems(["Spielercharakter", "NSC / Gegner"])
        self.base_form.insertRow(0, "Typ:", self.role_input)


        main_layout.addLayout(self.base_form)

        # Fähigkeiten
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {}
        self.skill_end_labels = {}
        self.category_labels = {}
        self.inspiration_labels = {}
        self.group_boxes = {}
        self.form_layouts = {}
        self.add_buttons = {}
        self.total_points_label = QLabel("Verbleibende Punkte: 400")
        self.total_points = 400

        for category in self.skills:
            self.group_boxes[category] = QGroupBox(category)
            self.style_groupbox(self.group_boxes[category])

            self.form_layouts[category] = QFormLayout()
            self.skill_inputs[category] = {}

            vbox = QVBoxLayout()
            vbox.addLayout(self.form_layouts[category])

            self.add_buttons[category] = QPushButton("+ Neue Fähigkeit")
            self.add_buttons[category].clicked.connect(lambda _, cat=category: self.add_skill(cat))
            vbox.addWidget(self.add_buttons[category])

            self.group_boxes[category].setLayout(vbox)

            main_layout.addWidget(self.group_boxes[category])

            self.category_labels[category] = QLabel(f"{category}-Wert: 0")
            self.inspiration_labels[category] = QLabel(f"Geistesblitzpunkte ({category}): 0")
            main_layout.addWidget(self.category_labels[category])
            main_layout.addWidget(self.inspiration_labels[category])


        main_layout.addWidget(self.total_points_label)

        # Items
        self.items_group = QGroupBox("Items")
        self.style_groupbox(self.items_group)
        self.items_layout = QVBoxLayout()
        self.item_groups = {}
        self.item_add_button = QPushButton("+ Neues Item")
        self.item_add_button.clicked.connect(self.add_item)
        self.items_layout.addWidget(self.item_add_button)
        self.item_add_from_lib_button = QPushButton("+ Item aus Sammlung hinzufügen")
        self.item_add_from_lib_button.clicked.connect(self.add_item_from_library)
        self.items_layout.addWidget(self.item_add_from_lib_button)
        self.items_group.setLayout(self.items_layout)
        main_layout.addWidget(self.items_group)

        # Zustände
        self.conditions_group = QGroupBox("Zustände")
        self.style_groupbox(self.conditions_group)
        self.conditions_layout = QVBoxLayout()
        self.condition_groups = {}
        # Zustände von Items
        # mappt item_name -> liste von condition_ids (UUIDs)
        self.item_condition_links = {}

        # mappt condition_id -> dict mit den vollen Zustandsdaten
        # so wie sie aus conditions.json kommen oder ad hoc gebaut wurden
        self.active_condition_by_id = {}

        # wir brauchen außerdem einen Counter, um Zustände, die von mehreren Items kommen, nicht doppelt zu entfernen
        # mappt condition_id -> wie viele Quellen (Items oder manuell) diesen Zustand "aktiv" halten
        self.condition_refcount = {}
        self.condition_add_button = QPushButton("+ Neuer Zustand")
        self.condition_add_button.clicked.connect(self.add_condition)
        self.conditions_layout.addWidget(self.condition_add_button)
        self.conditions_group.setLayout(self.conditions_layout)
        self.condition_add_from_lib_button = QPushButton("+ Zustand aus Sammlung hinzufügen")
        self.condition_add_from_lib_button.clicked.connect(self.add_condition_from_library)
        self.conditions_layout.addWidget(self.condition_add_from_lib_button)
        main_layout.addWidget(self.conditions_group)


        self.base_hitpoints = 0

        # Grundschaden (z. B. Faustkampf oder allgemeiner Nahkampfschaden)
        self.base_damage_input = QLineEdit()
        self.base_damage_input.setPlaceholderText("z.B. 1W6 oder 1W6+2")
        main_layout.addWidget(QLabel("Grundschaden:"))
        main_layout.addWidget(self.base_damage_input)

        self.base_values = {
            "Lebenspunkte": 0,
            "Kategorien": {},        # z. B. {"Handeln": 5}
            "Geistesblitzpunkte": {},# z. B. {"Wissen": 1}
            "Fertigkeiten": {}       # z. B. {"Laufen": 50}
        }


        # Speichern-Button
        save_button = QPushButton("Charakter speichern")
        save_button.clicked.connect(self.save_character)
        main_layout.addWidget(save_button)

        main_layout.addStretch()

    def _is_condition_target_valid_for_this_character(self, effect_target: str) -> bool:
        """
        Prüft, ob ein effect_target wie
        - "Lebenspunkte"
        - "Fertigkeit: Schleichen"
        - "Kategoriewert: Handeln"
        - "Geistesblitzpunkte: Wissen"
        in diesem Charakter tatsächlich existiert.

        Gibt True zurück, wenn der Zustand sinnvoll angewendet werden kann.
        """
        if not effect_target or effect_target == "(kein Ziel / n/a)":
            return True  # dann gibt's eh keinen Effekt, also nix zu validieren

        # 1) Lebenspunkte ist immer okay
        if effect_target == "Lebenspunkte":
            return True

        # 2) Fertigkeit: <name>
        if effect_target.startswith("Fertigkeit: "):
            skill_name = effect_target.replace("Fertigkeit: ", "", 1).strip()
            # checkt, ob der Char diese Fertigkeit überhaupt hat
            for cat, skill_list in self.skills.items():
                if skill_name in skill_list:
                    return True
            return False

        # 3) Kategoriewert: <cat>
        if effect_target.startswith("Kategoriewert: "):
            cat_name = effect_target.replace("Kategoriewert: ", "", 1).strip()
            # Kategorienamen sind unsere keys in self.skills (Handeln/Wissen/Soziales/…)
            return cat_name in self.skills

        # 4) Geistesblitzpunkte: <cat>
        if effect_target.startswith("Geistesblitzpunkte: "):
            cat_name = effect_target.replace("Geistesblitzpunkte: ", "", 1).strip()
            return cat_name in self.skills

        # 5) Wenn es ein komplett freies/custom Ziel ist (Benutzerdefiniert ... oder etwas Exotisches),
        #    dann können wir nicht prüfen → wir lassen es als gültig durchgehen.
        return True


    def style_groupbox(self, box: QGroupBox):
        box.setStyleSheet("""
            QGroupBox {
                margin-top: 8px;
                padding: 8px;
                border: 1px solid #444;
                border-radius: 6px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 4px;
                color: #ddd;
                font-weight: bold;
            }
        """)

    def add_skill(self, category):
        skill_name, ok = QInputDialog.getText(self, f"Neue Fähigkeit für {category}", "Fähigkeitsname:")
        if not ok or not skill_name.strip():
            QMessageBox.warning(self, "Fehler", "Fähigkeitsname darf nicht leer sein.")
            return
        skill_name = skill_name.strip()
        if skill_name in self.skills[category]:
            QMessageBox.warning(self, "Fehler", f"Fähigkeit '{skill_name}' existiert bereits in {category}.")
            return

        # Fähigkeit hinzufügen
        self.skills[category].append(skill_name)
        self.skill_end_labels.setdefault(category, {})

        # Eingabefeld + Entfernen-Button + Endwert-Label
        input_field = QLineEdit()
        input_field.setPlaceholderText("0–100")
        input_field.textChanged.connect(self.update_points)

        end_label = QLabel("Endwert: 0")
        self.skill_end_labels[category][skill_name] = end_label

        remove_button = QPushButton("– Entfernen")
        remove_button.clicked.connect(lambda _, cat=category, skill=skill_name: self.remove_skill(cat, skill))

        # Layout der Zeile
        h_layout = QHBoxLayout()
        h_layout.addWidget(input_field)
        h_layout.addWidget(end_label)
        h_layout.addWidget(remove_button)

        self.skill_inputs[category][skill_name] = input_field
        self.form_layouts[category].addRow(f"{skill_name}:", h_layout)
        self.update_points()


    def remove_skill(self, category, skill_name):
        """Entfernt eine Fähigkeit aus dem Layout und den Datenstrukturen."""
        if skill_name not in self.skills[category]:
            return

        self.skills[category].remove(skill_name)
        input_field = self.skill_inputs[category].pop(skill_name)
        if skill_name in self.skill_end_labels.get(category, {}):
            del self.skill_end_labels[category][skill_name]

        # Layoutzeile im FormLayout finden und entfernen
        form_layout = self.form_layouts[category]
        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if label_item and label_item.widget() and label_item.widget().text().startswith(skill_name):
                # Widgets explizit löschen
                label_item.widget().deleteLater()
                if field_item:
                    field_widget = field_item.layout() or field_item.widget()
                    if field_widget:
                        while isinstance(field_widget, QHBoxLayout) and field_widget.count():
                            item = field_widget.takeAt(0)
                            if item.widget():
                                item.widget().deleteLater()
                        field_widget.deleteLater()
                form_layout.removeRow(i)
                break

        self.update_points()
        QMessageBox.information(self, "Erfolg", f"Fertigkeit '{skill_name}' wurde entfernt.")


    def add_item(self):
        # 1. Namen abfragen wie bisher
        item_name, ok = QInputDialog.getText(self, "Neues Item", "Item-Name:")
        if not ok or not item_name.strip():
            QMessageBox.warning(self, "Fehler", "Item-Name darf nicht leer sein.")
            return
        item_name = item_name.strip()
        if item_name in self.item_groups:
            QMessageBox.warning(self, "Fehler", f"Item '{item_name}' existiert bereits.")
            return

        # 2. GroupBox für dieses Item
        item_group = QGroupBox(item_name)
        self.style_groupbox(item_group)

        item_layout = QVBoxLayout()

        # Wir speichern für dieses Item:
        # - attributes: dict[str,str]
        # - layout: das VBoxLayout
        # - group: die QGroupBox
        # - id: None (neu erzeugtes Item hat noch keine globale Item-ID)
        # - linked_conditions: [] (erstmal leer)
        # - is_weapon_checkbox: QCheckBox
        # - damage_field: QLineEdit
        self.item_groups[item_name] = {
            "attributes": {},
            "layout": item_layout,
            "group": item_group,
            "id": None,
            "linked_conditions": [],
            "is_weapon_checkbox": None,
            "damage_field": None,
        }

        # 3. Attribut-Liste (genau wie vorher)
        attr_layout = QFormLayout()
        item_layout.addLayout(attr_layout)

        # Wir brauchen Zugriff auf attr_layout später, also speichern wir es auch:
        self.item_groups[item_name]["attr_layout"] = attr_layout

        # 4. Waffen-spezifischer Bereich
        weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
        damage_input = QLineEdit()
        damage_input.setPlaceholderText("z. B. 1W6+2")
        damage_row = QHBoxLayout()
        damage_row.addWidget(QLabel("Schadensformel:"))
        damage_row.addWidget(damage_input)

        # standardmäßig ausgeblendet, bis Checkbox aktiv
        damage_input.setVisible(False)

        def on_weapon_toggle(state):
            damage_input.setVisible(state == Qt.CheckState.Checked.value)

        weapon_checkbox.stateChanged.connect(on_weapon_toggle)

        item_layout.addWidget(weapon_checkbox)
        item_layout.addLayout(damage_row)

        # Referenzen speichern, damit save_character() drankommt
        self.item_groups[item_name]["is_weapon_checkbox"] = weapon_checkbox
        self.item_groups[item_name]["damage_field"] = damage_input

        # 5. Button: neues Attribut hinzufügen (wie vorher)
        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addWidget(add_attr_button)

        # 6. Entfernen-Button wie vorher
        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item(item))
        item_layout.addWidget(remove_button)

        # 7. In die UI einhängen (vor den beiden globalen Buttons)
        item_group.setLayout(item_layout)

        # In items_layout ist aktuell:
        #   [ + Neues Item ]
        #   [ + Item aus Sammlung hinzufügen ]
        # Wir wollen das neue Item VOR diesen Buttons einfügen.
        insert_pos = max(0, self.items_layout.count() - 2)
        self.items_layout.insertWidget(insert_pos, item_group)


    def add_attribute(self, item_name):
        dialog = AttributeDialog(self)
        if dialog.exec() == 1:
            attr_name, attr_value = dialog.get_attribute()
            if not attr_name or not attr_value:
                QMessageBox.warning(self, "Fehler", "Attribut-Name und -Wert dürfen nicht leer sein.")
                return
            if attr_name in self.item_groups[item_name]["attributes"]:
                QMessageBox.warning(self, "Fehler", f"Attribut '{attr_name}' existiert bereits für {item_name}.")
                return

            self.item_groups[item_name]["attributes"][attr_name] = attr_value
            attr_layout = self.item_groups[item_name]["layout"].itemAt(0).layout()
            attr_layout.addRow(f"{attr_name}:", QLabel(attr_value))

    def remove_item(self, item_name):
        if item_name in self.item_groups:
            item_group = self.item_groups[item_name]["group"]
            self.items_layout.removeWidget(item_group)
            item_group.deleteLater()
            del self.item_groups[item_name]
            QMessageBox.information(self, "Erfolg", f"Item '{item_name}' wurde entfernt.")

    def add_item_from_library(self):
        """Fügt dem Charakter ein Item aus items.json hinzu und aktiviert dessen Zustände."""
        # 1. Items-Datei lesen
        if not os.path.exists("items.json"):
            QMessageBox.warning(self, "Fehler", "Keine items.json gefunden.")
            return

        try:
            with open("items.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                items_list = data.get("items", [])
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von items.json:\n{e}")
            return

        if not items_list:
            QMessageBox.information(self, "Hinweis", "Es sind keine Items in items.json vorhanden.")
            return

        # 2. Item auswählen lassen
        item_choices = [f"{it.get('name','(unbenannt)')} [{it.get('id','?')}]" for it in items_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Item auswählen",
            "Welches Item soll hinzugefügt werden?",
            item_choices,
            0,
            False
        )
        if not ok:
            return

        idx = item_choices.index(choice)
        chosen_item = items_list[idx]

        item_name = chosen_item.get("name", "Unbenanntes Item")
        item_id = chosen_item.get("id", str(uuid.uuid4()))
        attributes = chosen_item.get("attributes", {})
        linked_conditions = chosen_item.get("linked_conditions", [])

        # 3. Prüfen, ob Item mit gleichem Namen schon existiert
        if item_name in self.item_groups:
            QMessageBox.warning(self, "Fehler", f"Item '{item_name}' existiert bereits im Inventar.")
            return

        # 4. Item-UI Block erstellen wie in add_item(), aber vorbefüllt
        item_group = QGroupBox(item_name)
        item_group = QGroupBox(item_name)
        self.style_groupbox(item_group)

        item_layout = QVBoxLayout()
        self.item_groups[item_name] = {
            "attributes": {},
            "layout": item_layout,
            "group": item_group,
            "id": item_id,
            "linked_conditions": linked_conditions,
            "is_weapon": chosen_item.get("is_weapon", False),
            "damage_formula": chosen_item.get("damage_formula", ""),
            # diese beiden Felder haben Bibliotheks-Items nicht als Widgets:
            "is_weapon_checkbox": None,
            "damage_field": None,
        }

        attr_layout = QFormLayout()
        # Attribute aus dem gespeicherten Item hinzufügen
        for attr_name, attr_value in attributes.items():
            attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))
            self.item_groups[item_name]["attributes"][attr_name] = attr_value

        if chosen_item.get("is_weapon"):
            dmg = chosen_item.get("damage_formula", "")
            attr_layout.addRow("Waffe", QLabel(f"Schaden: {dmg}"))

        add_attr_button = QPushButton("+ Neue Eigenschaft")
        add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))
        item_layout.addLayout(attr_layout)
        item_layout.addWidget(add_attr_button)

        remove_button = QPushButton("- Item entfernen")
        remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))
        item_layout.addWidget(remove_button)

        item_group.setLayout(item_layout)
        self.items_layout.insertWidget(self.items_layout.count() - 2, item_group)
        # ^ wir -2 einfügen statt -1, weil wir jetzt 2 Buttons (Neues Item / Aus Sammlung) am Ende haben

        # 5. Zustände aus diesem Item aktivieren
        self.item_condition_links[item_name] = linked_conditions
        self.attach_item_conditions(item_name, linked_conditions)

    def attach_item_conditions(self, item_name, condition_ids):
        """
        Nimmt die Zustands-UUIDs eines Items, schaut in conditions.json nach,
        und sorgt dafür, dass diese Zustände im Charakter sichtbar/aktiv sind.
        Falls ein Zustand schon da ist (z.B. durch ein anderes Item), erhöhen wir nur den Refcount.
        """
        # conditions.json laden -> Map von ID -> Zustand
        cond_map = {}
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_map = {c["id"]: c for c in data.get("conditions", [])}
            except Exception:
                pass

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

        cond_name = cond_data.get("name", f"Zustand {cid[:8]}")
        desc = cond_data.get("description", "")
        effect_type = cond_data.get("effect_type", "keine Auswirkung")
        effect_target = cond_data.get("effect_target", "")
        effect_value = cond_data.get("effect_value", 0)

        group = QGroupBox(cond_name)
        self.style_groupbox(group)

        layout = QVBoxLayout()

        # Beschreibung
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Effektzeile (falls einer existiert)
        if effect_type != "keine Auswirkung" and effect_target:
            # Prüfen, ob dieses Target für DIESEN Charakter überhaupt Sinn ergibt
            target_ok = self._is_condition_target_valid_for_this_character(effect_target)

            if target_ok:
                # normaler Stil
                effect_label = QLabel(
                    f"{effect_type.capitalize()}e Wirkung: "
                    f"{effect_target} "
                    f"{effect_value:+}"
                )
                effect_label.setStyleSheet("color: #555; font-style: italic;")
                layout.addWidget(effect_label)
            else:
                # WARNUNG: dieser Zustand will etwas modifizieren,
                # das der Charakter gar nicht hat
                effect_label = QLabel(
                    f"{effect_type.capitalize()}e Wirkung: "
                    f"{effect_target} {effect_value:+}  (⚠ nicht vorhanden bei diesem Charakter)"
                )
                effect_label.setStyleSheet("color: #b00; font-weight: bold;")
                layout.addWidget(effect_label)

                warn_label = QLabel(
                    "Hinweis: Dieser Zustand verweist auf einen Wert, "
                    "den dieser Charakter aktuell nicht besitzt."
                )
                warn_label.setWordWrap(True)
                warn_label.setStyleSheet("color: #b00; font-size: 10px;")
                layout.addWidget(warn_label)

        # Falls der Zustand aus einem Item kommt, Info anzeigen
        if source_item:
            src_label = QLabel(f"Aktiv durch Item: {source_item}")
            src_label.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(src_label)

        # Entfernen-Button nur für manuell aktivierte Zustände (also ohne source_item).
        # Item-Zustände verschwinden nur, wenn das Item entfernt wird.
        if source_item is None:
            remove_button = QPushButton("– Zustand entfernen")
            remove_button.clicked.connect(lambda _, cond_id=cid: self.manual_remove_condition_by_id(cond_id))
            layout.addWidget(remove_button)

        group.setLayout(layout)

        # Gruppe VOR den Buttons einfügen (Buttons sind am Ende des Layouts)
        # self.conditions_layout enthält:
        #   [ "+ Neuer Zustand", ... , "+ Zustand aus Sammlung hinzufügen" ]
        # Wir wollen den Block davor reinschieben.
        insert_pos = max(0, self.conditions_layout.count() - 2)
        self.conditions_layout.insertWidget(insert_pos, group)

        # Widget-Metadaten in active_condition_by_id speichern (für späteres Entfernen usw.)
        temp = self.active_condition_by_id.get(cid, {})
        temp["_widget"] = group
        # Merge dicts
        merged = {**cond_data, **temp}
        self.active_condition_by_id[cid] = merged


    def remove_item_and_detach_conditions(self, item_name):
        """
        Entfernt ein Item aus dem Charakterinventar und reduziert die Refcounts
        der damit verknüpften Zustände.
        Zustände, die dadurch auf 0 fallen, verschwinden wieder aus der UI.
        """
        if item_name not in self.item_groups:
            return

        # 1. Zustands-Links dieses Items holen
        linked_conds = self.item_groups[item_name].get("linked_conditions", [])
        for cid in linked_conds:
            if cid in self.condition_refcount:
                self.condition_refcount[cid] -= 1
                if self.condition_refcount[cid] <= 0:
                    # komplett entfernen
                    self.condition_refcount.pop(cid, None)
                    self.remove_condition_widget_by_id(cid)

        # 2. Item-UI entfernen
        item_group = self.item_groups[item_name]["group"]
        self.items_layout.removeWidget(item_group)
        item_group.deleteLater()
        del self.item_groups[item_name]

        # 3. auch den Link aus item_condition_links löschen
        if item_name in self.item_condition_links:
            del self.item_condition_links[item_name]

        # 4. Effekte neu anwenden
        self.recalculate_conditions_effects()

        QMessageBox.information(self, "Erfolg", f"Item '{item_name}' wurde entfernt.")


    def remove_condition_widget_by_id(self, cid):
        """
        Entfernt die UI-Darstellung eines Zustands (falls sichtbar) und vergisst ihn in active_condition_by_id.
        Achtung: das betrifft NUR Zustände, die über Items gekommen sind ODER manuell entfernt wurden.
        """
        cond_info = self.active_condition_by_id.get(cid)
        if not cond_info:
            return

        widget = cond_info.get("_widget")
        if widget:
            self.conditions_layout.removeWidget(widget)
            widget.deleteLater()

        # aus Tracking entfernen
        self.active_condition_by_id.pop(cid, None)

    def add_condition(self):
        # baue die möglichen Ziele aus DIESEM Charakter
        skill_targets, cat_targets, insp_targets = self._build_condition_target_lists()

        dlg = ConditionEditorDialog(
            parent=self,
            available_skill_targets=skill_targets,
            available_category_targets=cat_targets,
            available_inspiration_targets=insp_targets
        )
        dlg.condition_id = str(uuid.uuid4())  # direkt neue UUID vergeben
        result = dlg.exec()
        if result != QDialog.DialogCode.Accepted:
            return  # Abbruch -> nix tun

        # Zustand wurde gespeichert → wir müssen ihn in den Charakter aktivieren
        # und ins UI holen

        # Schritt 1: conditions.json neu einlesen und den gespeicherten Zustand finden
        if os.path.exists("conditions.json"):
            try:
                with open("conditions.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cond_list = data.get("conditions", [])
            except Exception:
                cond_list = []
        else:
            cond_list = []

        # Wir suchen den Zustand per ID, die der Dialog gesetzt hat
        saved_cond = None
        for c in cond_list:
            if c.get("id") == dlg.condition_id:
                saved_cond = c
                break

        # Falls wir ihn nicht finden, ist was schief – dann bauen wir ihn eben aus Dialogfeldern rekonstruiert neu
        if not saved_cond:
            saved_cond = {
                "id": dlg.condition_id,
                "name": dlg.name_input.text().strip(),
                "description": dlg.description_input.text().strip(),
                "effect_type": dlg.effect_type_input.currentText(),
                "effect_target": dlg.ask_for_custom_target_if_needed(),  # finaler target string
                "effect_value": int(dlg.effect_value_input.text() or "0")
            }

        cid = saved_cond["id"]

        # Refcount erhöhen
        self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

        # In unsere aktiven Zustände aufnehmen (falls nicht schon da)
        already_active = cid in self.active_condition_by_id
        self.active_condition_by_id[cid] = {
            "id": cid,
            "name": saved_cond.get("name", ""),
            "description": saved_cond.get("description", ""),
            "effect_type": saved_cond.get("effect_type", "keine Auswirkung"),
            "effect_target": saved_cond.get("effect_target", ""),
            "effect_value": saved_cond.get("effect_value", 0),
            # _widget füllen wir gleich beim rendern, falls nötig
        }

        if not already_active:
            self.render_condition_block_from_condition_data(cid, self.active_condition_by_id[cid], source_item=None)

        # Effekte neu anwenden
        self.recalculate_conditions_effects()

    def remove_condition(self, condition_name):
        """Entfernt einen Zustand aus der Liste."""
        if condition_name in self.condition_groups:
            group = self.condition_groups[condition_name]["group"]
            self.conditions_layout.removeWidget(group)
            group.deleteLater()
            del self.condition_groups[condition_name]
            QMessageBox.information(self, "Erfolg", f"Zustand '{condition_name}' wurde entfernt.")
        # Falls missionsweite Effekte betroffen sind → aktualisieren
        self.apply_mission_effects()
        self.apply_all_mission_effects()

    def _build_condition_target_lists(self):
        skill_targets = []
        category_targets = []
        insp_targets = []

        for cat, skill_list in self.skills.items():
            # Skills
            for skill in skill_list:
                skill_targets.append(f"Fertigkeit: {skill}")

            # Kategorien immer eintragen:
            category_targets.append(f"Kategoriewert: {cat}")
            insp_targets.append(f"Geistesblitzpunkte: {cat}")

        return skill_targets, category_targets, insp_targets


    def manual_remove_condition_by_id(self, cid):
        """
        Entfernt einen manuell erstellten Zustand endgültig.
        Verringert Refcount und löscht ihn ggf. auch aus condition_groups.
        """
        if cid not in self.condition_refcount:
            return

        self.condition_refcount[cid] -= 1
        if self.condition_refcount[cid] <= 0:
            self.condition_refcount.pop(cid, None)
            # UI entfernen
            self.remove_condition_widget_by_id(cid)

            # auch aus condition_groups löschen, falls dort drin
            # Wir müssen über Namen iterieren, weil condition_groups keyed by name ist
            to_delete = []
            for name, data in self.condition_groups.items():
                if data.get("id") == cid:
                    to_delete.append(name)
            for name in to_delete:
                del self.condition_groups[name]

        # Effekte neu anwenden
        self.recalculate_conditions_effects()

    def add_condition_from_library(self):
        """Fügt dem Charakter einen bestehenden Zustand aus conditions.json hinzu (ohne Itembindung)."""
        # 1. conditions.json laden
        if not os.path.exists("conditions.json"):
            QMessageBox.warning(self, "Fehler", "Keine conditions.json gefunden.")
            return

        try:
            with open("conditions.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                cond_list = data.get("conditions", [])
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Laden von conditions.json:\n{e}")
            return

        if not cond_list:
            QMessageBox.information(self, "Hinweis", "Es sind keine Zustände in conditions.json vorhanden.")
            return

        # 2. Auswahl anzeigen
        choices = [f"{c.get('name','(unbenannt)')} [{c.get('id','?')}]" for c in cond_list]
        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du hinzufügen?",
            choices,
            0,
            False
        )
        if not ok:
            return

        idx = choices.index(choice)
        chosen = cond_list[idx]

        # 3. Die rohen Daten dieses Zustands holen
        cid = chosen.get("id", str(uuid.uuid4()))
        cond_name = chosen.get("name", f"Zustand {cid[:8]}")
        cond_description = chosen.get("description", "")
        cond_effect_type = chosen.get("effect_type", "keine Auswirkung")
        cond_effect_target = chosen.get("effect_target", "")
        cond_effect_value = chosen.get("effect_value", 0)

        # 4. In unsere laufenden Strukturen integrieren
        # Falls Zustand schon aktiv ist (z. B. durch Item oder schon mal hinzugefügt), 
        # erhöhen wir nur den Refcount und zeichnen ihn NICHT neu.
        already_active = cid in self.active_condition_by_id

        # Refcount +1
        self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

        if not already_active:
            # Zustand muss neu erzeugt und gerendert werden
            cond_data = {
                "id": cid,
                "name": cond_name,
                "description": cond_description,
                "effect_type": cond_effect_type,
                "effect_target": cond_effect_target,
                "effect_value": cond_effect_value,
            }

            # merken
            self.active_condition_by_id[cid] = cond_data

            # UI-Block bauen, ohne source_item (weil direkt auf den Char angewendet)
            self.render_condition_block_from_condition_data(cid, cond_data, source_item=None)

        # 5. Effekte neu anwenden
        self.recalculate_conditions_effects()

    def recalculate_conditions_effects(self):
        """
        Spiegelt alle aktiven Zustände (aus Items + manuell) nach self.condition_groups,
        damit apply_mission_effects / apply_all_mission_effects korrekt arbeiten,
        und aktualisiert anschließend die Missionseffekte.
        """
        self.condition_groups = {}

        for cid, cond_data in self.active_condition_by_id.items():
            widget = cond_data.get("_widget")
            if widget is None:
                # Falls aus irgendeinem Grund kein UI-Widget erzeugt wurde,
                # dann ist der Zustand nicht visuell aktiv -> überspringen.
                continue

            name_for_group = cond_data.get("name", f"Zustand {cid[:8]}")
            self.condition_groups[name_for_group] = {
                "description": cond_data.get("description", ""),
                "type": cond_data.get("effect_type", "keine Auswirkung"),
                "effect_target": cond_data.get("effect_target", ""),
                "effect_value": cond_data.get("effect_value", 0),
                "group": widget,
                "id": cid,
            }

        # Deine bestehende Logik weiterverwenden:
        self.apply_mission_effects()
        self.apply_all_mission_effects()



    def update_points(self):
        try:
            total_used = 0
            for category in self.skills:
                category_sum = 0
                for skill, input_field in self.skill_inputs[category].items():
                    value = input_field.text()
                    if value:
                        val = int(value)
                        if 0 <= val <= 100:
                            category_sum += val
                        else:
                            input_field.setText("")
                            raise ValueError(f"{skill}: Wert muss zwischen 0 und 100 liegen.")
                # Kategorie-Wert berechnen
                category_score = kaufmaennisch_runden(category_sum / 10)
                self.category_labels[category].setText(f"{category}-Wert: {category_score}")

                # Geistesblitzpunkte berechnen
                inspiration_points = kaufmaennisch_runden(category_sum / (10 * 10))
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {inspiration_points}")

                # Endwerte für Fähigkeiten aktualisieren
                for skill, input_field in self.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    end_value = val + category_score
                    if category in self.skill_end_labels and skill in self.skill_end_labels[category]:
                        self.skill_end_labels[category][skill].setText(f"Endwert: {end_value}")

                total_used += category_sum

            remaining = 400 - total_used
            # Basiswerte für spätere Zustandsanwendung speichern
            for category in self.skills:
                category_label_text = self.category_labels[category].text()
                cat_value = int(category_label_text.split(":")[-1].strip())
                self.base_values["Kategorien"][category] = cat_value

                insp_label_text = self.inspiration_labels[category].text()
                insp_value = int(insp_label_text.split(":")[-1].strip().replace("Geistesblitzpunkte", "").strip())
                self.base_values["Geistesblitzpunkte"][category] = insp_value

                for skill, input_field in self.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    self.base_values["Fertigkeiten"][skill] = val

            self.total_points_label.setText(f"Verbleibende Punkte: {remaining}")
            if remaining < 0:
                raise ValueError("Gesamtpunkte überschreiten 400!")
            self.update_endwert_labels()

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e))

    def apply_mission_effects(self):
        """Aktualisiert alle missionsweiten Effekte auf den Charakterwerten."""
        base_hp = self.base_hitpoints
        total_hp_modifier = 0
        affecting_conditions = []

        for cond_name, cond in self.condition_groups.items():
            if cond["type"] == "missionsweit" and cond["effect_target"] == "Lebenspunkte":
                total_hp_modifier += cond["effect_value"]
                affecting_conditions.append(f"{cond_name} ({cond['effect_value']:+})")

        modified_hp = base_hp + total_hp_modifier

        if affecting_conditions:
            self.hitpoints_input.setStyleSheet("color: red; font-weight: bold;")
            tooltip = " | ".join(affecting_conditions)
            self.hitpoints_input.setToolTip(f"Modifiziert durch: {tooltip}")
            # Anzeige anpassen, aber Basiswert beibehalten
            self.hitpoints_input.blockSignals(True)
            self.hitpoints_input.setText(str(modified_hp))
            self.hitpoints_input.blockSignals(False)
        else:
            self.hitpoints_input.blockSignals(True)
            self.hitpoints_input.setText(str(base_hp))
            self.hitpoints_input.blockSignals(False)
            self.hitpoints_input.setStyleSheet("")
            self.hitpoints_input.setToolTip("")

    def apply_all_mission_effects(self):
        """Wendet alle missionsweiten Zustände auf Lebenspunkte, Kategorien, Geistesblitzpunkte und Fertigkeiten an."""
        # 1️⃣ Starte mit sauberen Basiswerten
        self.apply_mission_effects()  # HP separat behandeln

        # 2️⃣ Kategorie-Labels anpassen
        for category, base_val in self.base_values["Kategorien"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Kategoriewert: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            if affecting:
                self.category_labels[category].setText(f"{category}-Wert: {modified_val} (Mod: {'; '.join(affecting)})")
                self.category_labels[category].setStyleSheet("color: darkred; font-weight: bold;")
            else:
                self.category_labels[category].setText(f"{category}-Wert: {base_val}")
                self.category_labels[category].setStyleSheet("")

        # 3️⃣ Geistesblitzpunkte anpassen
        for category, base_val in self.base_values["Geistesblitzpunkte"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Geistesblitzpunkte: {category}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier
            if affecting:
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {modified_val} (Mod: {'; '.join(affecting)})")
                self.inspiration_labels[category].setStyleSheet("color: darkblue; font-weight: bold;")
            else:
                self.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {base_val}")
                self.inspiration_labels[category].setStyleSheet("")

        # 4️⃣ Fertigkeiten anpassen
        for skill, base_val in self.base_values["Fertigkeiten"].items():
            total_modifier = 0
            affecting = []
            for cond_name, cond in self.condition_groups.items():
                if cond["type"] == "missionsweit" and cond["effect_target"] == f"Fertigkeit: {skill}":
                    total_modifier += cond["effect_value"]
                    affecting.append(f"{cond_name} ({cond['effect_value']:+})")

            modified_val = base_val + total_modifier

            for category, skills_dict in self.skill_inputs.items():
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

        # ✨ NEU: nach allen Modifikationen Endwert-Labels updaten
        self.update_endwert_labels()

    def update_endwert_labels(self):
        """
        Aktualisiert alle Endwert-Labels für alle Fertigkeiten basierend auf:
        - aktuellem (ggf. modifiziertem) Skill-Wert im Eingabefeld
        - aktuellem (ggf. modifiziertem) Kategoriewert-Label
        """
        for category in self.skills:
            # aktuellen (ggf. modifizierten) Kategoriewert aus dem Label parsen
            # Label sieht jetzt z.B. so aus:
            #   "Handeln-Wert: 5"
            # oder nach Mod: 
            #   "Handeln-Wert: 3 (Mod: Fieber (-2))"
            cat_label_text = self.category_labels[category].text()
            # wir holen die erste Zahl nach dem Doppelpunkt
            try:
                cat_current_value_str = cat_label_text.split(":")[1].strip().split(" ")[0]
                cat_current_value = int(cat_current_value_str)
            except Exception:
                cat_current_value = 0

            # jetzt alle Skills dieser Kategorie anfassen
            for skill, input_field in self.skill_inputs[category].items():
                # aktueller (ggf. modifizierter) Skillwert aus dem Feld
                try:
                    skill_val = int(input_field.text()) if input_field.text() else 0
                except ValueError:
                    skill_val = 0

                # Endwert = Skillwert + Kategoriewert
                final_val = skill_val + cat_current_value

                # zum passenden Endwert-Label schreiben
                if category in self.skill_end_labels and skill in self.skill_end_labels[category]:
                    self.skill_end_labels[category][skill].setText(f"Endwert: {final_val}")



    def update_base_hitpoints(self):
        """Aktualisiert den gespeicherten Basiswert, wenn der Nutzer Lebenspunkte manuell ändert."""
        try:
            # Wenn der Nutzer gerade einen Wert eingibt, interpretieren wir ihn als Basiswert
            self.base_hitpoints = int(self.hitpoints_input.text())
        except ValueError:
            # keine Zahl → ignorieren
            self.base_hitpoints = 0


    def save_character(self):
        try:
            name = self.name_input.text().strip()
            if not name:
                raise ValueError("Name darf nicht leer sein.")

            age = int(self.age_input.text())
            if not 1 <= age <= 120:
                raise ValueError("Alter muss zwischen 1 und 120 liegen.")

            hitpoints = self.base_hitpoints
            if not 1 <= hitpoints <= 100:
                raise ValueError("Lebenspunkte müssen zwischen 1 und 100 liegen.")

            religion = self.religion_input.text().strip()
            occupation = self.occupation_input.text().strip()
            base_damage = self.base_damage_input.text().strip()

            total_used = 0
            skills_data = {}
            category_scores = {}
            inspiration_points = {}

            for category in self.skills:
                skills_data[category] = {}
                category_sum = 0
                for skill, input_field in self.skill_inputs[category].items():
                    value = input_field.text()
                    val = int(value) if value else 0
                    if not 0 <= val <= 100:
                        raise ValueError(f"{skill}: Wert muss zwischen 0 und 100 liegen.")
                    skills_data[category][skill] = val
                    category_sum += val

                total_used += category_sum
                category_scores[category] = kaufmaennisch_runden(category_sum / 10)
                inspiration_points[category] = kaufmaennisch_runden(category_scores[category] / 10)

            if total_used > 400:
                raise ValueError("Gesamtpunkte überschreiten 400!")

            # Items sammeln
            # Wir speichern jetzt vollständiger:
            # - attributes
            # - id (falls vorhanden)
            # - linked_conditions (falls vorhanden)
            items_data = {}
            for item_name, data in self.item_groups.items():
                is_weapon = False
                damage_formula = ""

                # Falls dieses Item im Dialog direkt erstellt wurde,
                # gibt es die Felder is_weapon_checkbox / damage_field
                weapon_cb = data.get("is_weapon_checkbox")
                dmg_field = data.get("damage_field")

                if weapon_cb is not None and dmg_field is not None:
                    is_weapon = weapon_cb.isChecked()
                    damage_formula = dmg_field.text().strip() if is_weapon else ""
                else:
                    # Falls das Item aus der Bibliothek kam (add_item_from_library),
                    # liegen die Infos nicht in Widgets, sondern nur implizit in attributes.
                    # Beim Laden aus der Bibliothek hatten wir:
                    #   if chosen_item.get("is_weapon"):
                    #       ...
                    # Da haben wir's NICHT explizit gespeichert. Holen wir jetzt nach:
                    is_weapon = bool(data.get("is_weapon", False))
                    damage_formula = data.get("damage_formula", "")

                items_data[item_name] = {
                    "attributes": data.get("attributes", {}),
                    "id": data.get("id", None),  # kann None sein für neue Items
                    "linked_conditions": data.get("linked_conditions", []),
                    "is_weapon": is_weapon,
                    "damage_formula": damage_formula,
                }


            # Zustände sammeln (für Savegame-Kompatibilität)
            # -> wir nehmen ALLE aktiven Zustände aus self.active_condition_by_id
            #    (also sowohl manuell erzeugte als auch durch Items automatisch aktivierte)
            conditions_data = {}
            for cid, cond_data in self.active_condition_by_id.items():
                # cond_data enthält unsere Felder aus conditions.json / add_condition
                # aber plus "_widget"; das darf NICHT in die Datei
                cleaned = {
                    "id": cid,
                    "name": cond_data.get("name", ""),
                    "description": cond_data.get("description", ""),
                    "effect_type": cond_data.get("effect_type", "keine Auswirkung"),
                    "effect_target": cond_data.get("effect_target", ""),
                    "effect_value": cond_data.get("effect_value", 0),
                }
                # Wir legen im Savegame nach name ab, so wie du es vorher gespeichert hast,
                # aber jetzt mit angereichertem Inhalt (inklusive id).
                # Falls zwei Zustände denselben Anzeigenamen haben, gewinnt der letzte – das ist
                # ok für jetzt; ein sauberer Ansatz wäre eine Liste statt dict, aber wir
                # behalten erstmal kompatibles Format.
                conditions_data[cleaned["name"]] = cleaned

        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e) if str(e) != "" else "Bitte gültige Zahlen eingeben.")
            return

        # Stelle sicher, dass der Charakter eine stabile ID hat
        if not self.char_id:
            self.char_id = str(uuid.uuid4())

        character = {
            "id": self.char_id,
            "name": name,
            "class": self.class_input.currentText(),
            "gender": self.gender_input.currentText(),
            "age": age,
            "hitpoints": hitpoints,
            "base_damage": base_damage,
            "build": self.build_input.currentText(),
            "religion": religion,
            "occupation": occupation,
            "marital_status": self.marital_status_input.currentText(),
            "skills": skills_data,
            "category_scores": category_scores,
            "inspiration_points": inspiration_points,
            "items": items_data,
            "conditions": conditions_data,
            "role": "pc" if self.role_input.currentText().startswith("Spieler") else "npc"
        }

        # Speicherort bestimmen
        # Falls wir schon aus einer Datei geladen wurden oder bereits gespeichert haben:
        if self.loaded_file:
            target_path = self.loaded_file
        else:
            # Ordner characters/ anlegen, falls nicht vorhanden
            os.makedirs("characters", exist_ok=True)

            # Dateiname z. B. "characters/<uuid>_<name>.json"
            safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
            if not safe_name:
                safe_name = "unbenannt"
            target_path = os.path.join("characters", f"{self.char_id} - {safe_name}.json")

            # Das merken wir uns für zukünftige Saves in dieser Session
            self.loaded_file = target_path

        # JSON schreiben
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(character, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Erfolg", f"Charakter '{name}' wurde gespeichert:\n{target_path}")
        self.accept()



    def load_character_data(self, character, file_path):
        """Befüllt das Formular mit den Daten eines geladenen Charakters."""
        self.loaded_file = file_path

        # Datei & ID merken
        self.loaded_file = file_path
        self.char_id = character.get("id", str(uuid.uuid4()))
        # Basisfelder
        self.name_input.setText(character.get("name", ""))
        self.class_input.setCurrentText(character.get("class", "Krieger"))
        self.gender_input.setCurrentText(character.get("gender", "Männlich"))
        self.age_input.setText(str(character.get("age", "")))
        self.base_hitpoints = int(character.get("hitpoints", 0))
        self.hitpoints_input.setText(str(self.base_hitpoints))
        self.build_input.setCurrentText(character.get("build", "Durchschnittlich"))
        self.religion_input.setText(character.get("religion", ""))
        self.occupation_input.setText(character.get("occupation", ""))
        self.marital_status_input.setCurrentText(character.get("marital_status", "Ledig"))
        self.base_damage_input.setText(character.get("base_damage", ""))


        # Reset Strukturen für Fähigkeiten
        # (Falls du reload im gleichen Dialog machst, bräuchtest du hier ein hartes "Layout cleanup".
        # Wenn du pro Load eh neuen Dialog öffnest, ist das unkritisch.)
        self.skills = {"Handeln": [], "Wissen": [], "Soziales": []}
        self.skill_inputs = {"Handeln": {}, "Wissen": {}, "Soziales": {}}
        self.skill_end_labels = {"Handeln": {}, "Wissen": {}, "Soziales": {}}

        # Fähigkeiten wiederherstellen
        for category, skills in character.get("skills", {}).items():
            for skill, value in skills.items():
                if category not in self.skills:
                    # Fallback, falls in Zukunft neue Kategorien auftauchen
                    self.skills[category] = []
                    self.skill_inputs[category] = {}
                    self.skill_end_labels[category] = {}
                    # Du müsstest hier theoretisch auch eine neue GroupBox + FormLayout bauen,
                    # aber momentan haben wir nur Handeln/Wissen/Soziales, also ignorieren wir das für jetzt.

                self.skills[category].append(skill)

                input_field = QLineEdit(str(value))
                input_field.textChanged.connect(self.update_points)

                end_label = QLabel("Endwert: 0")
                self.skill_end_labels[category][skill] = end_label

                remove_button = QPushButton("– Entfernen")
                remove_button.clicked.connect(lambda _, cat=category, skill=skill: self.remove_skill(cat, skill))

                h_layout = QHBoxLayout()
                h_layout.addWidget(input_field)
                h_layout.addWidget(end_label)
                h_layout.addWidget(remove_button)
                self.form_layouts[category].addRow(f"{skill}:", h_layout)

                self.skill_inputs[category][skill] = input_field

        # Items wiederherstellen (neues Format)
        self.item_groups = {}
        self.item_condition_links = {}

        for item_name, item_info in character.get("items", {}).items():
            attrs = item_info.get("attributes", {})
            item_uuid = item_info.get("id", str(uuid.uuid4()))
            linked_conditions = item_info.get("linked_conditions", [])

            item_group = QGroupBox(item_name)
            item_layout = QVBoxLayout()

            attr_layout = QFormLayout()
            for attr_name, attr_value in attrs.items():
                attr_layout.addRow(f"{attr_name}:", QLabel(str(attr_value)))

            # --- Waffenbereich ---
            is_weapon = item_info.get("is_weapon", False)
            damage_formula = item_info.get("damage_formula", "")
            weapon_checkbox = QCheckBox("Dieses Item ist eine Waffe")
            weapon_checkbox.setChecked(is_weapon)
            damage_input = QLineEdit()
            damage_input.setPlaceholderText("z. B. 2W10+5")
            damage_input.setText(damage_formula)
            damage_row = QHBoxLayout()
            damage_row.addWidget(QLabel("Schadensformel:"))
            damage_row.addWidget(damage_input)

            # Schadensformel nur anzeigen, wenn Checkbox aktiv ist
            damage_input.setVisible(is_weapon)

            def on_weapon_toggle(state, dmg_input=damage_input):
                dmg_input.setVisible(state == Qt.CheckState.Checked.value)

            weapon_checkbox.stateChanged.connect(on_weapon_toggle)

            add_attr_button = QPushButton("+ Neue Eigenschaft")
            add_attr_button.clicked.connect(lambda _, item=item_name: self.add_attribute(item))

            remove_button = QPushButton("- Item entfernen")
            remove_button.clicked.connect(lambda _, item=item_name: self.remove_item_and_detach_conditions(item))

            item_layout.addLayout(attr_layout)
            item_layout.addWidget(add_attr_button)
            item_layout.addWidget(remove_button)
            item_group.setLayout(item_layout)

            # Vor die beiden Buttons ("+ Neues Item", "+ Item aus Sammlung") einfügen:
            self.items_layout.insertWidget(self.items_layout.count() - 2, item_group)

            self.item_groups[item_name] = {
                "attributes": dict(attrs),
                "layout": item_layout,
                "group": item_group,
                "id": item_uuid,
                "linked_conditions": linked_conditions
            }

            self.item_condition_links[item_name] = linked_conditions

        # Zustands-Tracking komplett neu aufsetzen
        self.active_condition_by_id = {}
        self.condition_refcount = {}

        # 1) Zustände aus Items anhängen
        for item_name, cond_ids in self.item_condition_links.items():
            self.attach_item_conditions(item_name, cond_ids)

        # 2) Zustände aus dem Save explizit wiederherstellen (manuell aktivierte)
        for saved_name, cond_entry in character.get("conditions", {}).items():
            cid = cond_entry.get("id", str(uuid.uuid4()))
            cond_data = {
                "id": cid,
                "name": cond_entry.get("name", saved_name),
                "description": cond_entry.get("description", ""),
                "effect_type": cond_entry.get("effect_type", "keine Auswirkung"),
                "effect_target": cond_entry.get("effect_target", ""),
                "effect_value": cond_entry.get("effect_value", 0),
            }

            # Refcount erhöhen -> Zustand ist aktiv laut Save
            self.condition_refcount[cid] = self.condition_refcount.get(cid, 0) + 1

            if cid not in self.active_condition_by_id:
                # Zustand ist noch nicht durch ein Item gekommen -> wir müssen ihn rendern
                self.active_condition_by_id[cid] = cond_data
                self.render_condition_block_from_condition_data(cid, cond_data, source_item=None)
            else:
                # Zustand kam schon durch ein Item rein, hat also schon ein _widget.
                # Wir wollen ihn nur "aufwerten", damit er nicht verschwindet, wenn Item entfernt wird.
                # Das ist schon durch den refcount erledigt.
                pass

        # WICHTIG:
        # condition_groups NICHT hier manuell bauen!
        # Stattdessen den zentralen Weg benutzen:
        self.recalculate_conditions_effects()

        # Skills / Endwerte aktualisieren
        self.update_points()
        # Charakter Rolle
        role = character.get("role", "pc")
        if role == "npc":
            self.role_input.setCurrentText("NSC / Gegner")
        else:
            self.role_input.setCurrentText("Spielercharakter")


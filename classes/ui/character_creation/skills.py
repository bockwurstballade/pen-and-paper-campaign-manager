"""
Alles was mit Skills / Fertigkeiten 
und Fertigkeitskategorien (Handeln / Wissen / Soziales)
innerhalb des Charakter Erstellbildschirmes zu tun hat
"""
# imports
from PyQt6.QtWidgets import (
    QInputDialog, QMessageBox, QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QFormLayout
)
from utils.functions.math import kaufmaennisch_runden

class CharacterCreationDialogSkills:
    def __init__(self, dialog):
        """
        dialog: Referenz auf CharacterCreationDialog
        """
        self.dialog = dialog

    # -------------------------------------------------------------------------
    # Fähigkeit hinzufügen
    # -------------------------------------------------------------------------
    def add_skill(self, category):
        dialog = self.dialog

        skill_name, ok = QInputDialog.getText(dialog, f"Neue Fähigkeit für {category}", "Fähigkeitsname:")
        if not ok or not skill_name.strip():
            QMessageBox.warning(dialog, "Fehler", "Fähigkeitsname darf nicht leer sein.")
            return

        skill_name = skill_name.strip()
        if skill_name in dialog.skills[category]:
            QMessageBox.warning(dialog, "Fehler", f"Fähigkeit '{skill_name}' existiert bereits in {category}.")
            return

        # Fähigkeit hinzufügen
        dialog.skills[category].append(skill_name)
        dialog.skill_end_labels.setdefault(category, {})

        # Eingabefeld + Entfernen-Button + Endwert-Label
        input_field = QLineEdit()
        input_field.setPlaceholderText("0–100")
        input_field.textChanged.connect(self.update_points)

        end_label = QLabel("Endwert: 0")
        dialog.skill_end_labels[category][skill_name] = end_label

        remove_button = QPushButton("– Entfernen")
        remove_button.clicked.connect(lambda _, cat=category, skill=skill_name: self.remove_skill(cat, skill))

        # Layout der Zeile
        h_layout = QHBoxLayout()
        h_layout.addWidget(input_field)
        h_layout.addWidget(end_label)
        h_layout.addWidget(remove_button)

        dialog.skill_inputs[category][skill_name] = input_field
        dialog.form_layouts[category].addRow(f"{skill_name}:", h_layout)
        self.update_points()

    # -------------------------------------------------------------------------
    # Fähigkeit entfernen
    # -------------------------------------------------------------------------
    def remove_skill(self, category, skill_name):
        dialog = self.dialog

        if skill_name not in dialog.skills[category]:
            return

        dialog.skills[category].remove(skill_name)
        input_field = dialog.skill_inputs[category].pop(skill_name, None)
        if skill_name in dialog.skill_end_labels.get(category, {}):
            del dialog.skill_end_labels[category][skill_name]

        # Layoutzeile im FormLayout finden und entfernen
        form_layout = dialog.form_layouts[category]
        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if label_item and label_item.widget() and label_item.widget().text().startswith(skill_name):
                label_item.widget().deleteLater()
                if field_item:
                    field_widget = field_item.layout() or field_item.widget()
                    if field_widget:
                        while hasattr(field_widget, "count") and field_widget.count():
                            item = field_widget.takeAt(0)
                            if item.widget():
                                item.widget().deleteLater()
                        field_widget.deleteLater()
                form_layout.removeRow(i)
                break

        self.update_points()
        QMessageBox.information(dialog, "Erfolg", f"Fertigkeit '{skill_name}' wurde entfernt.")

    # -------------------------------------------------------------------------
    # Punkteberechnung
    # -------------------------------------------------------------------------
    def update_points(self):
        dialog = self.dialog
        try:
            total_used = 0
            for category in dialog.skills:
                category_sum = 0
                for skill, input_field in dialog.skill_inputs[category].items():
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
                dialog.category_labels[category].setText(f"{category}-Wert: {category_score}")

                # Geistesblitzpunkte berechnen
                inspiration_points = kaufmaennisch_runden(category_sum / 100)
                dialog.inspiration_labels[category].setText(f"Geistesblitzpunkte ({category}): {inspiration_points}")

                # Endwerte für Fähigkeiten aktualisieren
                for skill, input_field in dialog.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    end_value = val + category_score
                    if category in dialog.skill_end_labels and skill in dialog.skill_end_labels[category]:
                        dialog.skill_end_labels[category][skill].setText(f"Endwert: {end_value}")

                total_used += category_sum

            remaining = 400 - total_used
            dialog.total_points_label.setText(f"Verbleibende Punkte: {remaining}")

            if remaining < 0:
                raise ValueError("Gesamtpunkte überschreiten 400!")

            # Basiswerte für spätere Zustandsanwendung speichern
            for category in dialog.skills:
                # Kategorien & Inspirationen merken
                category_label_text = dialog.category_labels[category].text()
                cat_value = int(category_label_text.split(":")[-1].strip().split(" ")[0])
                dialog.base_values["Kategorien"][category] = cat_value

                insp_label_text = dialog.inspiration_labels[category].text()
                insp_value = int(insp_label_text.split(":")[-1].strip().split(" ")[0])
                dialog.base_values["Geistesblitzpunkte"][category] = insp_value

                # Skills merken
                for skill, input_field in dialog.skill_inputs[category].items():
                    try:
                        val = int(input_field.text()) if input_field.text() else 0
                    except ValueError:
                        val = 0
                    dialog.base_values["Fertigkeiten"][skill] = val

            # Endwertlabels aktualisieren
            self.update_endwert_labels()

        except ValueError as e:
            QMessageBox.warning(dialog, "Fehler", str(e))

    # -------------------------------------------------------------------------
    # Endwerte aktualisieren
    # -------------------------------------------------------------------------
    def update_endwert_labels(self):
        dialog = self.dialog
        for category in dialog.skills:
            # aktuellen Kategoriewert aus Label holen
            cat_label_text = dialog.category_labels[category].text()
            try:
                cat_current_value_str = cat_label_text.split(":")[1].strip().split(" ")[0]
                cat_current_value = int(cat_current_value_str)
            except Exception:
                cat_current_value = 0

            # Skills dieser Kategorie
            for skill, input_field in dialog.skill_inputs[category].items():
                try:
                    skill_val = int(input_field.text()) if input_field.text() else 0
                except ValueError:
                    skill_val = 0

                final_val = skill_val + cat_current_value
                if category in dialog.skill_end_labels and skill in dialog.skill_end_labels[category]:
                    dialog.skill_end_labels[category][skill].setText(f"Endwert: {final_val}")

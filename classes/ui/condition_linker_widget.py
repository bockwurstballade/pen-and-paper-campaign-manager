"""
Wiederverwendbares Widget zum Verknüpfen von Zuständen mit einem Item.
Wird sowohl im standalone ItemEditorDialog als auch potenziell in der
Charaktererstellung verwendet.
"""
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QInputDialog, QMessageBox
)

from classes.ui.condition_editor_dialog import ConditionEditorDialog
from classes.core.data_manager import DataManager
from classes.ui.ui_utils import style_groupbox


class ConditionLinkerWidget(QWidget):
    """
    Ein eigenständiges Widget, das eine Liste verknüpfter Zustands-UUIDs verwaltet.
    Bietet Buttons zum Hinzufügen (bestehend oder neu) und Entfernen von Zuständen
    sowie eine Textanzeige der verknüpften Zustände.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.linked_conditions: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.conditions_group = QGroupBox("Verknüpfte Zustände")
        style_groupbox(self.conditions_group)
        group_layout = QVBoxLayout()

        # Anzeige der verknüpften Zustände
        self.conditions_list_label = QLabel("Keine Zustände verknüpft.")
        group_layout.addWidget(self.conditions_list_label)

        # Buttons: bestehenden Zustand verknüpfen / neuen Zustand erstellen
        button_row = QHBoxLayout()

        add_existing_button = QPushButton("+ Bestehenden Zustand verknüpfen")
        add_existing_button.clicked.connect(self.add_existing_condition)
        button_row.addWidget(add_existing_button)

        create_new_button = QPushButton("+ Neuen Zustand erstellen")
        create_new_button.clicked.connect(self.create_new_condition)
        button_row.addWidget(create_new_button)

        group_layout.addLayout(button_row)

        # Entfernen-Button
        remove_button = QPushButton("– Zustand entfernen")
        remove_button.clicked.connect(self.remove_condition)
        group_layout.addWidget(remove_button)

        self.conditions_group.setLayout(group_layout)
        layout.addWidget(self.conditions_group)

    # --- Öffentliche API ---

    def get_linked_conditions(self) -> list[str]:
        """Gibt die aktuelle Liste der verknüpften Zustands-UUIDs zurück."""
        return list(self.linked_conditions)

    def set_linked_conditions(self, condition_ids: list[str]) -> None:
        """Setzt die Liste der verknüpften Zustands-UUIDs und aktualisiert die Anzeige."""
        self.linked_conditions = list(condition_ids)
        self._update_display()

    # --- Interne Methoden ---

    def _update_display(self) -> None:
        """Aktualisiert die Anzeige der verknüpften Zustände."""
        if not self.linked_conditions:
            self.conditions_list_label.setText("Keine Zustände verknüpft.")
            return

        conditions = DataManager.get_all_conditions()
        cond_map = {c["id"]: c for c in conditions}

        lines = []
        for cid in self.linked_conditions:
            cond = cond_map.get(cid)
            if cond:
                lines.append(f"{cond.get('name', '(unbenannt)')} ({cid[:8]}...)")
            else:
                lines.append(f"[Fehlend] {cid[:8]}...")

        self.conditions_list_label.setText("\n".join(lines))

    def add_existing_condition(self) -> None:
        """Lässt den Nutzer einen bestehenden Zustand auswählen und verknüpft ihn."""
        conditions = DataManager.get_all_conditions()

        if not conditions:
            QMessageBox.information(self, "Hinweis", "Es sind keine Zustände vorhanden.")
            return

        cond_names = [f"{c.get('name', '(unbenannt)')} [{c.get('id', '?')}]" for c in conditions]
        choice, ok = QInputDialog.getItem(
            self,
            "Zustand auswählen",
            "Welchen Zustand möchtest du verknüpfen?",
            cond_names,
            0,
            False
        )
        if not ok:
            return

        idx = cond_names.index(choice)
        selected = conditions[idx]
        cid = selected.get("id")

        if cid in self.linked_conditions:
            QMessageBox.information(self, "Hinweis", "Dieser Zustand ist bereits verknüpft.")
            return

        self.linked_conditions.append(cid)
        self._update_display()

    def create_new_condition(self) -> None:
        """Erstellt einen neuen Zustand und verknüpft ihn direkt."""
        dlg = ConditionEditorDialog(self)
        new_id = str(uuid.uuid4())
        dlg.condition_id = new_id
        dlg.exec()

        # Versuchen, den zuletzt gespeicherten Zustand zu verknüpfen
        try:
            conditions = DataManager.get_all_conditions()
            if conditions:
                # Suche gezielt nach der ID, die wir vergeben haben
                saved = next((c for c in conditions if c.get("id") == new_id), None)
                if saved and new_id not in self.linked_conditions:
                    self.linked_conditions.append(new_id)
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Konnte neuen Zustand nicht verknüpfen:\n{e}")

        self._update_display()

    def remove_condition(self) -> None:
        """Ermöglicht, eine bestehende Verknüpfung zu entfernen."""
        if not self.linked_conditions:
            QMessageBox.information(self, "Hinweis", "Dieses Item hat keine verknüpften Zustände.")
            return

        # Namen zu IDs auflösen, damit der User nicht nur UUIDs sieht
        conditions = DataManager.get_all_conditions()
        cond_map = {c["id"]: c for c in conditions}

        cond_choices = [
            cond_map[cid]["name"] if cid in cond_map else f"[Fehlend] {cid[:8]}..."
            for cid in self.linked_conditions
        ]

        choice, ok = QInputDialog.getItem(
            self,
            "Zustand entfernen",
            "Welchen Zustand möchtest du entfernen?",
            cond_choices,
            0,
            False
        )
        if not ok:
            return

        idx = cond_choices.index(choice)
        cid_to_remove = self.linked_conditions[idx]
        self.linked_conditions.remove(cid_to_remove)
        self._update_display()

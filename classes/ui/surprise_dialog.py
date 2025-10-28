# benötigte Imports

## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

class SurpriseDialog(QDialog):
    def __init__(self, battle_actors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Überraschungsrunde festlegen")
        self.setGeometry(350, 250, 500, 400)

        self.battle_actors = battle_actors
        self.checkboxes = {}
        self.team_checkboxes = {}

        layout = QVBoxLayout(self)

        # Finde alle Teams
        teams = sorted(set(a["team"] for a in battle_actors))

        for team_name in teams:
            group = QGroupBox(team_name)
            vbox = QVBoxLayout()

            # Team-Gesamt-Checkbox
            team_cb = QCheckBox(f"Gesamtes Team '{team_name}' überrascht")
            self.team_checkboxes[team_name] = team_cb
            vbox.addWidget(team_cb)

            # Einzelne Kämpfer dieses Teams
            for actor in [a for a in battle_actors if a["team"] == team_name]:
                cb = QCheckBox(actor["display_name"])
                self.checkboxes[actor["instance_id"]] = cb
                vbox.addWidget(cb)

            # Wenn Team angehakt → alle untergeordneten Kämpfer aktivieren
            def make_handler(tn=team_name):
                def handler(state):
                    checked = state == Qt.CheckState.Checked.value
                    for aid, cb in self.checkboxes.items():
                        for a in self.battle_actors:
                            if a["instance_id"] == aid and a["team"] == tn:
                                cb.setChecked(checked)
                return handler

            team_cb.stateChanged.connect(make_handler())

            group.setLayout(vbox)
            layout.addWidget(group)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def get_surprised_ids(self):
        """Gibt Menge von instance_ids zurück, die überrascht sind"""
        return {aid for aid, cb in self.checkboxes.items() if cb.isChecked()}
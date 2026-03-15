from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton
)

class CombatActorListWidget(QWidget):
    def __init__(self, main_dialog, parent=None):
        super().__init__(parent)
        self.main_dialog = main_dialog

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.layout.addWidget(QLabel("Teilnehmer im Kampf:"))
        
        # Container for the actual list
        self.actors_layout = QVBoxLayout()
        self.layout.addLayout(self.actors_layout)
        self.layout.addStretch()

    def refresh_actor_list(self):
        # Erstmal alles leerräumen
        while self.actors_layout.count():
            item = self.actors_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Für jede Instanz einen kleinen Block bauen
        for actor in self.main_dialog.combat_manager.battle_actors:
            box = QGroupBox(f"{actor['display_name']} ({actor['team']})")
            box.setStyleSheet("QGroupBox { font-weight:bold; }")
            v = QVBoxLayout()

            hp_label = QLabel(f"HP: {actor['current_hp']}/{actor['max_hp']}")
            v.addWidget(hp_label)

            # Buttons für HP +/- und Entfernen
            btn_row = QHBoxLayout()

            minus_btn = QPushButton("-1 HP")
            plus_btn = QPushButton("+1 HP")
            remove_btn = QPushButton("Entfernen")

            # Hilfsfunktionen binden Variablen
            def make_minus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = max(0, a["current_hp"] - 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_plus(a=actor, l=hp_label):
                def _inner():
                    a["current_hp"] = min(a["max_hp"], a["current_hp"] + 1)
                    l.setText(f"HP: {a['current_hp']}/{a['max_hp']}")
                return _inner

            def make_remove(a=actor):
                def _inner():
                    self.main_dialog.combat_manager.remove_combatant(a["instance_id"])
                    self.refresh_actor_list()
                return _inner

            minus_btn.clicked.connect(make_minus())
            plus_btn.clicked.connect(make_plus())
            remove_btn.clicked.connect(make_remove())

            btn_row.addWidget(minus_btn)
            btn_row.addWidget(plus_btn)
            btn_row.addWidget(remove_btn)

            v.addLayout(btn_row)
            box.setLayout(v)
            self.actors_layout.addWidget(box)

"""
Wiederverwendbares Widget für Waffen-Status: Kammern, Magazin, Projektile.
Wird in Charaktererstellung und Item-Editor verwendet.
- Schusswaffe: Kammern (max/geladen), Magazin (eingelegt, Kapazität, Füllstand)
- Natural/Explosivwaffe: Projektile geladen, Projektil-Typ
"""
from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QCheckBox,
    QLineEdit,
    QSpinBox,
    QGroupBox,
)


# Kategorien, für die Munition/Magazin sichtbar sind (nur Schusswaffe)
SCHUSSWAFFE = "Schusswaffe"
# Kategorien für Projektil-Felder (Bogen, Armbrust, Schleuder, etc.)
PROJEKTIL_KATEGORIEN = ("Natural", "Explosivwaffe")


def default_weapon_state():
    """Leerer Waffen-Status-Dict, konsistent mit dem erwarteten Schema."""
    return {
        "chambers": 0,
        "chambers_capacity": 0,
        "magazine": {
            "inserted": False,
            "count": 0,
            "capacity": 0,
        },
        "projectiles_loaded": 0,
        "projectile_type": "",
    }


class WeaponStateWidget(QWidget):
    """
    Modulares Widget für Waffen-Status.
    - Kammern (max) / Kammern geladen: z. B. 1 für Pistole/ Armbrust, 2 für Schrotflinte
    - Magazin: eingelegt, Kapazität, aktueller Füllstand (nur bei Schusswaffe sichtbar/befüllbar)
    - Projektile: geladen, Typ (nur bei Natural/Explosivwaffe sichtbar)
    """

    def __init__(self, parent=None, title="Waffen-Status"):
        super().__init__(parent)
        self._build_ui(title)

    def _build_ui(self, title):
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.group = QGroupBox(title)
        form = QFormLayout()

        # --- Schusswaffe: Kammern & Magazin ---
        self.chambers_capacity_spin = QSpinBox()
        self.chambers_capacity_spin.setRange(0, 10)
        self.chambers_loaded_spin = QSpinBox()
        self.chambers_loaded_spin.setRange(0, 10)

        self.magazine_inserted_cb = QCheckBox("Magazin eingelegt")
        self.magazine_capacity_spin = QSpinBox()
        self.magazine_capacity_spin.setRange(0, 200)
        self.magazine_count_spin = QSpinBox()
        self.magazine_count_spin.setRange(0, 200)

        form.addRow("Kammern (max):", self.chambers_capacity_spin)
        form.addRow("Kammern geladen:", self.chambers_loaded_spin)
        form.addRow(self.magazine_inserted_cb)
        form.addRow("Magazin Kapazität:", self.magazine_capacity_spin)
        form.addRow("Magazin aktuell:", self.magazine_count_spin)

        # --- Projektile (Bogen, Armbrust, Schleuder) ---
        self.projectiles_loaded_spin = QSpinBox()
        self.projectiles_loaded_spin.setRange(0, 10)
        self.projectile_type_input = QLineEdit()
        self.projectile_type_input.setPlaceholderText("z. B. Pfeil, Kugel …")

        form.addRow("Proj. geladen:", self.projectiles_loaded_spin)
        form.addRow("Proj. Typ:", self.projectile_type_input)

        self._schusswaffe_widgets = (
            self.chambers_capacity_spin,
            self.chambers_loaded_spin,
            self.magazine_inserted_cb,
            self.magazine_capacity_spin,
            self.magazine_count_spin,
        )
        self._projektil_widgets = (
            self.projectiles_loaded_spin,
            self.projectile_type_input,
        )

        # Alle initial ausblenden; Sichtbarkeit steuert update_visibility(weapon_category)
        for w in self._schusswaffe_widgets + self._projektil_widgets:
            w.setVisible(False)

        self.group.setLayout(form)
        layout.addWidget(self.group)

    def update_visibility(self, weapon_category):
        """
        Zeigt nur die passenden Felder zur Waffenkategorie.
        - Schusswaffe: Kammern und Magazin (Munition/Magazin nur hier befüllbar).
        - Natural / Explosivwaffe: Projektile geladen, Projektil-Typ.
        - Sonstige Kategorien: alle Waffen-Status-Felder ausgeblendet.
        """
        for w in self._schusswaffe_widgets + self._projektil_widgets:
            w.setVisible(False)

        if weapon_category == SCHUSSWAFFE:
            for w in self._schusswaffe_widgets:
                w.setVisible(True)
        elif weapon_category in PROJEKTIL_KATEGORIEN:
            for w in self._projektil_widgets:
                w.setVisible(True)

    def get_state(self):
        """Liefert den aktuellen Waffen-Status als Dict (für JSON/Speicherung)."""
        return {
            "chambers": self.chambers_loaded_spin.value(),
            "chambers_capacity": self.chambers_capacity_spin.value(),
            "magazine": {
                "inserted": self.magazine_inserted_cb.isChecked(),
                "count": self.magazine_count_spin.value(),
                "capacity": self.magazine_capacity_spin.value(),
            },
            "projectiles_loaded": self.projectiles_loaded_spin.value(),
            "projectile_type": self.projectile_type_input.text().strip(),
        }

    def set_state(self, state):
        """Setzt die Felder aus einem weapon_state-Dict (z. B. beim Laden)."""
        if not state:
            state = default_weapon_state()
        self.chambers_loaded_spin.setValue(state.get("chambers", 0))
        self.chambers_capacity_spin.setValue(state.get("chambers_capacity", 0))
        mag = state.get("magazine", {})
        self.magazine_inserted_cb.setChecked(mag.get("inserted", False))
        self.magazine_capacity_spin.setValue(mag.get("capacity", 0))
        self.magazine_count_spin.setValue(mag.get("count", 0))
        self.projectiles_loaded_spin.setValue(state.get("projectiles_loaded", 0))
        self.projectile_type_input.setText(state.get("projectile_type", ""))

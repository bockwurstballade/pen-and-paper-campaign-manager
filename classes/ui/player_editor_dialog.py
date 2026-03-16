import uuid
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

from classes.core.data_manager import DataManager


class PlayerEditorDialog(QDialog):
    """
    Einfache Maske zum Erstellen und Bearbeiten von Spielern.
    Spieler werden als separate JSON-Dateien unter data/players gespeichert.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Spieler bearbeiten / erstellen")
        self.setGeometry(250, 250, 400, 250)

        self.loaded_file: Optional[str] = None
        self.player_id: Optional[str] = None

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.nickname_input = QLineEdit()
        self.discord_input = QLineEdit()
        self.roll20_input = QLineEdit()

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Nickname:", self.nickname_input)
        form_layout.addRow("Discord:", self.discord_input)
        form_layout.addRow("Roll20:", self.roll20_input)

        main_layout.addLayout(form_layout)

        save_button = QPushButton("Spieler speichern")
        save_button.clicked.connect(self.save_player)
        main_layout.addWidget(save_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_player_data(self, player_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
        """
        Lädt einen bestehenden Spieler in den Dialog.
        """
        self.loaded_file = file_path
        self.player_id = player_data.get("id", str(uuid.uuid4()))

        self.name_input.setText(player_data.get("name", ""))
        self.nickname_input.setText(player_data.get("nickname", ""))
        self.discord_input.setText(player_data.get("discord", ""))
        self.roll20_input.setText(player_data.get("roll20", ""))

    def save_player(self) -> None:
        """
        Validiert die Eingaben und speichert den Spieler über den DataManager.
        """
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein.")
            return

        nickname = self.nickname_input.text().strip()
        discord = self.discord_input.text().strip()
        roll20 = self.roll20_input.text().strip()

        if not self.player_id:
            self.player_id = str(uuid.uuid4())

        player_obj: Dict[str, Any] = {
            "id": self.player_id,
            "name": name,
            "nickname": nickname,
            "discord": discord,
            "roll20": roll20,
        }

        try:
            DataManager.save_player(player_obj)
            QMessageBox.information(self, "Erfolg", f"Spieler '{name}' wurde gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Konnte Spieler nicht speichern:\n{e}")


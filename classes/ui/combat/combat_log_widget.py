from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class CombatLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Kampf-Log...")
        self.layout.addWidget(self.log_box)

    def log_message(self, text: str):
        """Fügt eine Nachricht in das Kampf-Log ein."""
        self.log_box.append(f"• {text}")

    def append(self, text: str):
        """Standard append Methode kompatibel halten."""
        self.log_box.append(text)

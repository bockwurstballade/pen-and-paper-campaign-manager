## Qt Frontend Technologie
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
class AttributeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Eigenschaft")
        self.setGeometry(200, 200, 300, 150)

        layout = QVBoxLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Attribut-Name")
        self.value_input = QLineEdit(self)
        self.value_input.setPlaceholderText("Attribut-Wert")
        layout.addWidget(QLabel("Attribut-Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Attribut-Wert:"))
        layout.addWidget(self.value_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Abbrechen", self)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def get_attribute(self):
        name = self.name_input.text().strip()
        value = self.value_input.text().strip()
        return name, value if name and value else (None, None)


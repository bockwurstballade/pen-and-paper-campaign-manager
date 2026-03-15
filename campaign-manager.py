import sys
import json
import os
import uuid
## Import everything to do with Qt (Frontend Technology)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QGroupBox,
    QInputDialog, QHBoxLayout, QFileDialog, QTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt

## Importieren eigener Funktionen
from utils.functions.math import kaufmaennisch_runden

## Importieren eigener Klassen
from classes.ui.welcome_window import WelcomeWindow # Startbildschirm

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())

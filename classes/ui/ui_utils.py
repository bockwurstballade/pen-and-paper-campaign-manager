"""
Gemeinsame UI-Hilfsfunktionen, die in verschiedenen Dialogen und Widgets
wiederverwendet werden.
"""
from PyQt6.QtWidgets import QGroupBox


def style_groupbox(box: QGroupBox) -> None:
    """Wendet das einheitliche GroupBox-Styling an."""
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

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog


class ImageSelectorWidget(QWidget):
    """
    Wiederverwendbares Widget:
    - Bild auswählen via File-Chooser
    - Vorschau (immer vollständig sichtbar, KeepAspectRatio)
    - Merkt sich:
      - selected_source_path (vom Client-PC)
      - current_filename (Dateiname im Entity-Ordner, wenn aus gespeicherten Daten geladen)
    """

    def __init__(
        self,
        parent=None,
        *,
        placeholder_text: str = "Kein Bild verfügbar.",
        button_text: str = "Bild auswählen …",
        min_height: int = 220,
    ):
        super().__init__(parent)

        self.placeholder_text = placeholder_text
        self.selected_source_path: Optional[str] = None
        self.current_filename: Optional[str] = None

        self._original_pixmap: Optional[QPixmap] = None
        self._last_target_size = None

        layout = QVBoxLayout(self)

        self.preview_label = QLabel("Kein Bild ausgewählt.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(min_height)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        self.preview_label.setWordWrap(True)
        self.preview_label.installEventFilter(self)

        self.select_button = QPushButton(button_text)
        self.select_button.clicked.connect(self.choose_image)

        layout.addWidget(self.preview_label)
        layout.addWidget(self.select_button)

    def _set_placeholder(self, text: Optional[str] = None) -> None:
        self._original_pixmap = None
        self._last_target_size = None
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText(text or self.placeholder_text)

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        self._original_pixmap = pixmap
        self._last_target_size = None
        self.preview_label.setText("")
        self._update_scaled_pixmap()
        QTimer.singleShot(0, self._update_scaled_pixmap)

    def _update_scaled_pixmap(self) -> None:
        if not self._original_pixmap:
            return
        size = self.preview_label.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        if self._last_target_size == size:
            return
        self._last_target_size = size
        scaled = self._original_pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def choose_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Bild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.webp)",
        )
        if not file_path:
            return

        self.selected_source_path = file_path
        self.current_filename = None  # bewusst überschreiben

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._set_placeholder("Bild konnte nicht geladen werden.")
            return
        self._set_pixmap(pixmap)

    def set_existing_image(self, *, folder_path: str, filename: Optional[str]) -> None:
        """
        Lädt ein bestehendes Bild aus einem Entity-Ordner (z. B. beim Laden eines Items).
        """
        self.selected_source_path = None
        self.current_filename = filename

        if not filename:
            self._set_placeholder()
            return

        image_path = os.path.join(folder_path, filename)
        if not os.path.exists(image_path):
            self._set_placeholder("Bilddatei nicht gefunden.")
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self._set_placeholder("Bild konnte nicht geladen werden.")
            return

        self._set_pixmap(pixmap)

    def clear(self) -> None:
        """Entfernt Auswahl/Referenz und zeigt Platzhalter."""
        self.selected_source_path = None
        self.current_filename = None
        self._set_placeholder()

    def eventFilter(self, obj, event):
        if obj is self.preview_label and event.type() == QEvent.Type.Resize:
            self._update_scaled_pixmap()
        return super().eventFilter(obj, event)


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
)

class CombatTurnWidget(QWidget):
    def __init__(self, main_dialog, parent=None):
        super().__init__(parent)
        self.main_dialog = main_dialog

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # We start with it hidden until initiative is set
        self.setVisible(False)

        self.current_turn_label = QLabel()
        self.layout.addWidget(self.current_turn_label)

        self.order_list_widget = QTextEdit()
        self.order_list_widget.setReadOnly(True)
        self.layout.addWidget(self.order_list_widget)

        # Buttons
        btns = QHBoxLayout()
        self.next_turn_btn = QPushButton("▶️ Nächster Zug")
        self.next_turn_btn.clicked.connect(self.next_turn)
        btns.addWidget(self.next_turn_btn)

        self.reset_round_btn = QPushButton("🔁 Neue Runde")
        self.reset_round_btn.clicked.connect(self.reset_round)
        btns.addWidget(self.reset_round_btn)

        self.action_btn = QPushButton("⚔️ Zug ausführen")
        self.action_btn.clicked.connect(self.run_current_turn)
        btns.addWidget(self.action_btn)

        self.layout.addLayout(btns)

    def show_turn_area(self):
        self.setVisible(True)

    def next_turn(self):
        manager = self.main_dialog.combat_manager
        new_round = manager.next_turn()
        if new_round:
            QMessageBox.information(self, "Neue Runde", f"Runde {manager.round_number} beginnt!")

        # Skip incapacitated
        while True:
            actor = manager.get_current_actor()
            if not actor:
                break
            
            skipped, reason = manager.check_and_skip_if_incapacitated()
            if skipped:
                self.main_dialog.log_message(reason)
                new_round = manager.next_turn()
                if new_round:
                    QMessageBox.information(self, "Neue Runde", f"Runde {manager.round_number} beginnt!")
            else:
                break

        self.refresh_turn_display()

    def reset_round(self):
        manager = self.main_dialog.combat_manager
        if not manager.turn_order:
            return
        
        manager.round_number = 1
        manager.current_turn_index = 0
        manager.round_damage = {}
        manager.parry_used = {}
        QMessageBox.information(self, "Runde zurückgesetzt", "Die Initiative startet wieder bei Runde 1.")
        self.refresh_turn_display()

    def run_current_turn(self):
        # Delegate to main dialog's action handler
        self.main_dialog.action_handler.run_current_turn()

    def refresh_turn_display(self):
        manager = self.main_dialog.combat_manager
        if not manager.turn_order:
            return

        current_actor = manager.get_current_actor()
        if not current_actor:
            return

        # Header
        self.current_turn_label.setText(
            f"<b>Runde {manager.round_number}</b><br>"
            f"<b>Aktuell am Zug:</b> {current_actor['display_name']} ({current_actor['team']})"
        )

        # Order Display
        text = ""
        for i, actor in enumerate(manager.turn_order, start=1):
            status_icon = ""
            status_style = ""
            skip_note = ""

            if actor.get("dead", False):
                status_icon = " [TOT]"
                status_style = 'style="color:red; font-weight:bold;"'
            elif actor.get("unconscious", False):
                status_icon = " [BEWUSSTLOS]"
                status_style = 'style="color:orange; font-style:italic;"'
                skip_note = " (setzt aus)" if not actor.get("dead", False) else ""
            elif actor["instance_id"] in manager.surprised_ids:
                status_icon = " [ÜBERRASCHT]"
                status_style = 'style="color:gray; font-style:italic;"'
                skip_note = " (setzt in Runde 1 aus)" if manager.round_number == 1 else ""
            else:
                status_style = ""

            prefix = " " if i - 1 == manager.current_turn_index else ""

            text += (
                f'{prefix}{i}. '
                f'<span {status_style}>{actor["display_name"]}{status_icon} ({actor["team"]}){skip_note}</span><br>'
            )

        self.order_list_widget.setHtml(text)

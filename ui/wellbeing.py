"""Offline English WHO-5 well-being check dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


WHO5_URL = "https://www.who.int/publications/m/item/who-ucn-msd-mhe-2024.01"
WHO5_FOLLOW_UP_SCORE = 50
_OPTIONS = (
    "All of the time",
    "Most of the time",
    "More than half of the time",
    "Less than half of the time",
    "Some of the time",
    "At no time",
)
_ITEMS = (
    "I have felt cheerful and in good spirits",
    "I have felt calm and relaxed",
    "I have felt active and vigorous",
    "I woke up feeling fresh and rested",
    "My daily life has been filled with things that interest me",
)


class WellbeingDialog(QDialog):
    """Collect all five WHO-5 answers and expose a score from 0 to 100."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Well-Being Check")
        self.setMinimumSize(760, 620)
        self.resize(900, 700)
        self._groups = []
        self._score = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        intro = QLabel(
            "WHO-5 Well-Being Check"
        )
        intro.setObjectName("wellbeingTitle")
        layout.addWidget(intro)

        instructions = QLabel(
            "Over the last two weeks, select one answer for each statement. "
            "All five questions are required."
        )
        instructions.setObjectName("wellbeingInstructions")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName("wellbeingScroll")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 12, 2)
        content_layout.setSpacing(12)

        for number, item in enumerate(_ITEMS, start=1):
            card = QGroupBox(f"{number}. {item}")
            card.setObjectName("wellbeingQuestion")
            options_layout = QGridLayout(card)
            options_layout.setContentsMargins(16, 20, 16, 12)
            options_layout.setHorizontalSpacing(28)
            options_layout.setVerticalSpacing(8)
            group = QButtonGroup(card)
            group.setExclusive(True)
            buttons = []
            for value, label in enumerate(_OPTIONS):
                button = QRadioButton(label)
                button.setProperty("scoreValue", value)
                button.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                group.addButton(button, value)
                buttons.append(button)
            for index, button in enumerate(buttons):
                options_layout.addWidget(button, index // 2, index % 2)
            self._groups.append(group)
            content_layout.addWidget(card)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setObjectName("wellbeingActions")
        buttons.accepted.connect(self._accept_if_complete)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #0B0E14;
            }
            QLabel#wellbeingTitle {
                color: #E8EEF6;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#wellbeingInstructions {
                color: #8A99AD;
                font-size: 12px;
            }
            QScrollArea#wellbeingScroll {
                background-color: #0B0E14;
            }
            QGroupBox#wellbeingQuestion {
                color: #E8EEF6;
                background-color: #131822;
                border: 1px solid #1F293D;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: 600;
            }
            QGroupBox#wellbeingQuestion::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QRadioButton {
                color: #E8EEF6;
                spacing: 8px;
                padding: 5px 2px;
            }
            QRadioButton:hover {
                color: #00F0FF;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:unchecked {
                border: 1px solid #8A99AD;
                border-radius: 8px;
                background-color: #0B0E14;
            }
            QRadioButton::indicator:checked {
                border: 4px solid #00F0FF;
                border-radius: 8px;
                background-color: #0B0E14;
            }
            QDialogButtonBox QPushButton {
                min-width: 100px;
                padding: 8px 16px;
            }
            """
        )

    def _accept_if_complete(self) -> None:
        if not all(group.checkedButton() is not None for group in self._groups):
            QMessageBox.warning(
                self,
                "Incomplete check",
                "Please answer all five questions before continuing.",
            )
            return
        self._score = sum(
            group.id(group.checkedButton()) for group in self._groups
        ) * 4
        self.accept()

    def score(self) -> int:
        return self._score

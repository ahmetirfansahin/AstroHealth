"""Offline English WHO-5 well-being check dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
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
        self._groups = []
        self._score = 0

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Over the last two weeks, how much of the time have you felt this way?"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        for number, item in enumerate(_ITEMS, start=1):
            layout.addWidget(QLabel(f"{number}. {item}"))
            group = []
            for value, label in enumerate(_OPTIONS):
                button = QRadioButton(f"{value}: {label}")
                group.append(button)
                layout.addWidget(button)
            self._groups.append(group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_complete)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept_if_complete(self) -> None:
        if not all(any(button.isChecked() for button in group) for group in self._groups):
            QMessageBox.warning(
                self,
                "Incomplete check",
                "Please answer all five questions before continuing.",
            )
            return
        self._score = sum(
            next(value for value, button in enumerate(group) if button.isChecked())
            for group in self._groups
        ) * 4
        self.accept()

    def score(self) -> int:
        return self._score

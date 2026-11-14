"""AstroHealth offline crew health dashboard entry point."""

from __future__ import annotations

import sys
import sqlite3
from pathlib import Path

from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.database import TelemetryDatabase
from ui.dashboard import DashboardWindow


def main() -> int:
    """Initialize local storage and start the dashboard event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("AstroHealth")
    app.setOrganizationName("AstroHealth")
    app.setFont(QFont("Segoe UI", 10))
    app_icon = QIcon(str(Path(__file__).resolve().parent / "images" / "logo.png"))
    app.setWindowIcon(app_icon)

    database_path = Path.home() / ".astrohealth" / "astrohealth.sqlite3"
    try:
        database = TelemetryDatabase(database_path)
    except (OSError, sqlite3.Error) as error:
        QMessageBox.critical(
            None,
            "AstroHealth startup failed",
            f"Could not initialize the local health database at "
            f"{database_path}.\n\n{error}",
        )
        return 1

    window = DashboardWindow(database)
    window.setWindowIcon(app_icon)
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

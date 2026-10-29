"""Dark, mission-oriented PyQt6 telemetry dashboard."""

from __future__ import annotations

import sqlite3
import time
from collections import deque
from datetime import datetime
from html import escape
from importlib.metadata import version
from pathlib import Path

import pyqtgraph as pg
from PyQt6.QtCore import QObject, QUrl, Qt, QTimer, qVersion
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from core.anomaly_engine import Anomaly, AnomalyEngine, Severity
from core.database import TelemetryDatabase
from core.simulator import TelemetrySample, TelemetrySimulator


COLORS = {
    "background": "#0B0E14",
    "surface": "#131822",
    "border": "#1F293D",
    "cyan": "#00F0FF",
    "normal": "#00FF87",
    "warning": "#FFB800",
    "critical": "#FF2A6D",
    "muted": "#8A99AD",
    "text": "#E8EEF6",
}

_SEVERITY_COLORS = {
    Severity.NORMAL: COLORS["normal"],
    Severity.WARNING: COLORS["warning"],
    Severity.CRITICAL: COLORS["critical"],
}

_METRICS = (
    ("heart_rate", "HEART RATE", "bpm", "{:.0f}"),
    ("spo2", "BLOOD OXYGEN", "% SpO2", "{:.1f}"),
    ("body_temperature", "BODY TEMPERATURE", "°C", "{:.2f}"),
    ("radiation", "RADIATION", "mSv/h", "{:.3f}"),
    ("hrv", "HEART RATE VARIABILITY", "ms HRV", "{:.0f}"),
)

_METRIC_NORMALS = {
    "heart_rate": "Configured range 60-100 bpm",
    "spo2": "Configured range 95-99%",
    "body_temperature": "Configured range 36.5-37.5 °C",
    "radiation": "Configured range 0.05-0.20 mSv/h",
    "hrv": "Configured range 40-70 ms",
}


class MetricCard(QFrame):
    """A compact, explicitly labeled telemetry reading."""

    def __init__(self, title: str, unit: str, normal_range: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(144)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.title = QLabel(title)
        self.title.setObjectName("metricTitle")
        self.title.setWordWrap(True)

        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        self.value = QLabel("--")
        self.value.setObjectName("metricValue")
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.unit = QLabel(unit)
        self.unit.setObjectName("metricUnit")
        self.unit.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        value_row.addWidget(self.value, 0, Qt.AlignmentFlag.AlignLeft)
        value_row.addWidget(self.unit, 0, Qt.AlignmentFlag.AlignLeft)
        value_row.addStretch(1)

        self.range = QLabel(normal_range)
        self.range.setObjectName("metricRange")
        self.range.setWordWrap(True)
        self.status = QLabel("AWAITING DATA")
        self.status.setObjectName("metricStatus")
        self.status.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addLayout(value_row)
        layout.addWidget(self.range)
        layout.addStretch(1)
        layout.addWidget(self.status)

    def set_reading(self, value: str, severity: Severity, description: str) -> None:
        self.value.setText(value)
        color = _SEVERITY_COLORS[severity]
        self.status.setText(description)
        self.status.setStyleSheet(f"color: {color};")
        self.value.setStyleSheet(f"color: {color if severity else COLORS['text']};")


class DashboardWindow(QMainWindow):
    """Connect simulator signals to the dashboard and offline SQLite log."""

    def __init__(
        self,
        database: TelemetryDatabase,
        simulator: TelemetrySimulator | None = None,
    ) -> None:
        super().__init__()
        self._database = database
        self._simulator = simulator or TelemetrySimulator(parent=self)
        self._engine = AnomalyEngine()
        self._active_incidents: dict[str, tuple[Anomaly, int]] = {}
        self._history: dict[str, deque[float]] = {
            metric: deque(maxlen=300) for metric, _, _, _ in _METRICS
        }
        self._elapsed_start = time.monotonic()
        self._storage_error_reported = False
        self._cards: dict[str, MetricCard] = {}
        self._curves: dict[str, pg.PlotDataItem] = {}

        self.setWindowTitle("AstroHealth")
        self.setMinimumSize(1080, 720)
        self.resize(1520, 980)
        self.setStyleSheet(self._stylesheet())

        self._build_ui()
        self._simulator.sample_ready.connect(self._handle_sample)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_mission_clock)
        self._clock_timer.start(1000)
        self._simulator.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop the worker before closing its parent dashboard."""
        self._clock_timer.stop()
        if self._simulator.isRunning():
            self._simulator.stop()
            if not self._simulator.wait(3000):
                QMessageBox.warning(
                    self,
                    "Telemetry still stopping",
                    "The telemetry worker did not stop in time. "
                    "Please close the dashboard again after it stops.",
                )
                event.ignore()
                return
        self._database.close()
        event.accept()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("dashboardScroll")
        self.setCentralWidget(scroll)

        page = QWidget()
        page.setObjectName("dashboardPage")
        scroll.setWidget(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = self._build_header()
        layout.addWidget(header)

        self._storage_banner = QLabel()
        self._storage_banner.setObjectName("storageBanner")
        self._storage_banner.setWordWrap(True)
        self._storage_banner.hide()
        layout.addWidget(self._storage_banner)

        section_header = self._section_heading(
            "Crew health", "LIVE SIMULATION · ONE-SECOND TELEMETRY"
        )
        layout.addWidget(section_header)

        metrics = QGridLayout()
        metrics.setSpacing(8)
        for column, (key, title, unit, _) in enumerate(_METRICS):
            card = MetricCard(title, unit, _METRIC_NORMALS[key])
            self._cards[key] = card
            metrics.addWidget(card, 0, column)
        layout.addLayout(metrics)

        chart_heading = self._section_heading(
            "Physiological and environment trends", "ROLLING WINDOW · 5 MIN"
        )
        layout.addWidget(chart_heading)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(16)
        self._heart_chart = self._create_chart(
            "Heart rate",
            "Heart rate",
            "beats per minute",
            COLORS["cyan"],
            ((100, COLORS["warning"]), (140, COLORS["critical"])),
        )
        self._radiation_chart = self._create_chart(
            "Ambient radiation",
            "Radiation exposure",
            "mSv/h",
            COLORS["warning"],
            ((0.20, COLORS["warning"]), (1.50, COLORS["critical"])),
        )
        chart_row.addWidget(self._heart_chart, 1)
        chart_row.addWidget(self._radiation_chart, 1)
        layout.addLayout(chart_row)

        lower = QHBoxLayout()
        lower.setSpacing(16)
        self._build_alert_console(lower)
        self._build_controls(lower)
        layout.addLayout(lower)

        disclaimer = QLabel(
            "SIMULATED DATA ONLY · Demonstration thresholds are configurable "
            "examples, not validated medical or mission guidance."
        )
        disclaimer.setObjectName("disclaimer")
        disclaimer.setWordWrap(True)
        layout.addWidget(disclaimer)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerPanel")
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 16, 20, 16)
        row.setSpacing(16)

        brand = QVBoxLayout()
        brand.setSpacing(4)
        title = QLabel("AstroHealth")
        title.setObjectName("appTitle")
        subtitle = QLabel("CREW HEALTH WATCH")
        subtitle.setObjectName("headerSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)

        mission = QVBoxLayout()
        mission.setSpacing(4)
        mission_label = QLabel("MISSION ELAPSED")
        mission_label.setObjectName("headerMeta")
        self._mission_clock = QLabel("T+ 00:00:00")
        self._mission_clock.setObjectName("missionClock")
        mission.addWidget(mission_label)
        mission.addWidget(self._mission_clock)

        self._overall_status = QLabel("AWAITING TELEMETRY")
        self._overall_status.setObjectName("overallStatus")
        self._set_overall_status(Severity.NORMAL, "AWAITING TELEMETRY")

        about_button = QPushButton("About")
        about_button.setObjectName("button_about")
        about_button.setAccessibleName("About AstroHealth and third-party licenses")
        about_button.setToolTip("Application information and software attributions")
        about_button.setMinimumHeight(40)
        about_button.clicked.connect(self._show_about)

        row.addLayout(brand, 1)
        row.addLayout(mission, 0)
        row.addWidget(self._overall_status, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(about_button, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _show_about(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("About AstroHealth")
        dialog.setObjectName("aboutDialog")
        dialog.setMinimumSize(620, 520)
        dialog.resize(700, 600)
        dialog.setStyleSheet(
            self._stylesheet()
            + f"QDialog#aboutDialog {{ background-color: {COLORS['background']}; }}"
        )

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("AstroHealth")
        title.setObjectName("appTitle")
        summary = QLabel(
            "Offline-first crew-health monitoring demonstration"
            " · NASA Space Apps Challenge"
        )
        summary.setObjectName("headerSubtitle")
        summary.setWordWrap(True)

        credits = QTextBrowser()
        credits.setObjectName("aboutCredits")
        credits.setOpenExternalLinks(True)
        credits.setReadOnly(True)
        credits.setHtml(self._about_credits_html())

        actions = QHBoxLayout()
        notices_button = QPushButton("Open full license notices")
        notices_button.setObjectName("button_about")
        notices_button.clicked.connect(self._open_third_party_notices)
        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_buttons.rejected.connect(dialog.reject)
        actions.addWidget(notices_button)
        actions.addStretch(1)
        actions.addWidget(close_buttons)

        layout.addWidget(title)
        layout.addWidget(summary)
        layout.addWidget(credits, 1)
        layout.addLayout(actions)
        dialog.exec()

    @staticmethod
    def _about_credits_html() -> str:
        pyqt_version = escape(version("PyQt6"))
        qt_version = escape(qVersion())
        sip_version = escape(version("PyQt6-sip"))
        pyqtgraph_version = escape(version("pyqtgraph"))
        numpy_version = escape(version("numpy"))
        return f"""
            <html>
            <head>
              <style>
                body {{ color: {COLORS["text"]}; font-family: "Segoe UI", sans-serif; }}
                h3 {{ color: {COLORS["text"]}; }}
                a {{ color: {COLORS["cyan"]}; }}
                code {{ color: {COLORS["cyan"]}; }}
              </style>
            </head>
            <body style="color: {COLORS["text"]}; font-family: Segoe UI, sans-serif;">
              <p>This project is distributed under
                <b>GNU GPL version 3 only (GPL-3.0-only)</b>.
                The complete license is included as <code>LICENSE</code>.</p>
              <h3>Third-party software</h3>
              <p><b>PyQt6 {pyqt_version}</b> — Riverbank Computing Limited;
                GPL-3.0-only.
                <a href="https://www.riverbankcomputing.com/software/pyqt/">
                Project and license information</a>.</p>
              <p><b>Qt {qt_version}</b> — The Qt Company Ltd and contributors;
                LGPL version 3.
                <a href="https://doc.qt.io/qt-6/licensing.html">
                Qt license information</a>.</p>
              <p><b>PyQt6-sip {sip_version}</b> — Phil Thompson;
                BSD 2-Clause license.
                <a href="https://riverbankcomputing.com/software/sip/">
                Project information</a>.</p>
              <p><b>PyQtGraph {pyqtgraph_version}</b> — copyright © 2012
                University of North Carolina at Chapel Hill and Luke Campagnola;
                MIT license.
                <a href="https://github.com/pyqtgraph/pyqtgraph">
                Source and license</a>.</p>
              <p><b>NumPy {numpy_version}</b> — NumPy Developers;
                BSD 3-Clause license.
                <a href="https://numpy.org/doc/stable/license.html">
                License and bundled-component notices</a>.
                Binary distributions may include separately licensed
                components; see the full notices.</p>
              <h3>Project scope</h3>
              <p>AstroHealth is being developed for the NASA Space Apps
                Challenge. The current telemetry stream is synthetic. NASA
                datasets and their source attributions will be documented
                when those datasets are integrated. This application does not
                provide validated medical guidance.</p>
            </body>
            </html>
        """

    def _open_third_party_notices(self) -> None:
        notices_path = Path(__file__).resolve().parents[1] / "THIRD_PARTY_NOTICES.md"
        if not notices_path.is_file():
            QMessageBox.warning(
                self,
                "License notices unavailable",
                f"The third-party notices file could not be found:\n{notices_path}",
            )
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(notices_path))):
            QMessageBox.warning(
                self,
                "Could not open license notices",
                f"Open this file to view the full third-party notices:\n{notices_path}",
            )

    def _section_heading(self, title: str, detail: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 8, 0, 0)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        detail_label = QLabel(detail)
        detail_label.setObjectName("sectionDetail")
        detail_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(detail_label)
        return row

    def _create_chart(
        self,
        title: str,
        axis_name: str,
        units: str,
        line_color: str,
        thresholds: tuple[tuple[float, str], ...],
    ) -> QFrame:
        panel = QFrame()
        panel.setObjectName("chartPanel")
        panel.setMinimumHeight(268)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(8)

        heading = QLabel(title)
        heading.setObjectName("chartTitle")
        plot = pg.PlotWidget()
        plot.setBackground(COLORS["surface"])
        plot.setAntialiasing(True)
        plot.showGrid(x=True, y=True, alpha=0.16)
        plot.setLabel("left", axis_name, units=units, color=COLORS["muted"])
        plot.setLabel("bottom", "Seconds from now", color=COLORS["muted"])
        plot.getAxis("left").setTextPen(COLORS["muted"])
        plot.getAxis("bottom").setTextPen(COLORS["muted"])
        plot.getAxis("left").setPen(COLORS["border"])
        plot.getAxis("bottom").setPen(COLORS["border"])
        plot.setXRange(-300, 0, padding=0)
        plot.setLimits(xMin=-300, xMax=0)
        plot.setMouseEnabled(x=False, y=False)
        plot.setMenuEnabled(False)
        plot.getPlotItem().setContentsMargins(8, 4, 8, 4)

        curve = plot.plot(
            [],
            [],
            pen=pg.mkPen(color=line_color, width=2),
            antialias=True,
        )
        for value, color in thresholds:
            threshold_line = pg.InfiniteLine(
                pos=value,
                angle=0,
                pen=pg.mkPen(color=color, width=1, style=Qt.PenStyle.DashLine),
            )
            plot.addItem(threshold_line)
        self._curves[axis_name] = curve

        layout.addWidget(heading)
        layout.addWidget(plot, 1)
        return panel

    def _build_alert_console(self, parent_layout: QHBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setMinimumHeight(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        heading = QLabel("Anomaly incident log")
        heading.setObjectName("chartTitle")
        self._incident_count = QLabel("0 ACTIVE")
        self._incident_count.setObjectName("sectionDetail")
        header.addWidget(heading)
        header.addStretch(1)
        header.addWidget(self._incident_count)

        self._alert_console = QTextEdit()
        self._alert_console.setObjectName("alertConsole")
        self._alert_console.setReadOnly(True)
        self._alert_console.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._alert_console.document().setMaximumBlockCount(400)
        self._alert_console.setPlaceholderText(
            "Telemetry status changes and active incidents appear here."
        )
        layout.addLayout(header)
        layout.addWidget(self._alert_console, 1)
        parent_layout.addWidget(panel, 7)

    def _build_controls(self, parent_layout: QHBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setMinimumWidth(300)
        panel.setMinimumHeight(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        heading = QLabel("Scenario controls")
        heading.setObjectName("chartTitle")
        detail = QLabel("SYNTHETIC EVENTS · AUTO-RESET 20-30 S")
        detail.setObjectName("sectionDetail")

        actions = QGridLayout()
        actions.setSpacing(8)
        buttons = (
            ("Trigger hypoxia", self._simulator.trigger_hypoxia_event, "critical"),
            (
                "Radiation spike",
                self._simulator.trigger_radiation_spike,
                "warning",
            ),
            ("Trigger fever", self._simulator.trigger_fever_event, "warning"),
            ("Recovery", self._simulator.trigger_recovery, "neutral"),
        )
        for index, (text, callback, variant) in enumerate(buttons):
            button = QPushButton(text)
            button.setObjectName(f"button_{variant}")
            button.setMinimumHeight(40)
            button.clicked.connect(callback)
            actions.addWidget(button, index // 2, index % 2)

        export_button = QPushButton("Export mission health log")
        export_button.setObjectName("button_primary")
        export_button.setMinimumHeight(44)
        export_button.clicked.connect(self._export_report)

        layout.addWidget(heading)
        layout.addWidget(detail)
        layout.addLayout(actions)
        layout.addStretch(1)
        layout.addWidget(export_button)
        parent_layout.addWidget(panel, 4)

    def _handle_sample(self, payload: object) -> None:
        if not isinstance(payload, TelemetrySample):
            self._append_log("ERROR: Received an invalid telemetry payload.")
            return

        sample = payload
        anomalies = self._engine.evaluate(sample)
        overall = max(
            (anomaly.severity for anomaly in anomalies), default=Severity.NORMAL
        )
        active = {anomaly.metric: anomaly for anomaly in anomalies}

        for metric, (previous, incident_id) in tuple(self._active_incidents.items()):
            current = active.get(metric)
            if current is None or current.severity != previous.severity:
                try:
                    self._database.resolve_incident(incident_id, sample.timestamp)
                    self._append_log(
                        f"RESOLVED: {previous.metric.replace('_', ' ')}",
                        timestamp=sample.timestamp,
                    )
                except (OSError, sqlite3.Error) as error:
                    self._report_storage_error(error)
                del self._active_incidents[metric]

        for anomaly in anomalies:
            existing = self._active_incidents.get(anomaly.metric)
            if existing is None or existing[0] != anomaly:
                try:
                    incident_id = self._database.open_incident(
                        anomaly, sample.timestamp
                    )
                    self._active_incidents[anomaly.metric] = (
                        anomaly,
                        incident_id,
                    )
                    self._append_log(
                        anomaly.message, anomaly.severity, sample.timestamp
                    )
                except (OSError, sqlite3.Error) as error:
                    self._report_storage_error(error)

        for key, _, _, value_format in _METRICS:
            card_severity = next(
                (
                    anomaly.severity
                    for anomaly in anomalies
                    if anomaly.metric == key
                ),
                Severity.NORMAL,
            )
            display_value = value_format.format(getattr(sample, key))
            description = card_severity.name
            self._cards[key].set_reading(display_value, card_severity, description)
            self._history[key].append(getattr(sample, key))

        self._update_charts()
        self._set_overall_status(overall, f"CREW STATUS · {overall.name}")
        self._incident_count.setText(f"{len(anomalies)} ACTIVE")
        self._incident_count.setStyleSheet(
            f"color: {_SEVERITY_COLORS[overall]};"
        )

        try:
            self._database.record_sample(sample, overall)
            self._storage_error_reported = False
            self._storage_banner.hide()
        except (OSError, sqlite3.Error) as error:
            self._report_storage_error(error)

    def _update_charts(self) -> None:
        for key, series in (
            ("heart_rate", self._history["heart_rate"]),
            ("radiation", self._history["radiation"]),
        ):
            points = tuple(series)
            x_values = range(-len(points) + 1, 1)
            self._curves[
                "Heart rate" if key == "heart_rate" else "Radiation exposure"
            ].setData(x_values, points)

    def _update_mission_clock(self) -> None:
        elapsed = max(0, int(time.monotonic() - self._elapsed_start))
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self._mission_clock.setText(f"T+ {hours:02}:{minutes:02}:{seconds:02}")

    def _set_overall_status(self, severity: Severity, text: str) -> None:
        self._overall_status.setText(text)
        color = _SEVERITY_COLORS[severity]
        self._overall_status.setStyleSheet(
            f"color: {color}; border: 1px solid {color};"
            "border-radius: 12px; padding: 8px 12px;"
        )

    def _append_log(
        self,
        message: str,
        severity: Severity | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        color = _SEVERITY_COLORS.get(severity, COLORS["muted"])
        display_time = (timestamp or datetime.now().astimezone()).strftime("%H:%M:%S")
        safe_message = escape(message)
        self._alert_console.moveCursor(QTextCursor.MoveOperation.End)
        self._alert_console.insertHtml(
            f'<span style="color:{color}">[{display_time}] {safe_message}</span><br>'
        )
        self._alert_console.moveCursor(QTextCursor.MoveOperation.End)

    def _report_storage_error(self, error: Exception) -> None:
        message = f"Local database write failed: {error}"
        self._storage_banner.setText(
            "LOCAL STORAGE ERROR — telemetry is still live, but records may "
            "not be saved. Check the database path and available disk space. "
            f"Details: {error}"
        )
        self._storage_banner.show()
        if not self._storage_error_reported:
            self._append_log(message, Severity.CRITICAL)
            self._storage_error_reported = True

    def _export_report(self) -> None:
        suggested_name = (
            f"astrohealth-mission-{datetime.now().astimezone():%Y%m%d-%H%M%S}.json"
        )
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Export mission health log",
            str(Path.home() / suggested_name),
            "JSON report (*.json)",
        )
        if not destination:
            return
        if not destination.lower().endswith(".json"):
            destination += ".json"
        try:
            exported = self._database.export_json(destination)
        except (OSError, sqlite3.Error, TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Export failed",
                f"The mission health log could not be exported.\n\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Export complete",
            f"Mission health log saved to:\n{exported}",
        )

    @staticmethod
    def _stylesheet() -> str:
        return f"""
            QWidget {{
                color: {COLORS["text"]};
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 13px;
            }}
            QScrollArea, QWidget#dashboardPage {{
                background-color: {COLORS["background"]};
                border: none;
            }}
            QFrame#headerPanel, QFrame#metricCard, QFrame#chartPanel,
            QFrame#contentPanel {{
                background-color: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 8px;
            }}
            QLabel#appTitle {{
                color: {COLORS["text"]};
                font-size: 26px;
                font-weight: 700;
            }}
            QLabel#headerSubtitle, QLabel#headerMeta, QLabel#sectionDetail,
            QLabel#metricTitle, QLabel#metricRange, QLabel#metricUnit,
            QLabel#disclaimer {{
                color: {COLORS["muted"]};
            }}
            QLabel#headerSubtitle, QLabel#headerMeta, QLabel#sectionDetail,
            QLabel#metricTitle, QLabel#metricStatus {{
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QLabel#missionClock {{
                color: {COLORS["cyan"]};
                font-family: "Consolas", "Courier New", monospace;
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#overallStatus {{
                background-color: {COLORS["background"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#sectionTitle, QLabel#chartTitle {{
                color: {COLORS["text"]};
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#metricValue {{
                color: {COLORS["text"]};
                font-family: "Consolas", "Courier New", monospace;
                font-size: 28px;
                font-weight: 700;
            }}
            QLabel#metricUnit {{
                font-size: 11px;
                padding-bottom: 4px;
            }}
            QLabel#metricRange {{
                font-size: 10px;
            }}
            QLabel#metricStatus {{
                font-size: 9px;
            }}
            QLabel#storageBanner {{
                color: {COLORS["critical"]};
                background-color: {COLORS["surface"]};
                border: 1px solid {COLORS["critical"]};
                border-radius: 6px;
                padding: 12px;
            }}
            QTextEdit#alertConsole {{
                background-color: {COLORS["background"]};
                color: {COLORS["text"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 8px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
                selection-background-color: {COLORS["cyan"]};
                selection-color: {COLORS["background"]};
            }}
            QPushButton {{
                color: {COLORS["text"]};
                background-color: {COLORS["background"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {COLORS["cyan"]};
                color: {COLORS["cyan"]};
            }}
            QPushButton:focus {{
                border: 2px solid {COLORS["cyan"]};
            }}
            QPushButton#button_critical {{
                border-color: {COLORS["critical"]};
            }}
            QPushButton#button_critical:hover {{
                color: {COLORS["critical"]};
            }}
            QPushButton#button_warning {{
                border-color: {COLORS["warning"]};
            }}
            QPushButton#button_warning:hover {{
                color: {COLORS["warning"]};
            }}
            QPushButton#button_primary {{
                color: {COLORS["background"]};
                background-color: {COLORS["cyan"]};
                border-color: {COLORS["cyan"]};
                font-weight: 700;
            }}
            QPushButton#button_primary:hover {{
                background-color: #7CF8FF;
            }}
            QPushButton#button_about {{
                color: {COLORS["cyan"]};
                border-color: {COLORS["cyan"]};
            }}
            QPushButton#button_about:hover {{
                color: {COLORS["background"]};
                background-color: {COLORS["cyan"]};
            }}
            QTextBrowser#aboutCredits {{
                background-color: {COLORS["background"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 12px;
                selection-background-color: {COLORS["cyan"]};
                selection-color: {COLORS["background"]};
            }}
            QTextBrowser#aboutCredits a {{
                color: {COLORS["cyan"]};
            }}
            QPushButton:disabled {{
                color: {COLORS["muted"]};
                border-color: {COLORS["border"]};
            }}
            QLabel#disclaimer {{
                font-size: 10px;
                padding: 4px 0;
            }}
            QScrollBar:vertical {{
                background: {COLORS["background"]};
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS["border"]};
                min-height: 28px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS["muted"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {COLORS["background"]};
                height: 12px;
            }}
            QScrollBar::handle:horizontal {{
                background: {COLORS["border"]};
                min-width: 28px;
                border-radius: 4px;
            }}
        """

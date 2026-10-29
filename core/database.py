"""Thread-safe SQLite storage and JSON export for local mission records."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from core.anomaly_engine import Anomaly, Severity
from core.simulator import TelemetrySample


class TelemetryDatabase:
    """Persist telemetry and incidents in an offline SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.path, check_same_thread=False, timeout=10.0
        )
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._create_tables()

    def close(self) -> None:
        """Close the local database connection."""
        with self._lock:
            self._connection.close()

    def record_sample(
        self, sample: TelemetrySample, overall_status: Severity
    ) -> None:
        """Store one timestamped telemetry record."""
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO telemetry_logs (
                    timestamp, heart_rate, spo2, body_temperature,
                    radiation, hrv, overall_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sample.timestamp.isoformat(),
                    sample.heart_rate,
                    sample.spo2,
                    sample.body_temperature,
                    sample.radiation,
                    sample.hrv,
                    overall_status.name,
                ),
            )

    def open_incident(self, anomaly: Anomaly, timestamp: datetime) -> int:
        """Record a newly active anomaly and return its row identifier."""
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO anomaly_incidents (
                    opened_at, resolved_at, severity, metric, message
                ) VALUES (?, NULL, ?, ?, ?)
                """,
                (
                    timestamp.isoformat(),
                    anomaly.severity.name,
                    anomaly.metric,
                    anomaly.message,
                ),
            )
            return int(cursor.lastrowid)

    def resolve_incident(self, incident_id: int, timestamp: datetime) -> None:
        """Close an active incident with its resolution timestamp."""
        with self._lock, self._connection:
            self._connection.execute(
                """
                UPDATE anomaly_incidents
                SET resolved_at = ?
                WHERE id = ? AND resolved_at IS NULL
                """,
                (timestamp.isoformat(), incident_id),
            )

    def export_json(self, destination: str | Path) -> Path:
        """Export all locally stored telemetry and incident records as JSON."""
        export_path = Path(destination).expanduser()
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            telemetry = self._connection.execute(
                "SELECT * FROM telemetry_logs ORDER BY id"
            ).fetchall()
            incidents = self._connection.execute(
                "SELECT * FROM anomaly_incidents ORDER BY id"
            ).fetchall()
            payload: dict[str, Any] = {
                "exported_at": datetime.now().astimezone().isoformat(),
                "database": str(self.path),
                "telemetry_logs": [dict(row) for row in telemetry],
                "anomaly_incidents": [dict(row) for row in incidents],
            }
        with export_path.open("w", encoding="utf-8", newline="\n") as report:
            json.dump(payload, report, indent=2, ensure_ascii=False)
            report.write("\n")
        return export_path

    def _create_tables(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                heart_rate REAL NOT NULL,
                spo2 REAL NOT NULL,
                body_temperature REAL NOT NULL,
                radiation REAL NOT NULL,
                hrv REAL NOT NULL,
                overall_status TEXT NOT NULL
                    CHECK (overall_status IN ('NORMAL', 'WARNING', 'CRITICAL'))
            );
            CREATE INDEX IF NOT EXISTS idx_telemetry_logs_timestamp
                ON telemetry_logs(timestamp);

            CREATE TABLE IF NOT EXISTS anomaly_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_at TEXT NOT NULL,
                resolved_at TEXT,
                severity TEXT NOT NULL
                    CHECK (severity IN ('WARNING', 'CRITICAL')),
                metric TEXT NOT NULL,
                message TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_anomaly_incidents_opened_at
                ON anomaly_incidents(opened_at);
            """
        )

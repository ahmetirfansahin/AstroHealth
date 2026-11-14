"""Focused tests for anomaly classification and offline persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from core.anomaly_engine import AnomalyEngine, Severity
from core.database import TelemetryDatabase
from core.simulator import TelemetrySample


def sample(
    *,
    heart_rate: float = 76.0,
    spo2: float = 97.0,
    body_temperature: float = 37.0,
    radiation: float = 0.10,
    hrv: float = 55.0,
) -> TelemetrySample:
    return TelemetrySample(
        timestamp=datetime.now(timezone.utc).astimezone(),
        heart_rate=heart_rate,
        spo2=spo2,
        body_temperature=body_temperature,
        radiation=radiation,
        hrv=hrv,
    )


class AnomalyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = AnomalyEngine()

    def test_nominal_readings_have_no_findings(self) -> None:
        self.assertEqual(self.engine.evaluate(sample()), ())

    def test_critical_hypoxia_is_explicit(self) -> None:
        findings = self.engine.evaluate(sample(spo2=91.0))
        hypoxia = next(item for item in findings if item.metric == "spo2")
        self.assertEqual(hypoxia.severity, Severity.CRITICAL)
        self.assertIn("SpO2 < 92%", hypoxia.message)
        self.assertEqual(hypoxia.hazard.code, "HAZARD_PHYSIOLOGICAL_STRESS")

    def test_out_of_range_heart_rate_is_warning(self) -> None:
        findings = self.engine.evaluate(sample(heart_rate=55.0))
        heart_rate = next(item for item in findings if item.metric == "heart_rate")
        self.assertEqual(heart_rate.severity, Severity.WARNING)

    def test_warning_radiation_and_critical_fever(self) -> None:
        findings = self.engine.evaluate(
            sample(radiation=0.45, body_temperature=38.7)
        )
        by_metric = {item.metric: item for item in findings}
        self.assertEqual(by_metric["radiation"].severity, Severity.WARNING)
        self.assertIsNone(by_metric["radiation"].hazard)
        self.assertEqual(
            by_metric["body_temperature"].severity, Severity.CRITICAL
        )
        self.assertEqual(
            by_metric["body_temperature"].hazard.code, "HAZARD_THERMAL_REGULATION"
        )

    def test_critical_heart_rate_and_warning_hrv(self) -> None:
        findings = self.engine.evaluate(sample(heart_rate=145, hrv=35))
        by_metric = {item.metric: item for item in findings}
        self.assertEqual(by_metric["heart_rate"].severity, Severity.CRITICAL)
        self.assertEqual(
            by_metric["heart_rate"].hazard.code, "HAZARD_PHYSIOLOGICAL_STRESS"
        )
        self.assertEqual(by_metric["hrv"].severity, Severity.WARNING)

    def test_hazard_boundaries_and_radiation_mapping(self) -> None:
        at_boundary = sample(heart_rate=140, spo2=92, body_temperature=38.5, radiation=1.5)
        self.assertTrue(all(item.hazard is None for item in self.engine.evaluate(at_boundary)))
        radiation = self.engine.evaluate(sample(radiation=1.501))[0]
        self.assertEqual(radiation.hazard.code, "HAZARD_RADIATION_SPE")
        self.assertEqual(radiation.hazard.nasa_hrp_hazard, "Space Radiation")


class DatabaseTests(unittest.TestCase):
    def test_persists_telemetry_incident_and_structured_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database = TelemetryDatabase(root / "mission.sqlite3")
            reading = sample(spo2=90.0)
            anomaly = AnomalyEngine().evaluate(reading)[0]
            incident_id = database.open_incident(anomaly, reading.timestamp)
            database.record_sample(reading, Severity.CRITICAL)
            database.resolve_incident(incident_id, reading.timestamp)

            export_path = database.export_json(root / "report.json")
            report = json.loads(export_path.read_text(encoding="utf-8"))
            database.close()

            self.assertEqual(len(report["telemetry_logs"]), 1)
            self.assertEqual(report["telemetry_logs"][0]["spo2"], 90.0)
            self.assertEqual(len(report["anomaly_incidents"]), 1)
            self.assertEqual(
                report["anomaly_incidents"][0]["severity"], "CRITICAL"
            )
            self.assertIsNotNone(report["anomaly_incidents"][0]["resolved_at"])
            hazard = report["anomaly_incidents"][0]["hazard_context"]
            self.assertEqual(hazard["code"], "HAZARD_PHYSIOLOGICAL_STRESS")
            self.assertTrue(hazard["explanation"])
            self.assertIn("https://www.nasa.gov/hrp/hazards/", hazard["references"])


if __name__ == "__main__":
    unittest.main()

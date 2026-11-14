"""Thread and scenario checks for the synthetic telemetry worker."""

from __future__ import annotations

import unittest

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtTest import QSignalSpy

from core.anomaly_engine import AnomalyEngine
from core.simulator import TelemetrySample, TelemetrySimulator


_APP = QCoreApplication.instance() or QCoreApplication([])


class TelemetrySimulatorTests(unittest.TestCase):
    def test_spe_rises_quickly_and_decays_to_background(self) -> None:
        profile = TelemetrySimulator._spe_excess_dose_rate
        self.assertGreater(profile(0), 1.5)
        self.assertGreater(profile(2), profile(0))
        self.assertGreater(profile(2), profile(8))
        self.assertGreater(profile(8), profile(19))
        self.assertGreater(profile(19), 0)
        self.assertEqual(profile(20), 0)

    def test_scenarios_emit_anomalous_samples_and_recover(self) -> None:
        simulator = TelemetrySimulator(interval_seconds=0.02)
        spy = QSignalSpy(simulator.sample_ready)
        simulator.start()
        try:
            self.assertTrue(spy.wait(1000))
            nominal_sample = spy[0][0]
            self.assertIsInstance(nominal_sample, TelemetrySample)
            self.assertTrue(60 <= nominal_sample.heart_rate <= 100)
            self.assertTrue(95 <= nominal_sample.spo2 <= 99)
            self.assertTrue(36.5 <= nominal_sample.body_temperature <= 37.5)
            self.assertTrue(0.05 <= nominal_sample.radiation <= 0.20)
            self.assertTrue(40 <= nominal_sample.hrv <= 70)

            simulator.trigger_hypoxia_event()
            simulator.trigger_radiation_spike()
            simulator.trigger_fever_event()
            self.assertTrue(spy.wait(1000))
            event_sample = spy[len(spy) - 1][0]
            self.assertIsInstance(event_sample, TelemetrySample)
            self.assertLess(event_sample.spo2, 92)
            self.assertGreaterEqual(event_sample.heart_rate, 140)
            self.assertGreater(event_sample.radiation, 1.5)
            self.assertGreater(event_sample.body_temperature, 38.5)
            self.assertGreaterEqual(len(AnomalyEngine().evaluate(event_sample)), 4)

            simulator.trigger_recovery()
            self.assertTrue(spy.wait(1000))
            recovered_sample = spy[len(spy) - 1][0]
            self.assertIsInstance(recovered_sample, TelemetrySample)
            self.assertGreaterEqual(recovered_sample.spo2, 95)
            self.assertLessEqual(recovered_sample.heart_rate, 100)
            self.assertLessEqual(recovered_sample.radiation, 0.20)
            self.assertLessEqual(recovered_sample.body_temperature, 37.5)
        finally:
            simulator.stop()
            self.assertTrue(simulator.wait(1000))


if __name__ == "__main__":
    unittest.main()

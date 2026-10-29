"""Threaded, synthetic crew telemetry for offline demonstrations."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from PyQt6.QtCore import QObject, QThread, pyqtSignal


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One timestamped synthetic biometric and environmental reading."""

    timestamp: datetime
    heart_rate: float
    spo2: float
    body_temperature: float
    radiation: float
    hrv: float


class TelemetrySimulator(QThread):
    """Emit synthetic telemetry from a worker thread at a fixed interval."""

    sample_ready = pyqtSignal(object)

    _EVENT_DURATIONS = {
        "hypoxia": 30.0,
        "radiation": 20.0,
        "fever": 30.0,
    }

    def __init__(
        self, interval_seconds: float = 1.0, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        if interval_seconds <= 0:
            raise ValueError("The telemetry interval must be greater than zero.")
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._scenario_lock = threading.Lock()
        self._active_scenarios: dict[str, float] = {}
        self._rng = random.Random()

    def trigger_hypoxia_event(self) -> None:
        """Simulate a temporary low-oxygen event."""
        self._trigger("hypoxia")

    def trigger_radiation_spike(self) -> None:
        """Simulate a temporary solar-particle radiation spike."""
        self._trigger("radiation")

    def trigger_fever_event(self) -> None:
        """Simulate a temporary fever or hyperthermia event."""
        self._trigger("fever")

    def trigger_recovery(self) -> None:
        """Clear active event scenarios and resume nominal readings."""
        with self._scenario_lock:
            self._active_scenarios.clear()

    def stop(self) -> None:
        """Request a prompt, thread-safe shutdown."""
        self._stop_event.set()

    def run(self) -> None:
        """Emit an immediate sample, then continue until stopped."""
        self._stop_event.clear()
        while not self._stop_event.is_set():
            self.sample_ready.emit(self._generate_sample())
            if self._stop_event.wait(self._interval_seconds):
                break

    def _trigger(self, scenario: str) -> None:
        with self._scenario_lock:
            self._active_scenarios[scenario] = (
                time.monotonic() + self._EVENT_DURATIONS[scenario]
            )

    def _generate_sample(self) -> TelemetrySample:
        now = time.monotonic()
        with self._scenario_lock:
            self._active_scenarios = {
                name: expiry
                for name, expiry in self._active_scenarios.items()
                if expiry > now
            }
            scenarios = frozenset(self._active_scenarios)

        heart_rate = min(100.0, max(60.0, self._rng.gauss(76.0, 5.0)))
        spo2 = min(99.0, max(95.0, self._rng.gauss(97.0, 0.7)))
        body_temperature = min(37.5, max(36.5, self._rng.gauss(37.0, 0.12)))
        radiation = self._rng.uniform(0.05, 0.20)
        hrv = min(70.0, max(40.0, self._rng.gauss(55.0, 5.0)))

        if "hypoxia" in scenarios:
            heart_rate = max(141.0, self._rng.gauss(145.0, 3.0))
            spo2 = self._rng.uniform(88.0, 91.0)
        if "radiation" in scenarios:
            radiation = self._rng.uniform(1.6, 2.4)
        if "fever" in scenarios:
            body_temperature = self._rng.uniform(38.6, 39.2)

        return TelemetrySample(
            timestamp=datetime.now(timezone.utc).astimezone(),
            heart_rate=round(heart_rate, 1),
            spo2=round(spo2, 1),
            body_temperature=round(body_temperature, 2),
            radiation=round(radiation, 3),
            hrv=round(hrv, 1),
        )

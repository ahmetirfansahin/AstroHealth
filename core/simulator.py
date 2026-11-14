"""Threaded, synthetic crew telemetry for offline demonstrations."""

from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import uuid4

from PyQt6.QtCore import QObject, QThread, pyqtSignal


NOAA_SOLAR_STORMS_URL = "https://www.spaceweather.gov/phenomena/solar-radiation-storm"


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One timestamped synthetic biometric and environmental reading."""

    timestamp: datetime
    heart_rate: float
    spo2: float
    body_temperature: float
    radiation: float
    hrv: float
    session_cumulative_radiation_msv: float | None = None
    simulation_session_id: str | None = None


class TelemetrySimulator(QThread):
    """Emit synthetic telemetry from a worker thread at a fixed interval."""

    sample_ready = pyqtSignal(object)

    _EVENT_DURATIONS = {
        "hypoxia": 30.0,
        "radiation": 20.0,
        "fever": 30.0,
    }
    _SPE_RISE_SECONDS = 2.0
    _SPE_ONSET_EXCESS = 1.6  # mSv/h above synthetic background
    _SPE_PEAK_EXCESS = 2.2

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
        """Start or restart a time-compressed synthetic solar particle event."""
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
        session_id = uuid4().hex
        cumulative_dose = 0.0
        previous_time = None
        previous_rate = 0.0
        while not self._stop_event.is_set():
            sample = self._generate_sample()
            now = time.monotonic()
            if previous_time is not None:
                mean_rate = (previous_rate + sample.radiation) / 2
                cumulative_dose += mean_rate * (now - previous_time) / 3600
            self.sample_ready.emit(
                replace(
                    sample,
                    session_cumulative_radiation_msv=cumulative_dose,
                    simulation_session_id=session_id,
                )
            )
            previous_time = now
            previous_rate = sample.radiation
            if self._stop_event.wait(self._interval_seconds):
                break

    def _trigger(self, scenario: str) -> None:
        with self._scenario_lock:
            self._active_scenarios[scenario] = (
                time.monotonic() + self._EVENT_DURATIONS[scenario]
            )

    def _generate_sample(self) -> TelemetrySample:
        with self._scenario_lock:
            now = time.monotonic()
            self._active_scenarios = {
                name: expiry
                for name, expiry in self._active_scenarios.items()
                if expiry > now
            }
            scenarios = frozenset(self._active_scenarios)
            radiation_expiry = self._active_scenarios.get("radiation")

        heart_rate = min(100.0, max(60.0, self._rng.gauss(76.0, 5.0)))
        spo2 = min(99.0, max(95.0, self._rng.gauss(97.0, 0.7)))
        body_temperature = min(37.5, max(36.5, self._rng.gauss(37.0, 0.12)))
        radiation = self._rng.uniform(0.05, 0.20)
        hrv = min(70.0, max(40.0, self._rng.gauss(55.0, 5.0)))

        if "hypoxia" in scenarios:
            heart_rate = max(141.0, self._rng.gauss(145.0, 3.0))
            spo2 = self._rng.uniform(88.0, 91.0)
        if radiation_expiry is not None:
            elapsed = self._EVENT_DURATIONS["radiation"] - (radiation_expiry - now)
            radiation += self._spe_excess_dose_rate(elapsed)
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

    @classmethod
    def _spe_excess_dose_rate(cls, elapsed: float) -> float:
        """Model abrupt arrival, a rapid rise and a slower return to background.

        NOAA observations motivate the time-compressed shape. The amplitude
        is synthetic and independent of GOES proton flux.
        """
        duration = cls._EVENT_DURATIONS["radiation"]
        if elapsed < 0 or elapsed >= duration:
            return 0.0
        rise = cls._SPE_RISE_SECONDS
        if elapsed <= rise:
            return cls._SPE_ONSET_EXCESS + (
                cls._SPE_PEAK_EXCESS - cls._SPE_ONSET_EXCESS
            ) * elapsed / rise

        decay_fraction = (elapsed - rise) / (duration - rise)
        return cls._SPE_PEAK_EXCESS * (
            math.expm1(4.0 * (1.0 - decay_fraction)) / math.expm1(4.0)
        )

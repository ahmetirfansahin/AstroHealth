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

from core.crew_profile import CrewProfile


NOAA_SOLAR_STORMS_URL = "https://www.spaceweather.gov/phenomena/solar-radiation-storm"


@dataclass(frozen=True, slots=True)
class Scenario:
    label: str
    duration: float
    group: str
    description: str


SCENARIOS = {
    "hypoxia": Scenario("Hypoxia", 30, "cardiac", "SpO2 and HRV fall as heart rate rises."),
    "radiation": Scenario("Solar particle event", 20, "radiation", "Abrupt dose-rate spike followed by decay."),
    "fever": Scenario("Fever", 30, "thermal", "Body temperature and resting heart rate rise as HRV falls."),
    "exertion": Scenario("EVA exertion", 25, "cardiac", "Heart rate rises and HRV falls, then both recover."),
    "bradycardia": Scenario("Bradycardia", 20, "cardiac", "Heart rate drops below the critical limit."),
    "cold": Scenario("Cold exposure", 25, "thermal", "Body temperature drops below the configured range."),
    "low_hrv": Scenario(
        "Autonomic strain", 25, "cardiac",
        "Resting heart rate rises and HRV drops below the age-based critical limit.",
    ),
}


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
    crew_profile: CrewProfile | None = None


class TelemetrySimulator(QThread):
    """Emit synthetic telemetry from a worker thread at a fixed interval."""

    sample_ready = pyqtSignal(object)

    _SPE_RISE_SECONDS = 2.0
    _SPE_ONSET_EXCESS = 1.6  # mSv/h above synthetic background
    _SPE_PEAK_EXCESS = 2.2

    def __init__(
        self,
        interval_seconds: float = 1.0,
        parent: QObject | None = None,
        *,
        profile: CrewProfile | None = None,
    ) -> None:
        super().__init__(parent)
        if interval_seconds <= 0:
            raise ValueError("The telemetry interval must be greater than zero.")
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._scenario_lock = threading.Lock()
        self._profile = profile or CrewProfile()
        self._active_scenarios: dict[str, float] = {}
        self._rng = random.Random()

    def set_profile(self, profile: CrewProfile) -> None:
        """Apply the profile to future samples without interrupting scenarios."""
        with self._scenario_lock:
            self._profile = profile

    def trigger_hypoxia_event(self) -> None:
        """Simulate a temporary low-oxygen event."""
        self.trigger_scenario("hypoxia")

    def trigger_radiation_spike(self) -> None:
        """Start or restart a time-compressed synthetic solar particle event."""
        self.trigger_scenario("radiation")

    def trigger_fever_event(self) -> None:
        """Simulate a temporary fever or hyperthermia event."""
        self.trigger_scenario("fever")

    def trigger_scenario(self, key: str) -> None:
        """Start or restart an event, replacing conflicts in its group."""
        scenario = SCENARIOS[key]
        with self._scenario_lock:
            now = time.monotonic()
            self._active_scenarios = {
                active: expiry
                for active, expiry in self._active_scenarios.items()
                if expiry > now and SCENARIOS[active].group != scenario.group
            }
            self._active_scenarios[key] = now + scenario.duration

    def active_scenarios(self) -> dict[str, float]:
        """Return remaining wall-clock seconds for each active event."""
        with self._scenario_lock:
            now = time.monotonic()
            return {
                key: expiry - now
                for key, expiry in self._active_scenarios.items()
                if expiry > now
            }

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

    def _generate_sample(self) -> TelemetrySample:
        with self._scenario_lock:
            now = time.monotonic()
            self._active_scenarios = {
                name: expiry
                for name, expiry in self._active_scenarios.items()
                if expiry > now
            }
            scenarios = {
                key: expiry - now for key, expiry in self._active_scenarios.items()
            }
            profile = self._profile

        heart_rate = min(100.0, max(60.0, self._rng.gauss(76.0, 5.0)))
        spo2 = self._rng.uniform(profile.spo2.low, profile.spo2.high)
        body_temperature = self._rng.uniform(
            profile.body_temperature.low, profile.body_temperature.high
        )
        radiation = self._rng.uniform(0.05, 0.20)
        hrv_range = profile.hrv
        hrv_baseline = self._rng.gauss((hrv_range.low + hrv_range.high) / 2, 3.0)
        hrv_baseline = min(hrv_range.high, max(hrv_range.low, hrv_baseline))
        autonomic_strain = 0.0

        if "hypoxia" in scenarios:
            autonomic_strain = self._rng.uniform(0.7, 0.85)
            spo2 = 91.0 - 3.0 * autonomic_strain
            heart_rate = profile.max_heart_rate * (0.85 + 0.08 * autonomic_strain)
        elif "exertion" in scenarios:
            remaining = scenarios["exertion"]
            elapsed = SCENARIOS["exertion"].duration - remaining
            effort = max(0.0, min(1.0, elapsed / 4, remaining / 5))
            target = (profile.heart_rate.high + profile.max_heart_rate) / 2
            heart_rate += (target - heart_rate) * effort
            autonomic_strain = 0.85 * effort
        elif "bradycardia" in scenarios:
            heart_rate = self._rng.uniform(32.0, 38.0)
        elif "low_hrv" in scenarios:
            autonomic_strain = 1.0
            heart_rate += 25.0
        if "radiation" in scenarios:
            elapsed = SCENARIOS["radiation"].duration - scenarios["radiation"]
            radiation += self._spe_excess_dose_rate(elapsed)
        if "fever" in scenarios:
            body_temperature = self._rng.uniform(38.6, 39.2)
            thermal_strain = 0.7 + 0.2 * (body_temperature - 38.6) / 0.6
            autonomic_strain = max(autonomic_strain, thermal_strain)
            if not any(SCENARIOS[key].group == "cardiac" for key in scenarios):
                heart_rate += 25.0 * thermal_strain
        elif "cold" in scenarios:
            body_temperature = profile.body_temperature.low - self._rng.uniform(0.3, 0.8)
        # Synthetic RMSSD-style response to a shared stressor. Coefficients
        # set demonstration amplitudes and are independent of clinical cutoffs.
        hrv_floor = hrv_range.low - 14.0
        hrv = hrv_baseline + (hrv_floor - hrv_baseline) * autonomic_strain

        return TelemetrySample(
            timestamp=datetime.now(timezone.utc).astimezone(),
            heart_rate=round(heart_rate, 1),
            spo2=round(spo2, 1),
            body_temperature=round(body_temperature, 2),
            radiation=round(radiation, 3),
            hrv=round(hrv, 1),
            crew_profile=profile,
        )

    @classmethod
    def _spe_excess_dose_rate(cls, elapsed: float) -> float:
        """Model abrupt arrival, a rapid rise and a slower return to background.

        NOAA observations motivate the time-compressed shape. The amplitude
        is synthetic and independent of GOES proton flux.
        """
        duration = SCENARIOS["radiation"].duration
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

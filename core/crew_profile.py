"""Age-based demonstration ranges for crew telemetry."""

from __future__ import annotations

from dataclasses import dataclass


MIN_CREW_AGE = 26
MAX_CREW_AGE = 46


@dataclass(frozen=True, slots=True)
class MetricRange:
    """Inclusive configured range for a simulated metric."""

    low: float
    high: float

    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high


@dataclass(frozen=True, slots=True)
class CrewProfile:
    """Simulation profile selected by the operator's crew age."""

    age: int = 36
    spo2: MetricRange = MetricRange(95.0, 99.0)
    body_temperature: MetricRange = MetricRange(36.5, 37.5)

    def __post_init__(self) -> None:
        if not MIN_CREW_AGE <= self.age <= MAX_CREW_AGE:
            raise ValueError(
                f"Crew age must be between {MIN_CREW_AGE} and {MAX_CREW_AGE}."
            )

    @property
    def max_heart_rate(self) -> int:
        return 220 - self.age

    @property
    def heart_rate(self) -> MetricRange:
        return MetricRange(60.0, self.max_heart_rate * 0.85)

    @property
    def hrv(self) -> MetricRange:
        if self.age <= 35:
            return MetricRange(55.0, 85.0)
        return MetricRange(40.0, 65.0)

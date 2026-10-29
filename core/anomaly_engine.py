"""Transparent, configurable demonstration thresholds for simulated telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from core.simulator import TelemetrySample


class Severity(IntEnum):
    """Ordered dashboard severity levels."""

    NORMAL = 0
    WARNING = 1
    CRITICAL = 2


@dataclass(frozen=True, slots=True)
class Anomaly:
    """A single active threshold finding."""

    metric: str
    severity: Severity
    message: str


class AnomalyEngine:
    """Classify samples using explicit demo thresholds, not medical guidance."""

    def evaluate(self, sample: TelemetrySample) -> tuple[Anomaly, ...]:
        """Return active findings in stable metric order."""
        findings: list[Anomaly] = []

        if sample.heart_rate < 40 or sample.heart_rate > 140:
            findings.append(
                Anomaly(
                    "heart_rate",
                    Severity.CRITICAL,
                    f"CRITICAL: Heart rate outside configured limits - "
                    f"{sample.heart_rate:.0f} bpm",
                )
            )
        elif sample.heart_rate < 60 or sample.heart_rate > 100:
            findings.append(
                Anomaly(
                    "heart_rate",
                    Severity.WARNING,
                    f"WARNING: Heart rate outside configured range - "
                    f"{sample.heart_rate:.0f} bpm",
                )
            )

        if sample.spo2 < 92:
            findings.append(
                Anomaly(
                    "spo2",
                    Severity.CRITICAL,
                    f"CRITICAL: Hypoxia Detected - SpO2 < 92% "
                    f"({sample.spo2:.1f}%)",
                )
            )
        elif sample.spo2 < 95:
            findings.append(
                Anomaly(
                    "spo2",
                    Severity.WARNING,
                    f"WARNING: Low blood oxygen - SpO2 < 95% "
                    f"({sample.spo2:.1f}%)",
                )
            )

        if sample.body_temperature > 38.5:
            findings.append(
                Anomaly(
                    "body_temperature",
                    Severity.CRITICAL,
                    f"CRITICAL: Fever / Hyperthermia - temperature > 38.5 C "
                    f"({sample.body_temperature:.2f} C)",
                )
            )
        elif sample.body_temperature > 37.5:
            findings.append(
                Anomaly(
                    "body_temperature",
                    Severity.WARNING,
                    f"WARNING: Elevated body temperature - "
                    f"{sample.body_temperature:.2f} C",
                )
            )

        if sample.radiation > 1.5:
            findings.append(
                Anomaly(
                    "radiation",
                    Severity.CRITICAL,
                    f"CRITICAL: Solar Particle Event radiation peak - "
                    f"{sample.radiation:.2f} mSv/h",
                )
            )
        elif sample.radiation > 0.20:
            findings.append(
                Anomaly(
                    "radiation",
                    Severity.WARNING,
                    f"WARNING: Radiation Peak - Solar Flare Risk "
                    f"({sample.radiation:.2f} mSv/h)",
                )
            )

        if sample.hrv < 30:
            findings.append(
                Anomaly(
                    "hrv",
                    Severity.CRITICAL,
                    f"CRITICAL: HRV below configured limit - {sample.hrv:.0f} ms",
                )
            )
        elif sample.hrv < 40:
            findings.append(
                Anomaly(
                    "hrv",
                    Severity.WARNING,
                    f"WARNING: HRV below configured range - {sample.hrv:.0f} ms",
                )
            )

        return tuple(findings)

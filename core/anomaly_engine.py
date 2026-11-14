"""Transparent, configurable demonstration thresholds for simulated telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from core.crew_profile import CrewProfile
from core.mission_parameters import NASA_HRP_URL
from core.simulator import TelemetrySample


NASA_RADIATION_URL = "https://www.nasa.gov/reference/6-0-natural-and-induced-environments-vol-2/"
NASA_SPACESUITS_URL = "https://www.nasa.gov/reference/11-0-spacesuits-vol-2/"
CSA_DOSIMETRY_URL = "https://www.asc-csa.gc.ca/eng/astronauts/space-medicine/radiation.asp"


@dataclass(frozen=True, slots=True)
class HazardContext:
    code: str
    nasa_hrp_hazard: str
    explanation: str
    references: tuple[str, ...]


RADIATION_SPE = HazardContext(
    "HAZARD_RADIATION_SPE",
    "Space Radiation",
    "Energetic solar particles can rapidly increase crew radiation exposure. "
    "The simulation uses an ambient dose-rate trigger for a suspected SPE. "
    "NASA-STD-3001 V2 6164 addresses exposure-rate alerting, and CSA describes "
    "dosimetry and cumulative exposure limits.",
    (NASA_HRP_URL, NASA_RADIATION_URL, CSA_DOSIMETRY_URL),
)
PHYSIOLOGICAL_STRESS = HazardContext(
    "HAZARD_PHYSIOLOGICAL_STRESS",
    "Gravity Fields",
    "Low oxygen saturation or elevated heart rate can flag physiological "
    "strain. Altered gravity affects cardiovascular adaptation, and EVA "
    "exertion raises metabolic demand. The readings alone cannot establish cause.",
    (NASA_HRP_URL, NASA_SPACESUITS_URL),
)
THERMAL_REGULATION = HazardContext(
    "HAZARD_THERMAL_REGULATION",
    "Hostile/Closed Environments",
    "Elevated body temperature can flag heat strain. During EVA, metabolic "
    "heat can accumulate if heat removal is insufficient. NASA-STD-3001 "
    "V2 11011 addresses suited crewmember heat storage.",
    (NASA_HRP_URL, NASA_SPACESUITS_URL),
)


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
    hazard: HazardContext | None = None


class AnomalyEngine:
    """Apply simulation thresholds and attach relevant NASA HRP hazard context."""

    def evaluate(
        self, sample: TelemetrySample, profile: CrewProfile | None = None
    ) -> tuple[Anomaly, ...]:
        """Return active findings in stable metric order."""
        findings: list[Anomaly] = []
        profile = profile or sample.crew_profile or CrewProfile()
        max_heart_rate = profile.max_heart_rate

        if sample.heart_rate < 40 or sample.heart_rate > max_heart_rate:
            findings.append(
                Anomaly(
                    "heart_rate",
                    Severity.CRITICAL,
                    f"CRITICAL: Heart rate outside configured limits - "
                    f"{sample.heart_rate:.0f} bpm",
                    PHYSIOLOGICAL_STRESS if sample.heart_rate > max_heart_rate else None,
                )
            )
        elif not profile.heart_rate.contains(sample.heart_rate):
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
                    f"CRITICAL: Low oxygen saturation - SpO2 < 92% "
                    f"({sample.spo2:.1f}%)",
                    PHYSIOLOGICAL_STRESS,
                )
            )
        elif not profile.spo2.contains(sample.spo2):
            findings.append(
                Anomaly(
                    "spo2",
                    Severity.WARNING,
                    f"WARNING: SpO2 outside configured range "
                    f"({sample.spo2:.1f}%)",
                )
            )

        if sample.body_temperature > 38.5:
            findings.append(
                Anomaly(
                    "body_temperature",
                    Severity.CRITICAL,
                    f"CRITICAL: Elevated body temperature > 38.5 C "
                    f"({sample.body_temperature:.2f} C)",
                    THERMAL_REGULATION,
                )
            )
        elif not profile.body_temperature.contains(sample.body_temperature):
            findings.append(
                Anomaly(
                    "body_temperature",
                    Severity.WARNING,
                    f"WARNING: Body temperature outside configured range - "
                    f"{sample.body_temperature:.2f} C",
                )
            )

        if sample.radiation > 1.5:
            findings.append(
                Anomaly(
                    "radiation",
                    Severity.CRITICAL,
                    f"CRITICAL: Elevated dose rate, suspected solar particle event - "
                    f"{sample.radiation:.2f} mSv/h",
                    RADIATION_SPE,
                )
            )
        elif sample.radiation > 0.20:
            findings.append(
                Anomaly(
                    "radiation",
                    Severity.WARNING,
                    f"WARNING: Dose rate above simulated background "
                    f"({sample.radiation:.2f} mSv/h)",
                )
            )

        if sample.hrv < profile.hrv.low - 10:
            findings.append(
                Anomaly(
                    "hrv",
                    Severity.CRITICAL,
                    f"CRITICAL: HRV below configured limit - {sample.hrv:.0f} ms",
                )
            )
        elif not profile.hrv.contains(sample.hrv):
            findings.append(
                Anomaly(
                    "hrv",
                    Severity.WARNING,
                    f"WARNING: HRV outside configured range - {sample.hrv:.0f} ms",
                )
            )

        return tuple(findings)

"""Published context and synthetic parameters shown in the mission UI."""

from __future__ import annotations

from dataclasses import dataclass


NASA_HRP_URL = "https://www.nasa.gov/hrp/hazards/"
WHO5_URL = "https://www.who.int/publications/m/item/who-ucn-msd-mhe-2024.01"


@dataclass(frozen=True, slots=True)
class ReferenceValue:
    parameter: str
    value: float
    unit: str
    context: str
    source: str


@dataclass(frozen=True, slots=True)
class HazardParameter:
    hazard: str
    candidate_inputs: str
    candidate_outcomes: str
    references: tuple[str, ...]


NASA_RADIATION_URL = (
    "https://www.nasa.gov/reference/6-0-natural-and-induced-environments-vol-2/"
)
NASA_SPACESUITS_URL = "https://www.nasa.gov/reference/11-0-spacesuits-vol-2/"
CSA_DOSIMETRY_URL = (
    "https://www.asc-csa.gc.ca/eng/astronauts/space-medicine/radiation.asp"
)
NOAA_SOLAR_STORMS_URL = (
    "https://www.spaceweather.gov/phenomena/solar-radiation-storm"
)

SOURCES = {
    NASA_HRP_URL: "NASA Human Research Program: Hazards of Human Spaceflight",
    NASA_RADIATION_URL: "NASA-STD-3001 Volume 2: Natural and Induced Environments",
    NASA_SPACESUITS_URL: "NASA-STD-3001 Volume 2: Spacesuits",
    CSA_DOSIMETRY_URL: "CSA astronaut dosimetry and radiation exposure",
    NOAA_SOLAR_STORMS_URL: "NOAA solar radiation storms",
    WHO5_URL: "WHO-5 Well-Being Index",
    "https://pubmed.ncbi.nlm.nih.gov/26781711/": "Exercise and HRV recovery",
    "https://pubmed.ncbi.nlm.nih.gov/27030629/": "Hypoxic exposure and HRV",
    "https://pubmed.ncbi.nlm.nih.gov/24390688/": "Heat stress and HRV",
}

REFERENCE_VALUES = (
    ReferenceValue(
        "Nominal radiation dose rate",
        0.20,
        "mSv/h",
        "Synthetic alert baseline for the dashboard.",
        NASA_RADIATION_URL,
    ),
    ReferenceValue(
        "Critical radiation dose rate",
        1.50,
        "mSv/h",
        "Synthetic threshold for a suspected solar particle event.",
        NASA_RADIATION_URL,
    ),
)

HAZARD_PARAMETERS = (
    HazardParameter(
        "Space Radiation",
        "Radiation dose rate and cumulative dose",
        "Radiation exposure and suspected solar particle event",
        (NASA_HRP_URL, NASA_RADIATION_URL, CSA_DOSIMETRY_URL),
    ),
    HazardParameter(
        "Gravity Fields",
        "Heart rate, oxygen saturation, and exertion state",
        "Cardiovascular adaptation and physiological strain",
        (NASA_HRP_URL, NASA_SPACESUITS_URL),
    ),
    HazardParameter(
        "Hostile/Closed Environments",
        "Body temperature and thermal scenario state",
        "Heat storage and thermal regulation strain",
        (NASA_HRP_URL, NASA_SPACESUITS_URL),
    ),
)

RESEARCH_EXAMPLES = {
    "Exercise and HRV recovery": (
        "Research context for the synthetic exertion and recovery response."
    ),
    "Hypoxic exposure and HRV": (
        "Research context for the synthetic hypoxia response."
    ),
    "Heat stress and HRV": (
        "Research context for the synthetic fever response."
    ),
}

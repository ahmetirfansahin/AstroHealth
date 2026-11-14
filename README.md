# AstroHealth

AstroHealth is an offline crew-health simulator built with PyQt6 and PyQtGraph
for the NASA Space Apps Challenge. The dashboard plots heart rate and ambient
radiation, tracks simulated cumulative radiation dose, and flags telemetry
that crosses configured thresholds.

## Run

Python 3.10 or later is required.

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Crew age and alerts

Set **Crew age** to a value from 26 to 46. The dashboard updates the card ranges
and heart-rate alert lines, clears both graphs, and starts plotting fresh
readings for the selected profile.

| Metric | Default simulation settings |
| --- | --- |
| HRV | 55–85 ms at ages 26–35 and 40–65 ms at ages 36–46 |
| Upper heart rate | Warning above 85% of the age-predicted maximum and critical above `220 − age` |
| SpO₂ | 95–99% configured range |
| Body temperature | 36.5–37.5 °C configured range |

## Scenario controls

| Scenario | Duration | Telemetry effect |
| --- | --- | --- |
| Hypoxia | 30 s | SpO₂ and HRV fall as heart rate rises |
| Solar particle event | 20 s | Radiation dose rate spikes, then decays |
| Fever | 30 s | Temperature rises above the critical threshold, HRV falls, and resting heart rate rises |
| EVA exertion | 25 s | Heart rate rises and HRV falls during exertion, then both recover |
| Bradycardia | 20 s | Heart rate drops below the critical threshold |
| Cold exposure | 25 s | Body temperature falls below the configured range |
| Autonomic strain | 25 s | Resting heart rate rises and HRV falls below the age-based critical threshold |

The panel shows active scenarios and their remaining time. A new scenario
replaces an active scenario in the same group, such as Fever replacing Cold
exposure. Independent scenarios can run together. Select **End active
scenarios** to return to nominal telemetry on the next reading.

The synthetic HRV channel represents an RMSSD-style measure of beat-to-beat
variability. Exercise, hypoxia, and thermal strain can change several readings
together. The simulator uses scenario-specific responses, with amplitudes and
timing chosen for demonstration. [Exercise and HRV recovery](https://pubmed.ncbi.nlm.nih.gov/26781711/)
· [Hypoxic exposure and HRV](https://pubmed.ncbi.nlm.nih.gov/27030629/)
· [Heat stress and HRV](https://pubmed.ncbi.nlm.nih.gov/24390688/)

## Well-being check and emergency support

Select **Well-Being Check** to complete the five English WHO-5 items about
the past two weeks. All five answers are required. The app adds the item
scores and multiplies the total by four to display a score out of 100.
Scores below 50 automatically open the support screen with the score and a
recommendation for a private medical check-in. This uses the WHO-5 threshold
for further assessment. In the app, immediate-help instructions are shown
on that same screen for anyone who needs them. The score alone does not
identify an emergency. Answers and scores are kept in memory for the session
flow and excluded from telemetry logs and exports.
[English WHO-5 and scoring guidance](https://www.who.int/publications/m/item/who-ucn-msd-mhe-2024.01)

Select **I need help now** in the dashboard header to open the English
emergency support screen. It works offline and is available at any telemetry
status. The screen directs crew to alert a nearby crewmate, contact the
onboard medical officer, and follow the mission's emergency medical procedure.
Opening it sends no message and creates no entry in the mission health log.
For operational use, the mission must supply its approved procedure and
emergency contact channel.

- Spaceflight emergency procedures and the role of onboard medical support. [NASA spaceflight medical operations](https://www.nasa.gov/reference/6-0-medical-operations/)
- Crew behavioral health support and private consultation. [NASA Behavioral Health & Performance](https://www.nasa.gov/reference/jsc-behavioral-health/)
- Immediate help for thoughts of suicide or urges to self-harm. [NIMH guidance on when to get immediate help](https://www.nimh.nih.gov/health/publications/my-mental-health-do-i-need-help)

The same references are available under **About → Emergency support references**.

## Local records and references

Telemetry and incidents are stored at `~/.astrohealth/astrohealth.sqlite3`.
Select **Export mission health log** to save the stored data, incident hazard
context, and mission reference parameters as JSON.

Open **About** for NASA HRP, NASA-STD-3001, CSA dosimetry, and NOAA references.
All telemetry and alert thresholds are configured for simulation and
demonstration.

## License and attributions

AstroHealth is distributed under GPL-3.0-only; see [LICENSE](./LICENSE).
Third-party software licenses and attribution details are provided in
[THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) and the dashboard's About
window.

## Verification

```powershell
python -m unittest discover -s tests -v
```

# AstroHealth Design System

## Surface and mode

AstroHealth is a desktop mission-health monitoring demonstration. The dashboard
is an **Operate** surface: crew status, measurements, trends, incidents, and
simulation controls remain visible and clearly labeled while the operator
monitors the stream.

## Visual direction

The crew watch docket brings together a persistent mission context and
time-stamped readings. It uses a measured, ruled information hierarchy, not a
generic clinical sheet: mission status leads; metric name, numeric value, unit,
configured range, and alert state stay close; trend plots and a chronological
incident record share the same watch surface.

## Tokens

| Token | Value | Use |
|---|---|---|
| Background | `#0B0E14` | Main window, chart field, and reading surfaces |
| Surface | `#131822` | Panels, measurement tiles, and controls |
| Border | `#1F293D` | Fine panel divisions and secondary control outlines |
| Primary accent | `#00F0FF` | Mission clock, focus, selected interactions, and heart-rate trace |
| Normal | `#00FF87` | Normal readings and clear crew status |
| Warning | `#FFB800` | Threshold warnings and radiation trace |
| Critical | `#FF2A6D` | Critical threshold state |
| Secondary text | `#8A99AD` | Captions, ranges, and supporting metadata |
| Primary text | `#E8EEF6` | High-contrast labels and values |

Use an 8px spacing rhythm for page gutters, card insets, and component gaps.
Panel corners are restrained and consistent. Borders, rather than broad shadows,
separate instrument regions.

## Typography and information design

Use a readable sans-serif hierarchy for labels and headings. Use a monospaced
face only for measured numeric values and the mission clock. Keep each metric's
plain-language name, value, unit, configured reference range, and severity
visible together. Severity is conveyed in text as well as color.

## Dashboard regions

- Mission header: AstroHealth, NASA Space Apps context, mission elapsed clock,
  overall crew status, About, **Well-Being Check**, and a persistent
  **I need help now** action.
- Well-being check: the five English WHO-5 items with no preselected answers.
  Low scores open the support dialog with a private check-in recommendation
  above the immediate-help instructions.
  [WHO-5](https://www.who.int/publications/m/item/who-ucn-msd-mhe-2024.01)
- Emergency support: a keyboard-accessible dialog with immediate steps in
  English, an explicit note about message delivery, and a close action.
  The critical accent marks the entry point. The steps are readable offline.
  [NASA spaceflight medical operations](https://www.nasa.gov/reference/6-0-medical-operations/)
  · [NIMH guidance on when to get immediate help](https://www.nimh.nih.gov/health/publications/my-mental-health-do-i-need-help)
- Crew readings: five persistent tiles for heart rate, SpO2, temperature,
  radiation, and HRV.
- Trends: anti-aliased rolling five-minute plots for heart rate and ambient
  radiation, with configured reference lines.
- Incident record: chronological, timestamped warnings, critical alerts, and
  resolutions.
- Simulation controls: a crew-age selector (26–46 years), clearly labeled
  synthetic scenarios for Hypoxia (30 s), Solar particle event (20 s), Fever
  (30 s), EVA exertion (25 s), Bradycardia (20 s), Cold exposure (25 s), and
  Autonomic strain (25 s), plus **End active scenarios** and
  **Export mission health log** actions. Scenarios in the same group replace
  one another; independent groups can run together, and each scenario expires
  automatically.
- About: project-license summary, live dependency versions, third-party
  attributions, and a link to the full local notices.

All records are explicitly synthetic. Thresholds are demonstration examples;
the interface does not claim clinical validation or mission certification.

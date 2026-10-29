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
  overall crew status, and an About action beside the status badge.
- Crew readings: five persistent tiles for heart rate, SpO2, temperature,
  radiation, and HRV.
- Trends: anti-aliased rolling five-minute plots for heart rate and ambient
  radiation, with configured reference lines.
- Incident record: chronological, timestamped warnings, critical alerts, and
  resolutions.
- Simulation controls: clearly labeled hypoxia, radiation, fever, recovery,
  and JSON export actions.
- About: project-license summary, live dependency versions, third-party
  attributions, and a link to the full local notices.

All records are explicitly synthetic. Thresholds are demonstration examples;
the interface does not claim clinical validation or mission certification.

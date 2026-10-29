# AstroHealth crew-health dashboard

## Mode

Operate

## User and task

Astronauts and mission medical/flight operations staff monitor a live synthetic
crew-health stream, inspect alert transitions, trigger demonstration scenarios,
and export the locally stored mission log.

## Success

The operator can identify current crew status, read all five labeled
measurements with their units and configured ranges, see the two live trend
plots, recognize new alerts, trigger or recover from a simulation scenario,
and export JSON without network access.

## Direction

Crew watch docket: mission context and readings stay visible together, with
timestamps and units adjacent to their values. Use the fixed AstroHealth palette
and 8px spacing grid. Keep severity legible in text as well as color.

## Constraints

- Desktop PyQt6 and PyQtGraph application; no web UI or network service.
- Worker-thread telemetry reaches the Qt interface through a Qt signal.
- SQLite persistence and JSON export operate locally.
- Readings and events are synthetic. Do not imply medical validation, NASA
  certification, real crew monitoring, or operational use.

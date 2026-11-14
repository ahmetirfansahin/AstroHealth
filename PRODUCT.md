# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop

## Stack

Python 3.10+, PyQt6, and PyQtGraph, as specified in the project brief.

## Users

Astronauts and mission medical/flight operations staff monitoring crew health during deep-space missions.

## Product Purpose

AstroHealth demonstrates offline-first crew health monitoring by simulating biometric telemetry, detecting configured anomalies, and presenting the resulting status and local health log to mission operators. Success means operators can inspect simulated vital signs, recognize manually triggered anomaly scenarios, and export a local health log.

## Positioning

An offline desktop dashboard combines a continuously running telemetry simulator, local SQLite history, and operator-triggered scenarios in one crew-health monitoring demonstration.

## Operating Context

The application is intended for desktop use in a deep-space mission scenario or NASA Space Apps Challenge demonstration. Operators monitor live simulated vital signs and alerts, trigger event scenarios, and export a structured JSON report without requiring network access.

## Capabilities and Constraints

- Simulate heart rate, blood oxygen, body temperature, ambient radiation, and heart-rate variability at one-second intervals.
- Trigger hypoxia, radiation spike, fever, and recovery scenarios manually.
- Classify telemetry against configured thresholds and record telemetry and anomaly incidents locally in SQLite.
- Export the latest mission health log as structured JSON.
- Offer the five-item English WHO-5 check offline. A score below 50 opens
  the support screen with a recommendation for further assessment.
  [WHO-5 scoring guidance](https://www.who.int/publications/m/item/who-ucn-msd-mhe-2024.01)
- Provide English emergency support instructions from a persistent dashboard
  action, available offline and independent of simulated readings. The screen
  directs crew to their onboard medical officer and mission procedure.
  [NASA spaceflight medical operations](https://www.nasa.gov/reference/6-0-medical-operations/)
  · [NIMH guidance on when to get immediate help](https://www.nimh.nih.gov/health/publications/my-mental-health-do-i-need-help)
- The displayed data is simulated; the application is a demonstration, not a medical device or a source of certified medical guidance. Thresholds require independent validation before any operational use.
- The app must remain useful offline and communicate telemetry safely between its worker thread and desktop UI.

## Brand Commitments

The product name is AstroHealth. The requested dashboard uses a deep navy/black background, glass-like dark panels, cyan highlights, green/yellow/red status indicators, a high-contrast sans-serif hierarchy, and an 8px spacing grid.

## Evidence on Hand

The project brief is the only product specification. No real crew data, clinical validation, mission integration, or external evidence has been provided; the application must not imply otherwise.

## Product Principles

- Make simulated health data and its status legible at a glance.
- Keep core monitoring, history, and export available offline.
- Make anomaly scenarios explicit and reproducible for demonstrations.
- Distinguish demonstrations from validated medical or operational guidance.

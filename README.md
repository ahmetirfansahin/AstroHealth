# AstroHealth

AstroHealth is an offline-first PyQt6 dashboard for a NASA Space Apps Challenge
crew-health monitoring demonstration. It generates synthetic biometric streams,
shows configured threshold alerts, stores records in a local SQLite database,
and exports them as JSON.

## Run

Python 3.10 or later is required.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Telemetry is stored locally at `~/.astrohealth/astrohealth.sqlite3`. Use the
dashboard controls to trigger a simulated hypoxia, radiation, or fever event,
or to clear active scenarios with Recovery. The export action saves all locally
stored telemetry and incident records to a JSON file. Select **About** beside
the crew status badge to view software attributions and license identifiers.
The full third-party notices are in [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

## License and attributions

AstroHealth is distributed under GPL-3.0-only; see [LICENSE](./LICENSE).
Third-party software licenses and attribution details are provided in
[THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) and the dashboard's About
window. AstroHealth is being developed for the NASA Space Apps Challenge.
NASA datasets and their source attributions will be documented as they are
integrated.

## Verification

```powershell
python -m unittest discover -s tests -v
```

All readings are simulated, and the threshold settings are demonstration
examples—not certified medical guidance or a validated flight-health system.

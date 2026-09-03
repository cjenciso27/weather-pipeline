# Global Weather Analytics & Alerting Pipeline

Production-grade, asynchronous API extraction pipeline built for the CENFOTEC
**SOFT-753 – Automation with Python** laboratory. It normalizes a dirty CSV of
global cities, extracts hourly forecasts from the
[Open-Meteo API](https://open-meteo.com/), aggregates them with pandas, and
produces an automated Excel report plus a JSON weather-alert payload.

## Features

- **City name normalization** with regular expressions and string manipulation
  (strip, replace, collapse whitespace, title-case).
- **Async API extraction** (`httpx.AsyncClient`) with configurable retries and
  a sequential per-city request loop, with total execution time logged.
- **Pandas transformations**: datetime conversion, missing-value handling, and
  daily aggregation (max temperature, total precipitation) per city.
- **Automated reporting**: formatted Excel export (`openpyxl`) and a JSON
  alert payload for cities exceeding 30 °C.
- **Logging** to `pipeline.log` with the level read dynamically from `.env`.
- **Tested** with pytest + `unittest.mock` (no network needed) and linted with
  Ruff, both enforced in CI on every pull request.

## Project structure

```
weather-pipeline/
├── src/
│   ├── pipeline.py       # Entry point: extraction + orchestration
│   ├── normalizer.py     # CSV parsing and city name normalization
│   ├── transform.py      # Pandas transformations and aggregation
│   ├── report.py         # Excel + JSON alert exports
│   └── logger_config.py  # Logging configuration (reads LOG_LEVEL)
├── tests/                # Pytest suite with mocked API calls
├── data/cities_raw.csv   # Raw input: 16 cities with dirty formatting
├── reports/              # Generated outputs (gitignored)
└── .github/workflows/ci.yml
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13+.

```bash
git clone <this-repo>
cd weather-pipeline
uv sync
cp .env.example .env   # adjust values if needed
```

### Configuration (`.env`)

| Variable            | Default   | Description                            |
| ------------------- | --------- | -------------------------------------- |
| `WEATHER_UNIT`      | `celsius` | Unit reported by the pipeline          |
| `MAX_RETRIES`       | `3`       | Retry attempts per failed API request  |
| `LOG_LEVEL`         | `INFO`    | Logging level for `pipeline.log`       |
| `ALERT_THRESHOLD_C` | `25`      | Configured alerting threshold (config) |

The JSON alert export uses the lab-specified fixed threshold of **> 30 °C**.

## Running the pipeline

```bash
uv run python -m src.pipeline
```

Outputs:

- `reports/weather_report.xlsx` — formatted daily report (max temperature and
  total precipitation per city per day).
- `reports/weather_alerts.json` — simplified alert payload for cities whose
  daily maximum exceeds 30 °C.
- `pipeline.log` — execution log.

## Testing and linting

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs the same checks
automatically on every pull request.

## Notes

- `truststore` is included so HTTPS calls also work behind corporate proxies
  that re-sign TLS traffic (the OS certificate store is used for validation).

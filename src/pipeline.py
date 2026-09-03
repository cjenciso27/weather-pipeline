"""Global Weather Analytics & Alerting Pipeline.

End-to-end flow: parse and normalize the input CSV, extract hourly
forecasts from the Open-Meteo API asynchronously (sequential requests,
with retries), aggregate with pandas, and export the Excel report plus
the JSON alert payload.

Run with: uv run python -m src.pipeline
"""

import asyncio
import os
import time

import httpx
import pandas as pd
import truststore
from dotenv import load_dotenv

from src.logger_config import get_logger
from src.normalizer import load_cities
from src.report import export_alerts_json, export_excel
from src.transform import aggregate_daily, hourly_to_dataframe, merge_with_cities

# Trust the operating system certificate store so HTTPS works behind
# corporate proxies that re-sign TLS traffic.
truststore.inject_into_ssl()
load_dotenv()

logger = get_logger(__name__)

CITIES_CSV = "data/cities_raw.csv"


class WeatherClient:
    """Async client for the Open-Meteo forecast API with retry support."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, http_client: httpx.AsyncClient, max_retries: int = 3):
        self._http = http_client
        self._max_retries = max_retries

    async def fetch_city(self, city: str, latitude: float, longitude: float) -> dict:
        """Fetch the hourly forecast for one location, retrying on failure."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation",
            "timezone": "auto",
        }
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._http.get(self.BASE_URL, params=params)
                response.raise_for_status()
                logger.info("Fetched forecast for %s (attempt %d)", city, attempt)
                return response.json()
            except (httpx.HTTPError, ValueError) as error:
                logger.error(
                    "Attempt %d/%d failed for %s: %s", attempt, self._max_retries, city, error
                )
                if attempt == self._max_retries:
                    raise
                await asyncio.sleep(2 ** (attempt - 1))
        raise RuntimeError("unreachable")  # pragma: no cover


async def extract_all(cities: list[dict], max_retries: int) -> dict[str, dict]:
    """Request data for every city sequentially and log total elapsed time."""
    payloads: dict[str, dict] = {}
    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        client = WeatherClient(http_client, max_retries=max_retries)
        for city in cities:
            try:
                payloads[city["city"]] = await client.fetch_city(
                    city["city"], city["latitude"], city["longitude"]
                )
            except httpx.HTTPError:
                logger.error("Giving up on %s after %d retries", city["city"], max_retries)

    elapsed = time.perf_counter() - start
    logger.info(
        "API extraction finished: %d/%d cities in %.2f seconds",
        len(payloads),
        len(cities),
        elapsed,
    )
    return payloads


def transform(cities: list[dict], payloads: dict[str, dict]) -> pd.DataFrame:
    """Build hourly frames, aggregate per city/day and merge with the catalog."""
    frames = [hourly_to_dataframe(city, payload) for city, payload in payloads.items()]
    hourly_df = pd.concat(frames, ignore_index=True)
    aggregated = aggregate_daily(hourly_df)
    return merge_with_cities(aggregated, cities)


async def run_pipeline() -> pd.DataFrame:
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    unit = os.getenv("WEATHER_UNIT", "celsius")
    alert_threshold = float(os.getenv("ALERT_THRESHOLD_C", "25"))
    logger.info(
        "Pipeline start | unit=%s max_retries=%d alert_threshold=%.1fC",
        unit,
        max_retries,
        alert_threshold,
    )

    cities = load_cities(CITIES_CSV)
    payloads = await extract_all(cities, max_retries)
    if not payloads:
        raise RuntimeError("No weather data could be extracted; aborting pipeline.")

    merged = transform(cities, payloads)
    export_excel(merged)
    export_alerts_json(merged)
    logger.info("Pipeline finished successfully with %d report rows", len(merged))
    return merged


def main() -> None:
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()

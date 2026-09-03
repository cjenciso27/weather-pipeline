"""Data transformation and aggregation with pandas.

Turns raw Open-Meteo JSON payloads into tidy DataFrames, handles missing
values, aggregates per city per day, and merges the results back with
the normalized city catalog from the input CSV.
"""

import pandas as pd

from src.logger_config import get_logger

logger = get_logger(__name__)


def hourly_to_dataframe(city: str, payload: dict) -> pd.DataFrame:
    """Convert one Open-Meteo JSON response into an hourly DataFrame.

    Timestamps are converted to pandas DateTime objects. Missing
    temperatures are dropped (they cannot be aggregated meaningfully)
    while missing precipitation values are treated as 0.0 mm.
    """
    hourly = payload.get("hourly", {})
    frame = pd.DataFrame(
        {
            "time": hourly.get("time", []),
            "temperature_2m": hourly.get("temperature_2m", []),
            "precipitation": hourly.get("precipitation", []),
        }
    )
    frame["city"] = city
    frame["time"] = pd.to_datetime(frame["time"])

    missing_temps = frame["temperature_2m"].isna().sum()
    if missing_temps:
        logger.warning("%s: dropping %d rows with missing temperature", city, missing_temps)
    frame = frame.dropna(subset=["temperature_2m"])
    frame["precipitation"] = frame["precipitation"].fillna(0.0)
    return frame


def aggregate_daily(hourly_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly data into max temperature and total precipitation
    per city per day."""
    daily = hourly_df.copy()
    daily["date"] = daily["time"].dt.date
    aggregated = (
        daily.groupby(["city", "date"])
        .agg(
            max_temperature_c=("temperature_2m", "max"),
            total_precipitation_mm=("precipitation", "sum"),
        )
        .reset_index()
    )
    logger.info("Aggregated %d hourly rows into %d city/day rows", len(hourly_df), len(aggregated))
    return aggregated


def merge_with_cities(aggregated_df: pd.DataFrame, cities: list[dict]) -> pd.DataFrame:
    """Join the aggregated weather statistics with the normalized city
    catalog (coordinates) coming from the original CSV."""
    cities_df = pd.DataFrame(cities)
    merged = pd.merge(cities_df, aggregated_df, on="city", how="inner")
    logger.info("Merged aggregates with city catalog: %d rows", len(merged))
    return merged

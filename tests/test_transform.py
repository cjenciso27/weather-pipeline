"""Unit tests for pandas transformations and aggregations."""

import pandas as pd
import pytest

from src.transform import aggregate_daily, hourly_to_dataframe, merge_with_cities


@pytest.fixture
def sample_payload() -> dict:
    return {
        "hourly": {
            "time": [
                "2026-09-01T00:00",
                "2026-09-01T12:00",
                "2026-09-02T00:00",
                "2026-09-02T12:00",
            ],
            "temperature_2m": [18.0, 27.5, 16.0, None],
            "precipitation": [0.0, 1.2, None, 3.4],
        }
    }


def test_hourly_to_dataframe_converts_timestamps_and_handles_missing(sample_payload):
    frame = hourly_to_dataframe("New York", sample_payload)

    assert pd.api.types.is_datetime64_any_dtype(frame["time"])
    # The row with the missing temperature is dropped.
    assert len(frame) == 3
    # Missing precipitation is treated as 0.0 mm.
    assert frame["precipitation"].isna().sum() == 0
    assert (frame["city"] == "New York").all()


def test_aggregate_daily_computes_max_temp_and_precip_sum(sample_payload):
    frame = hourly_to_dataframe("New York", sample_payload)

    daily = aggregate_daily(frame)

    day_one = daily[daily["date"] == pd.Timestamp("2026-09-01").date()].iloc[0]
    assert day_one["max_temperature_c"] == 27.5
    assert day_one["total_precipitation_mm"] == pytest.approx(1.2)


def test_merge_with_cities_joins_on_normalized_name(sample_payload):
    frame = hourly_to_dataframe("New York", sample_payload)
    daily = aggregate_daily(frame)
    cities = [{"city": "New York", "latitude": 40.7128, "longitude": -74.0060}]

    merged = merge_with_cities(daily, cities)

    assert len(merged) == len(daily)
    assert {"latitude", "longitude", "max_temperature_c"} <= set(merged.columns)

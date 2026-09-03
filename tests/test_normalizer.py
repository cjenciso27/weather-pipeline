"""Unit tests for city name normalization and CSV parsing."""

import pytest

from src.normalizer import load_cities, normalize_city_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  new YORK  ", "New York"),
        ("london!!", "London"),
        (" TOKYO# ", "Tokyo"),
        ("paris***", "Paris"),
        ("  são PAULO ", "São Paulo"),
        ("MEXICO   city", "Mexico City"),
        ("buenos__aires", "Buenos Aires"),
        ("   cairo@", "Cairo"),
        ("san    JOSÉ  ", "San José"),
        ("seoul##", "Seoul"),
    ],
)
def test_normalize_city_name(raw: str, expected: str):
    assert normalize_city_name(raw) == expected


def test_load_cities_normalizes_and_parses_coordinates(tmp_path):
    csv_file = tmp_path / "cities.csv"
    csv_file.write_text(
        'city_name,latitude,longitude\n"  new YORK  ",40.7128,-74.0060\n',
        encoding="utf-8",
    )

    cities = load_cities(csv_file)

    assert cities == [{"city": "New York", "latitude": 40.7128, "longitude": -74.0060}]


def test_load_cities_skips_malformed_rows(tmp_path):
    csv_file = tmp_path / "cities.csv"
    csv_file.write_text(
        "city_name,latitude,longitude\nlondon!!,not-a-number,-0.1278\nparis,48.8566,2.3522\n",
        encoding="utf-8",
    )

    cities = load_cities(csv_file)

    assert len(cities) == 1
    assert cities[0]["city"] == "Paris"

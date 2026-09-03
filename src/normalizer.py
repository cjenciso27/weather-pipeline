"""CSV input parsing and city name normalization.

The raw input CSV contains intentionally dirty city names (erratic
capitalization, trailing spaces, special characters). This module cleans
them using regular expressions and string manipulation.
"""

import csv
import re
from pathlib import Path

from src.logger_config import get_logger

logger = get_logger(__name__)

# Anything that is not a letter (including accented ones), space,
# hyphen or apostrophe is considered noise.
_NOISE_PATTERN = re.compile(r"[^a-zA-ZÀ-ÿ\s'-]")
_UNDERSCORE_PATTERN = re.compile(r"_+")
_MULTISPACE_PATTERN = re.compile(r"\s+")


def normalize_city_name(raw_name: str) -> str:
    """Normalize a dirty city name into clean Title Case.

    Steps: underscores become spaces, special characters are removed,
    whitespace is collapsed and stripped, and the result is title-cased.
    """
    name = _UNDERSCORE_PATTERN.sub(" ", raw_name)
    name = _NOISE_PATTERN.sub("", name)
    name = _MULTISPACE_PATTERN.sub(" ", name).strip()
    return name.title()


def load_cities(csv_path: str | Path) -> list[dict]:
    """Parse the raw cities CSV and return normalized city records.

    Each record contains the normalized city name plus its coordinates
    as floats. Rows with invalid coordinates are skipped and logged.
    """
    csv_path = Path(csv_path)
    cities: list[dict] = []

    logger.info("Loading cities from %s", csv_path)
    with csv_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw_name = row.get("city_name", "")
            try:
                city = {
                    "city": normalize_city_name(raw_name),
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
            except (KeyError, TypeError, ValueError):
                logger.error("Skipping malformed CSV row: %s", row)
                continue
            logger.info("Normalized city name %r -> %r", raw_name, city["city"])
            cities.append(city)

    logger.info("Loaded %d cities from CSV", len(cities))
    return cities

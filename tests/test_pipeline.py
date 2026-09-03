"""Tests for the API client using unittest.mock (no network required)."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.pipeline import WeatherClient


def make_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


@pytest.mark.asyncio
async def test_fetch_city_returns_parsed_json():
    payload = {"hourly": {"time": [], "temperature_2m": [], "precipitation": []}}
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.return_value = make_response(payload)

    client = WeatherClient(http, max_retries=3)
    result = await client.fetch_city("Tokyo", 35.6762, 139.6503)

    assert result == payload
    http.get.assert_awaited_once()
    params = http.get.await_args.kwargs["params"]
    assert params["hourly"] == "temperature_2m,precipitation"
    assert params["timezone"] == "auto"


@pytest.mark.asyncio
async def test_fetch_city_retries_then_succeeds():
    payload = {"hourly": {}}
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.side_effect = [
        httpx.ConnectError("boom"),
        make_response(payload),
    ]

    client = WeatherClient(http, max_retries=3)
    result = await client.fetch_city("Cairo", 30.0444, 31.2357)

    assert result == payload
    assert http.get.await_count == 2


@pytest.mark.asyncio
async def test_fetch_city_raises_after_max_retries():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.side_effect = httpx.ConnectError("network down")

    client = WeatherClient(http, max_retries=2)
    with pytest.raises(httpx.ConnectError):
        await client.fetch_city("Berlin", 52.52, 13.405)

    assert http.get.await_count == 2

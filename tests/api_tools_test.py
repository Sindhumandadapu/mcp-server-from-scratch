
import pytest

from tools.api_tools import validate_api_url


@pytest.mark.asyncio
async def test_weather_tool(mcp_client, monkeypatch):

    async def mock_fetch_json(url, params=None):

        if "geocoding-api" in url:
            return {
                "results": [
                    {
                        "name": "Hyderabad",
                        "latitude": 17.385,
                        "longitude": 78.4867,
                        "country": "India",
                    }
                ]
            }

        return {
            "current": {
                "temperature_2m": 30,
                "relative_humidity_2m": 60,
                "apparent_temperature": 32,
                "weather_code": 1,
                "wind_speed_10m": 10,
            }
        }

    monkeypatch.setattr(
        "tools.api_tools.fetch_json",
        mock_fetch_json
    )

    async with mcp_client() as client:
        result = await client.call_tool(
            "get_weather",
            {
                "city": "Hyderabad",
                "country_code": "IN",
                "temperature_unit": "celsius",
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_currency_conversion(mcp_client, monkeypatch):

    async def mock_fetch_json(url, params=None):
        return {
            "rate": 85.0
        }

    monkeypatch.setattr(
        "tools.api_tools.fetch_json",
        mock_fetch_json
    )

    async with mcp_client() as client:
        result = await client.call_tool(
            "convert_currency",
            {
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "INR",
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_same_currency_conversion(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "convert_currency",
            {
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "USD",
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_approved_generic_api(mcp_client, monkeypatch):

    async def mock_fetch_json(url, params=None):
        return {
            "status": "success",
            "message": "Mock API response",
        }

    monkeypatch.setattr(
        "tools.api_tools.fetch_json",
        mock_fetch_json
    )

    async with mcp_client() as client:
        result = await client.call_tool(
            "make_api_request",
            {
                "url": (
                    "https://api.open-meteo.com/v1/forecast"
                    "?latitude=17.385&longitude=78.4867"
                    "&current=temperature_2m"
                )
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_unapproved_host_rejected(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "make_api_request",
            {
                "url": "https://example.com/api"
            }
        )

        assert result.is_error


@pytest.mark.parametrize(
    "url",
    [
        "http://api.open-meteo.com/v1/forecast",
        "https://example.com/api",
        "https://user:password@api.open-meteo.com/v1/forecast",
        "https://api.open-meteo.com:8080/v1/forecast",
        "https://api.open-meteo.com/v1/forecast#fragment",
        "https://api.open-meteo.com/v1/forecast?api_key=secret",
    ],
)
def test_unsafe_urls_rejected(url):

    with pytest.raises(ValueError):
        validate_api_url(url)

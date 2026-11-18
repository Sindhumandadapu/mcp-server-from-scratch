
import json
import math
import re
from urllib.parse import urlsplit

import httpx


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

ALLOWED_API_HOSTS = {
    "api.open-meteo.com",
    "geocoding-api.open-meteo.com",
    "api.frankfurter.dev",
}

REQUEST_TIMEOUT = 10.0
MAX_RESPONSE_BYTES = 64 * 1024  # 64 KB


# ---------------------------------------------------------
# SHARED HTTP CLIENT FUNCTION
# ---------------------------------------------------------

async def fetch_json(
    url: str,
    params: dict | None = None,
) -> dict | list:
    """
    Fetch JSON data from an external API.

    Security:
    - Request timeout
    - Redirects disabled
    - Response size limited to 64 KB
    - Only successful HTTP responses accepted
    """

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=False,
    ) as client:

        async with client.stream(
            "GET",
            url,
            params=params,
            headers={"Accept": "application/json"},
        ) as response:

            body = bytearray()

            async for chunk in response.aiter_bytes():

                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise ValueError(
                        "API response exceeds the 64 KB limit."
                    )

                body.extend(chunk)

            if not 200 <= response.status_code < 300:

                message = body.decode(
                    "utf-8",
                    errors="replace",
                )[:500]

                raise ValueError(
                    f"External API returned HTTP "
                    f"{response.status_code}: {message}"
                )

            try:
                return json.loads(body)

            except json.JSONDecodeError as exc:
                raise ValueError(
                    "External API returned invalid JSON."
                ) from exc


# ---------------------------------------------------------
# URL VALIDATION
# ---------------------------------------------------------

def validate_api_url(url: str) -> str:
    """
    Validate URLs for the generic API request tool.

    Only approved HTTPS hosts are allowed.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid API URL is required.")

    if len(url) > 2048:
        raise ValueError("API URL is too long.")

    parsed = urlsplit(url.strip())

    if parsed.scheme != "https":
        raise ValueError("Only HTTPS API URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("A valid API hostname is required.")

    if parsed.username or parsed.password:
        raise ValueError(
            "URLs containing credentials are not allowed."
        )

    try:
        port = parsed.port

    except ValueError as exc:
        raise ValueError("Invalid URL port.") from exc

    if port not in (None, 443):
        raise ValueError(
            "Only the standard HTTPS port 443 is allowed."
        )

    hostname = parsed.hostname.lower()

    if hostname not in ALLOWED_API_HOSTS:
        raise ValueError(
            f"Host '{hostname}' is not approved. "
            f"Allowed hosts: {', '.join(sorted(ALLOWED_API_HOSTS))}"
        )

    if parsed.fragment:
        raise ValueError("URL fragments are not allowed.")

    sensitive_keys = {
        "key",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "password",
        "secret",
    }

    query_keys = {
        part.split("=", 1)[0].lower()
        for part in parsed.query.split("&")
        if part
    }

    if query_keys.intersection(sensitive_keys):
        raise ValueError(
            "Do not put API secrets in URL query parameters."
        )

    return url.strip()


# ---------------------------------------------------------
# WEATHER CODE DESCRIPTION
# ---------------------------------------------------------

def weather_description(code: int) -> str:
    """
    Convert WMO weather codes into readable descriptions.
    """

    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return descriptions.get(
        code,
        "Unknown weather condition",
    )


# ---------------------------------------------------------
# MCP TOOL REGISTRATION
# ---------------------------------------------------------

def register_api_tools(mcp):
    """
    Register external API tools with the MCP server.
    """

    # -----------------------------------------------------
    # TOOL 1: WEATHER API
    # -----------------------------------------------------

    @mcp.tool()
    async def get_weather(
        city: str,
        country_code: str = "",
        temperature_unit: str = "celsius",
    ) -> str:
        """
        Get current weather conditions for a city.

        Parameters:
            city: City name.
            country_code: Optional two-letter country code.
            temperature_unit: celsius or fahrenheit.

        Uses Open-Meteo APIs.
        No API key is required.
        """

        if not isinstance(city, str):
            raise ValueError("City must be a string.")

        city = city.strip()

        if len(city) < 2 or len(city) > 100:
            raise ValueError(
                "City name must contain between 2 and 100 characters."
            )

        if temperature_unit not in {
            "celsius",
            "fahrenheit",
        }:
            raise ValueError(
                "temperature_unit must be celsius or fahrenheit."
            )

        if not isinstance(country_code, str):
            raise ValueError("Country code must be a string.")

        country_code = country_code.strip().upper()

        if country_code and not re.fullmatch(
            r"[A-Z]{2}",
            country_code,
        ):
            raise ValueError(
                "country_code must be a two-letter country code."
            )

        # Step 1: Find city coordinates.

        locations = await fetch_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 5,
                "language": "en",
                **(
                    {"countryCode": country_code}
                    if country_code
                    else {}
                ),
            },
        )

        results = locations.get("results", [])

        if not results:
            raise ValueError(
                f"No location found for '{city}'."
            )

        location = results[0]

        # Step 2: Get weather for coordinates.

        weather = await fetch_json(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "is_day,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m,"
                    "wind_direction_10m"
                ),
                "temperature_unit": temperature_unit,
                "timezone": "auto",
            },
        )

        current = weather.get("current", {})
        units = weather.get("current_units", {})

        code = current.get("weather_code")

        result = {
            "location": {
                "city": location.get("name"),
                "state": location.get("admin1"),
                "country": location.get("country"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "timezone": location.get("timezone"),
            },
            "current_weather": {
                "temperature": current.get("temperature_2m"),
                "temperature_unit": units.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "weather": (
                    weather_description(code)
                    if code is not None
                    else None
                ),
                "weather_code": code,
                "wind_speed": current.get("wind_speed_10m"),
                "wind_speed_unit": units.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "precipitation": current.get("precipitation"),
                "time": current.get("time"),
                "is_day": current.get("is_day"),
            },
            "source": "Open-Meteo",
        }

        return json.dumps(result, indent=2)

    # -----------------------------------------------------
    # TOOL 2: CURRENCY CONVERSION API
    # -----------------------------------------------------

    @mcp.tool()
    async def convert_currency(
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> str:
        """
        Convert an amount between two currencies.

        Parameters:
            amount: Amount to convert.
            from_currency: Source currency code, e.g. USD.
            to_currency: Target currency code, e.g. INR.

        Uses Frankfurter reference exchange rates.
        No API key is required.
        """

        if not isinstance(amount, (int, float)):
            raise ValueError("Amount must be a number.")

        if not math.isfinite(amount) or amount < 0:
            raise ValueError(
                "Amount must be a finite, non-negative number."
            )

        if not isinstance(from_currency, str):
            raise ValueError(
                "from_currency must be a string."
            )

        if not isinstance(to_currency, str):
            raise ValueError(
                "to_currency must be a string."
            )

        source = from_currency.strip().upper()
        target = to_currency.strip().upper()

        if not re.fullmatch(r"[A-Z]{3}", source):
            raise ValueError(
                "from_currency must be a three-letter currency code."
            )

        if not re.fullmatch(r"[A-Z]{3}", target):
            raise ValueError(
                "to_currency must be a three-letter currency code."
            )

        # Same currency: no API call needed.

        if source == target:

            result = {
                "amount": amount,
                "from_currency": source,
                "to_currency": target,
                "exchange_rate": 1.0,
                "converted_amount": round(amount, 2),
                "rate_date": None,
                "source": "Frankfurter",
            }

            return json.dumps(result, indent=2)

        # Fetch exchange rate.

        data = await fetch_json(
            (
                "https://api.frankfurter.dev/v2/rate/"
                f"{source.lower()}/{target.lower()}"
            )
        )

        if not isinstance(data, dict) or "rate" not in data:
            raise ValueError(
                "Currency API returned an unexpected response."
            )

        rate = float(data["rate"])

        if not math.isfinite(rate) or rate <= 0:
            raise ValueError(
                "Currency API returned an invalid exchange rate."
            )

        result = {
            "amount": amount,
            "from_currency": source,
            "to_currency": target,
            "exchange_rate": rate,
            "converted_amount": round(
                amount * rate,
                2,
            ),
            "rate_date": data.get("date"),
            "source": "Frankfurter",
            "note": (
                "Reference exchange rate; "
                "not a live trading quote."
            ),
        }

        return json.dumps(result, indent=2)

    # -----------------------------------------------------
    # TOOL 3: CONTROLLED GENERIC API REQUEST
    # -----------------------------------------------------

    @mcp.tool()
    async def make_api_request(url: str) -> str:
        """
        Make a controlled GET request to an approved public API.

        Only HTTPS requests to configured allowlisted hosts
        are allowed.

        Redirects are disabled and responses are limited to 64 KB.
        """

        safe_url = validate_api_url(url)

        data = await fetch_json(safe_url)

        return json.dumps(
            {
                "status": "success",
                "url": safe_url,
                "data": data,
            },
            indent=2,
        )

    # Three tools are registered.

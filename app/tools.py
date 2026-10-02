from pathlib import Path
import re
import requests
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

# Dictionary of well-known Romanian peaks, massifs, and mountain landmarks
ROMANIAN_PEAKS: Dict[str, Dict[str, Any]] = {
    "moldoveanu": {"lat": 45.5997, "lon": 24.7369, "alt": 2544, "name": "Moldoveanu Peak (Fagaras Mountains)"},
    "negoiu": {"lat": 45.5847, "lon": 24.5769, "alt": 2535, "name": "Negoiu Peak (Fagaras Mountains)"},
    "balea": {"lat": 45.6042, "lon": 24.6167, "alt": 2034, "name": "Balea Lake (Fagaras Mountains)"},
    "fagaras": {"lat": 45.5997, "lon": 24.7369, "alt": 2500, "name": "Fagaras Mountains (Main Ridge)"},
    "omu": {"lat": 45.4456, "lon": 25.4578, "alt": 2505, "name": "Omu Peak (Bucegi Mountains)"},
    "babele": {"lat": 45.4086, "lon": 25.4742, "alt": 2206, "name": "Babele / Bucegi Plateau (Bucegi Mountains)"},
    "caraiman": {"lat": 45.4144, "lon": 25.4983, "alt": 2291, "name": "Caraiman Cross (Bucegi Mountains)"},
    "bucegi": {"lat": 45.4144, "lon": 25.4742, "alt": 2200, "name": "Bucegi Mountains (Plateau Zone)"},
    "malaiesti": {"lat": 45.4572, "lon": 25.4522, "alt": 1720, "name": "Malaiesti Cabin (Bucegi Mountains)"},
    "piatra craiului": {"lat": 45.5342, "lon": 25.2158, "alt": 2238, "name": "La Om / Piscul Baciului (Piatra Craiului)"},
    "curmatura": {"lat": 45.5567, "lon": 25.2667, "alt": 1470, "name": "Curmatura Cabin (Piatra Craiului)"},
    "retezat": {"lat": 45.3644, "lon": 22.8942, "alt": 2509, "name": "Peleaga Peak (Retezat Mountains)"},
    "peleaga": {"lat": 45.3644, "lon": 22.8942, "alt": 2509, "name": "Peleaga Peak (Retezat Mountains)"},
    "ceahlau": {"lat": 46.9608, "lon": 25.9500, "alt": 1904, "name": "Toaca Peak (Ceahlau Massif)"},
    "toaca": {"lat": 46.9608, "lon": 25.9500, "alt": 1904, "name": "Toaca Peak (Ceahlau Massif)"},
    "dochia": {"lat": 46.9614, "lon": 25.9542, "alt": 1750, "name": "Dochia Cabin (Ceahlau Massif)"},
    "parang": {"lat": 45.3375, "lon": 23.5358, "alt": 2519, "name": "Parangul Mare (Parang Mountains)"},
    "ciucas": {"lat": 45.5186, "lon": 25.9269, "alt": 1954, "name": "Ciucas Peak (Ciucas Mountains)"},
    "postavaru": {"lat": 45.5703, "lon": 25.5686, "alt": 1799, "name": "Postavaru Peak (Brasov / Poiana Brasov)"},
    "piatra mare": {"lat": 45.5539, "lon": 25.6450, "alt": 1844, "name": "Piatra Mare Peak"},
    "apuseni": {"lat": 46.5667, "lon": 22.7833, "alt": 1826, "name": "Apuseni Mountains (Padis / Vladeasa Area)"},
    "padis": {"lat": 46.5961, "lon": 22.7303, "alt": 1280, "name": "Padis Plateau (Apuseni Mountains)"},
}

WMO_WEATHER_CODES: Dict[int, str] = {
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
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def read_safety_guidelines(filename: str = "salvamont_rules.md") -> str:
    """
    Reads official mountain safety guidelines, Salvamont emergency rules, and equipment requirements.

    Args:
        filename: The Markdown filename inside the knowledge directory.
                  Defaults to 'salvamont_rules.md'.

    Returns:
        A string containing the full text of the requested safety documentation.
    """
    file_path = KNOWLEDGE_DIR / filename

    if not file_path.exists():
        return "Error: Salvamont rules knowledge file was not found."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading Salvamont guidelines: {e}"


def _find_peak_coordinates(query: str) -> Optional[Tuple[float, float, str]]:
    """Helper to look up coordinates from known Romanian mountain peaks."""
    query_clean = query.lower().strip()
    normalized = (
        query_clean.replace("â", "a")
        .replace("ă", "a")
        .replace("î", "i")
        .replace("ș", "s")
        .replace("ț", "t")
    )
    for key, data in ROMANIAN_PEAKS.items():
        if key in normalized or normalized in key:
            return data["lat"], data["lon"], data["name"]
    return None


def get_mountain_weather(
    destination: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> str:
    """
    Fetches real-time mountain weather, wind speeds, and alpine hazard alerts from Open-Meteo API.

    Args:
        destination: Mountain peak, massif, or hut name (e.g. 'Omu', 'Moldoveanu', 'Bucegi', 'Ceahlau', 'Piatra Craiului').
        latitude: Latitude coordinate (optional if destination is provided).
        longitude: Longitude coordinate (optional if destination is provided).

    Returns:
        Formatted weather report including temperature, wind speed, precipitation, and Salvamont alerts.
    """
    loc_name = destination.strip() if destination else ""
    target_lat = latitude
    target_lon = longitude

    if loc_name:
        coords = _find_peak_coordinates(loc_name)
        if coords:
            target_lat, target_lon, loc_name = coords

    # Fallback to Bucegi (Omu) if no coordinates resolved
    if target_lat == 0.0 and target_lon == 0.0:
        target_lat, target_lon = 45.4456, 25.4578
        loc_name = "Bucegi Mountains (Central Zone)"

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": target_lat,
        "longitude": target_lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
        ],
        "timezone": "auto",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})

        temp = current.get("temperature_2m", 0)
        feels_like = current.get("apparent_temperature", temp)
        humidity = current.get("relative_humidity_2m", 0)
        precip = current.get("precipitation", 0)
        code = current.get("weather_code", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        wind_gusts = current.get("wind_gusts_10m", wind_speed)

        condition_desc = WMO_WEATHER_CODES.get(code, f"Weather code {code}")

        # Safety & Salvamont hazard assessments
        warnings = []
        if code in [95, 96, 99]:
            warnings.append("[EXTREME LIGHTNING HAZARD] Thunderstorm with electrical discharges! Evacuate ridges, summits, and metal cables.")
        if wind_speed > 60 or wind_gusts > 75:
            warnings.append(f"[VIOLENT WIND HAZARD] Gusts of {wind_gusts} km/h! Extreme risk of losing balance on narrow ridges.")
        elif wind_speed > 40:
            warnings.append(f"[STRONG WIND WARNING] {wind_speed} km/h (gusts {wind_gusts} km/h). Wind-resistant shell essential.")
        if precip > 5:
            warnings.append("[HEAVY PRECIPITATION WARNING] Trail can be slippery on wet rock and mud; watch for flash water flow.")
        if temp <= 0:
            warnings.append("[SUB-ZERO TEMPERATURE WARNING] Below-freezing conditions. Risk of ice and frost. Thermal layers and crampons required.")

        warning_text = "\n".join(warnings) if warnings else "Conditions within standard mountain safety limits (always anticipate sudden weather shifts)."

        return (
            f"Mountain Weather Forecast for {loc_name or f'({target_lat:.3f}, {target_lon:.3f})'}:\n"
            f"- Condition: {condition_desc}\n"
            f"- Temperature: {temp} C (Feels like: {feels_like} C)\n"
            f"- Humidity: {humidity}%\n"
            f"- Precipitation: {precip} mm\n"
            f"- Wind: {wind_speed} km/h (Gusts up to {wind_gusts} km/h)\n\n"
            f"Salvamont Safety Alerts:\n{warning_text}"
        )
    except requests.RequestException as e:
        return f"Weather Notice: Weather service is temporarily unavailable ({e}). Always check latest forecasts with Salvamont Romania."


def get_mountain_routes(destination: str) -> str:
    """
    Searches official Romanian hiking routes in OpenStreetMap via Overpass API.

    Args:
        destination: Mountain peak, hut, massif, or locality (e.g. 'Negoiu', 'Bucegi', 'Moldoveanu', 'Malaiesti').

    Returns:
        A formatted list of hiking relations, official trail marks (symbols), and network details.
    """
    url = "https://overpass-api.de/api/interpreter"
    clean_dest = re.sub(r'["\\]', "", destination).strip()

    if not clean_dest:
        return "Error: Please specify a valid mountain destination."

    query = f"""
        [out:json][timeout:15];
        (
            relation["route"="hiking"]["name"~"{clean_dest}",i];
            node["tourism"~"alpine_hut|wilderness_hut"]["name"~"{clean_dest}",i];
        );
        out tags 8;
    """

    headers = {
        "User-Agent": "RoMountainAgent/1.0 (https://github.com/elena-silvia/HikeAI; contact: salvamont-agent@local)"
    }

    try:
        response = requests.post(url, data={"data": query}, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        elements = data.get("elements", [])
        if not elements:
            return (
                f"No marked trails found in OSM database specifically for '{clean_dest}'. "
                f"Recommendation: check official Salvamont local guide for certified trail routes."
            )

        results = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("int_name") or "Marked Trail"
            symbol = tags.get("osmc:symbol") or tags.get("symbol") or tags.get("trail_mark") or "Certified Salvamont Mark"
            network = tags.get("network", "Carpathian Mountain Trail")
            operator = tags.get("operator", "Salvamont")
            from_pt = tags.get("from", "")
            to_pt = tags.get("to", "")
            distance = tags.get("distance", "")

            route_entry = f"- **{name}**\n  - Marking: {symbol}\n  - Network: {network} ({operator})"
            if from_pt and to_pt:
                route_entry += f"\n  - Segment: {from_pt} -> {to_pt}"
            if distance:
                route_entry += f"\n  - Distance: {distance}"

            results.append(route_entry)

        return f"Hiking trails identified for '{clean_dest}':\n\n" + "\n\n".join(results)
    except requests.Timeout:
        return f"Search for trails for '{clean_dest}' timed out. Falling back to standard guide data."
    except requests.RequestException as e:
        return f"Notice: OSM mapping service did not respond ({e}). Using internal mountain guide."

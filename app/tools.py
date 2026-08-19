from idlelib.rpc import response_queue
from pathlib import Path
import requests
from typing import Dict, Any, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

def read_safety_guidelines(filename: str = "salvamont_rules.md") -> str:
    """
        Reads mountain safety guidelines, Salvamont emergency rules, and equipment requirements.

        Args:
            filename: The Markdown filename inside the knowledge directory.
                      Defaults to 'salvamont_rules.md'.

        Returns:
            A string containing the full text of the requested safety documentation.
        """
    file_path = KNOWLEDGE_DIR / filename

    if not file_path.exists():
        return "Error: knowledge file was not found"

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_mountain_weather(latitude: float, longitude: float) -> str:
    """
        Reads mountain safety guidelines, Salvamont emergency rules, and equipment requirements.

        Args:
            filename: The Markdown filename inside the knowledge directory.
                      Defaults to 'salvamont_rules.md'.

        Returns:
            A string containing the full text of the requested safety documentation.
        """
    url="https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current":[
            "temperature_2m",
            "humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed",
        ],
        "timezone":"auto"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        current = data.get("current",{})

        return(
            f"Current information at ({latitude},{longitude}):\n"
            f"Temperature {current.get('temperature_2m')}\n"
            f"Humidity {current.get('humidity_2m')}\n"
            f"Precipitation {current.get('precipitation')} mm\n"
            f"Wind speed {current.get('wind_speed')} km/h\n"
        )
    except:
        return "Error: unable to retrieve data"

def get_mountain_routes(destination: str) ->str:
    """
    Searches for global/Romanian hiking routes in OpenStreetMap via Overpass API.
    Args:
        destination: Mountain peak, hut, or locality (e.g., 'Negoiu', 'Bucegi', 'Moldoveanu').
    Returns:
        A formatted list of hiking relations, trail marks, and network details from OSM.
    """

    url = "https://overpass-api.de/api/interpreter"
    query = f"""
        [out:json][timeout:15];
        (
            relation["route"="hiking"]["name"~"{destination}",i];
            node["tourism"~"alpine_hut|willderness_hut"]["name"~"{destination}",i]
        );
        out tags 10;
    """

    try:
        response = requests.post(url, data={"data":query}, timeout=15)
        response.raise_for_status()
        data = response.json()

        elements = data.get["elements",[]]
        if not elements:
            return f"No hiking routes found for {destination}"
        results = []
        for el in elements:
            tags = el.get("tags",{})
            name = tags.get("name","Unnamed Route")
            symbol = tags.get("osmc:symbol") or tags.get("symbol")
            network = tags.get("network", "Local/Region Trail")
            operator = tags.get("operator", "Salvamont/Forestry")

            results.append(
                f"Name: {name}\n"
                f"Symbol: {symbol}\n"
                f"Network: {network}\n"
                f"Operator: {operator}\n"
            )
            return "\n".join(results)
    except requests.RequestException:
        return "Error: unable to retrieve data"



import json
import logging
import re
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

logger = logging.getLogger("CartographerAgent")

# Ground-truth Romanian mountain landmarks with verified GPS coordinates and elevations
CARPATHIAN_LANDMARKS: Dict[str, Dict[str, Any]] = {
    # Fagaras Mountains
    "balea lac": {"lat": 45.6042, "lon": 24.6167, "elevation": 2034, "type": "trailhead", "desc": "Balea Lake & Cabins"},
    "balea cascada": {"lat": 45.6358, "lon": 24.6178, "elevation": 1234, "type": "trailhead", "desc": "Balea Waterfall cable-car base"},
    "saua caprei": {"lat": 45.6000, "lon": 24.6300, "elevation": 2315, "type": "pass", "desc": "Capra Saddle"},
    "lacul capra": {"lat": 45.5986, "lon": 24.6303, "elevation": 2230, "type": "water", "desc": "Capra Glacial Lake & Monument"},
    "fereastra zmeilor": {"lat": 45.5894, "lon": 24.6592, "elevation": 2175, "type": "pass", "desc": "Dragons Window pass"},
    "podragu": {"lat": 45.6172, "lon": 24.6869, "elevation": 2156, "type": "cabin", "desc": "Podragu Alpine Cabin"},
    "cabana podragu": {"lat": 45.6172, "lon": 24.6869, "elevation": 2156, "type": "cabin", "desc": "Podragu Alpine Cabin"},
    "saua podragului": {"lat": 45.6050, "lon": 24.6850, "elevation": 2307, "type": "pass", "desc": "Podragu Saddle"},
    "vistea mare": {"lat": 45.6022, "lon": 24.7336, "elevation": 2527, "type": "summit", "desc": "Vistea Mare Peak"},
    "moldoveanu": {"lat": 45.5997, "lon": 24.7369, "elevation": 2544, "type": "summit", "desc": "Moldoveanu Peak - Roof of Romania"},
    "varful moldoveanu": {"lat": 45.5997, "lon": 24.7369, "elevation": 2544, "type": "summit", "desc": "Moldoveanu Peak (2544m)"},
    "negoiu": {"lat": 45.5847, "lon": 24.5769, "elevation": 2535, "type": "summit", "desc": "Negoiu Peak (2535m)"},
    "varful negoiu": {"lat": 45.5847, "lon": 24.5769, "elevation": 2535, "type": "summit", "desc": "Negoiu Peak (2535m)"},
    "strunga dracului": {"lat": 45.5860, "lon": 24.5820, "elevation": 2410, "type": "pass", "desc": "Devils Gully chimney pass"},
    "cabana negoiu": {"lat": 45.6094, "lon": 24.5492, "elevation": 1545, "type": "cabin", "desc": "Negoiu Cabin"},
    "cabana barcaciu": {"lat": 45.6200, "lon": 24.4700, "elevation": 1550, "type": "cabin", "desc": "Barcaciu Cabin"},
    "cabana suru": {"lat": 45.6139, "lon": 24.4250, "elevation": 1450, "type": "cabin", "desc": "Suru Cabin"},

    # Bucegi Mountains
    "busteni": {"lat": 45.4180, "lon": 25.5330, "elevation": 930, "type": "trailhead", "desc": "Busteni Trailhead (Silva)"},
    "gura diham": {"lat": 45.4320, "lon": 25.5050, "elevation": 987, "type": "trailhead", "desc": "Gura Diham Inn & Trailhead"},
    "cabana diham": {"lat": 45.4489, "lon": 25.4956, "elevation": 1320, "type": "cabin", "desc": "Diham Cabin"},
    "poiana izvoarelor": {"lat": 45.4394, "lon": 25.4939, "elevation": 1455, "type": "cabin", "desc": "Poiana Izvoarelor Cabin"},
    "cascada urlatoarea": {"lat": 45.4056, "lon": 25.5236, "elevation": 1100, "type": "water", "desc": "Urlatoarea Waterfall"},
    "babele": {"lat": 45.4086, "lon": 25.4742, "elevation": 2206, "type": "cabin", "desc": "Babele Cabin & Plateau"},
    "cabana babele": {"lat": 45.4086, "lon": 25.4742, "elevation": 2206, "type": "cabin", "desc": "Babele Cabin"},
    "sfinxul": {"lat": 45.4075, "lon": 25.4740, "elevation": 2216, "type": "landmark", "desc": "Bucegi Sphinx Rock"},
    "caraiman": {"lat": 45.4144, "lon": 25.4983, "elevation": 2291, "type": "landmark", "desc": "Heroes Cross on Caraiman Peak"},
    "crucea caraiman": {"lat": 45.4144, "lon": 25.4983, "elevation": 2291, "type": "landmark", "desc": "Heroes Cross on Caraiman Peak"},
    "cabana caraiman": {"lat": 45.4111, "lon": 25.4950, "elevation": 2025, "type": "cabin", "desc": "Caraiman Cabin"},
    "omu": {"lat": 45.4456, "lon": 25.4578, "elevation": 2505, "type": "summit", "desc": "Omu Peak & Cabin (2505m)"},
    "varful omu": {"lat": 45.4456, "lon": 25.4578, "elevation": 2505, "type": "summit", "desc": "Omu Peak & Cabin (2505m)"},
    "cabana omu": {"lat": 45.4456, "lon": 25.4578, "elevation": 2505, "type": "cabin", "desc": "Omu Alpine Cabin (2505m)"},
    "malaiesti": {"lat": 45.4572, "lon": 25.4522, "elevation": 1720, "type": "cabin", "desc": "Malaiesti Valley Cabin"},
    "cabana malaiesti": {"lat": 45.4572, "lon": 25.4522, "elevation": 1720, "type": "cabin", "desc": "Malaiesti Valley Cabin"},
    "padina": {"lat": 45.3658, "lon": 25.4336, "elevation": 1525, "type": "cabin", "desc": "Padina Cabin / Ialomita Valley"},
    "cabana padina": {"lat": 45.3658, "lon": 25.4336, "elevation": 1525, "type": "cabin", "desc": "Padina Cabin"},
    "pestera ialomitei": {"lat": 45.3789, "lon": 25.4358, "elevation": 1530, "type": "landmark", "desc": "Ialomita Cave & Monastery"},
    "saua strunga": {"lat": 45.3606, "lon": 25.3789, "elevation": 1909, "type": "pass", "desc": "Strunga Saddle Refuge"},
    "sinaia": {"lat": 45.3520, "lon": 25.5510, "elevation": 860, "type": "trailhead", "desc": "Sinaia Resort Trailhead"},
    "cota 1400": {"lat": 45.3560, "lon": 25.5340, "elevation": 1400, "type": "trailhead", "desc": "Cota 1400 Sinaia"},
    "cota 2000": {"lat": 45.3620, "lon": 25.4950, "elevation": 2000, "type": "cabin", "desc": "Cota 2000 Bucegi"},

    # Piatra Craiului
    "zarnesti": {"lat": 45.5680, "lon": 25.3210, "elevation": 725, "type": "trailhead", "desc": "Zarnesti Town Trailhead"},
    "fantana lui botorog": {"lat": 45.5458, "lon": 25.2958, "elevation": 850, "type": "water", "desc": "Botorog Fountain & Trailhead"},
    "prapastiile zarnestilor": {"lat": 45.5380, "lon": 25.2850, "elevation": 900, "type": "landmark", "desc": "Zarnesti Gorges Canyon"},
    "curmatura": {"lat": 45.5567, "lon": 25.2667, "elevation": 1470, "type": "cabin", "desc": "Curmatura Cabin"},
    "cabana curmatura": {"lat": 45.5567, "lon": 25.2667, "elevation": 1470, "type": "cabin", "desc": "Curmatura Cabin"},
    "saua crapaturii": {"lat": 45.5600, "lon": 25.2600, "elevation": 1660, "type": "pass", "desc": "Crapatura Saddle"},
    "saua padinei inchise": {"lat": 45.5500, "lon": 25.2400, "elevation": 1936, "type": "pass", "desc": "Padina Inchisa Saddle"},
    "varful turnu": {"lat": 45.5639, "lon": 25.2472, "elevation": 1923, "type": "summit", "desc": "Turnu Peak"},
    "varful ascutit": {"lat": 45.5528, "lon": 25.2347, "elevation": 2150, "type": "summit", "desc": "Ascutit Peak & Refuge"},
    "la om": {"lat": 45.5342, "lon": 25.2158, "elevation": 2238, "type": "summit", "desc": "La Om / Piscul Baciului (2238m)"},
    "piscul baciului": {"lat": 45.5342, "lon": 25.2158, "elevation": 2238, "type": "summit", "desc": "Piscul Baciului (La Om) (2238m)"},
    "refugiul grind": {"lat": 45.5300, "lon": 25.2280, "elevation": 1620, "type": "cabin", "desc": "Grind Emergency Refuge"},
    "plaiul foii": {"lat": 45.5611, "lon": 25.1972, "elevation": 849, "type": "trailhead", "desc": "Plaiul Foii Chalet Trailhead"},

    # Retezat Mountains
    "carnic": {"lat": 45.4180, "lon": 22.8800, "elevation": 1005, "type": "trailhead", "desc": "Carnic Parking & Trailhead"},
    "cabana pietrele": {"lat": 45.3956, "lon": 22.8714, "elevation": 1480, "type": "cabin", "desc": "Pietrele Cabin"},
    "cabana gentiana": {"lat": 45.3850, "lon": 22.8750, "elevation": 1670, "type": "cabin", "desc": "Gentiana Cabin"},
    "lacul bucura": {"lat": 45.3586, "lon": 22.8733, "elevation": 2040, "type": "water", "desc": "Bucura Glacial Lake & Salvamont Refuge"},
    "peleaga": {"lat": 45.3644, "lon": 22.8942, "elevation": 2509, "type": "summit", "desc": "Peleaga Peak (2509m)"},
    "varful peleaga": {"lat": 45.3644, "lon": 22.8942, "elevation": 2509, "type": "summit", "desc": "Peleaga Peak (2509m)"},
    "papusa": {"lat": 45.3608, "lon": 22.9094, "elevation": 2508, "type": "summit", "desc": "Papusa Peak (2508m)"},
    "varful papusa": {"lat": 45.3608, "lon": 22.9094, "elevation": 2508, "type": "summit", "desc": "Papusa Peak (2508m)"},
    "varful retezat": {"lat": 45.3800, "lon": 22.8464, "elevation": 2482, "type": "summit", "desc": "Retezat Peak (2482m)"},

    # Ceahlau Massif
    "durau": {"lat": 46.9989, "lon": 25.9236, "elevation": 800, "type": "trailhead", "desc": "Durau Resort Trailhead"},
    "izvorul muntelui": {"lat": 46.9639, "lon": 26.0111, "elevation": 797, "type": "trailhead", "desc": "Izvorul Muntelui Trailhead"},
    "cabana fantanele": {"lat": 46.9850, "lon": 25.9380, "elevation": 1220, "type": "cabin", "desc": "Fantanele Cabin"},
    "cascada duruitoarea": {"lat": 46.9750, "lon": 25.9180, "elevation": 1250, "type": "water", "desc": "Duruitoarea Waterfall"},
    "toaca": {"lat": 46.9608, "lon": 25.9500, "elevation": 1904, "type": "summit", "desc": "Toaca Peak (1904m)"},
    "varful toaca": {"lat": 46.9608, "lon": 25.9500, "elevation": 1904, "type": "summit", "desc": "Toaca Peak (1904m)"},
    "dochia": {"lat": 46.9614, "lon": 25.9542, "elevation": 1750, "type": "cabin", "desc": "Dochia Cabin"},
    "cabana dochia": {"lat": 46.9614, "lon": 25.9542, "elevation": 1750, "type": "cabin", "desc": "Dochia Cabin"},

    # Ciucas Mountains
    "cheia": {"lat": 45.4550, "lon": 25.9860, "elevation": 885, "type": "trailhead", "desc": "Cheia Resort Trailhead"},
    "pasul bratocea": {"lat": 45.4850, "lon": 25.9030, "elevation": 1263, "type": "trailhead", "desc": "Bratocea Pass Trailhead"},
    "cabana muntele rosu": {"lat": 45.5010, "lon": 25.9390, "elevation": 1280, "type": "cabin", "desc": "Muntele Rosu Cabin"},
    "cabana ciucas": {"lat": 45.5140, "lon": 25.9400, "elevation": 1595, "type": "cabin", "desc": "Ciucas Mountain Cabin"},
    "varful ciucas": {"lat": 45.5186, "lon": 25.9269, "elevation": 1954, "type": "summit", "desc": "Ciucas Peak (1954m)"},
    "ciucas": {"lat": 45.5186, "lon": 25.9269, "elevation": 1954, "type": "summit", "desc": "Ciucas Peak (1954m)"},

    # Apuseni / Padis
    "padis": {"lat": 46.5961, "lon": 22.7303, "elevation": 1280, "type": "trailhead", "desc": "Padis Plateau & Cabins"},
    "cetatile ponorului": {"lat": 46.5644, "lon": 22.7028, "elevation": 950, "type": "landmark", "desc": "Ponor Fortress Karstic Chasm"},
    "lumea pierduta": {"lat": 46.5714, "lon": 22.7314, "elevation": 1150, "type": "landmark", "desc": "Lumea Pierduta Karst Plateau"},
    "pestera ghetarul scarisoara": {"lat": 46.4892, "lon": 22.8108, "elevation": 1165, "type": "landmark", "desc": "Scarisoara Underground Glacier"},
}


CARTOGRAPHER_SYSTEM_PROMPT = """
You are the Mountain Cartographer Agent, an expert in Romanian Carpathian geospatial mapping and GIS visualization.
Your sole responsibility is to analyze mountain route recommendations produced by the Alpine Guide Agent and produce a structured, high-precision map specification.

Given the guide's trail recommendation or dossier:
1. Extract the primary trail name and massif.
2. Identify the sequential waypoints in order:
   - Trailhead / Starting point (type: 'trailhead')
   - Intermediate huts / cabins (type: 'cabin')
   - Water springs / lakes / rivers (type: 'water')
   - Mountain passes / saddles / chimneys (type: 'pass')
   - Significant peaks or final destination (type: 'summit')
3. Assign accurate coordinates (lat, lon) and elevation in meters.
4. Calculate the center coordinates and zoom level (typically 12 - 14 for mountain massifs).
5. Output ONLY a valid JSON object matching this schema without any markdown backticks or commentary:

{
  "trail_name": "String",
  "massif": "String",
  "center": {"lat": 45.60, "lon": 24.65},
  "zoom": 13,
  "waypoints": [
    {
      "name": "String",
      "type": "trailhead" | "cabin" | "water" | "pass" | "summit" | "landmark",
      "lat": 45.60,
      "lon": 24.62,
      "elevation": 2034,
      "description": "String"
    }
  ],
  "polyline": [
    [45.60, 24.62],
    [45.60, 24.73]
  ]
}
""".strip()


from app.schema import AgentCard

class CartographerAgent:
    """
    Subordinate specialist agent responsible for cartographic data extraction,
    coordinate resolution, and interactive Leaflet map spec generation.
    """

    def __init__(self, client: Optional[genai.Client] = None, model: str = "gemini-3.5-flash-lite"):
        self.client = client
        self.model = model
        self.agent_card = AgentCard(
            agent_id="cartographer-agent",
            name="RoMountainCartographer",
            version="1.0.0",
            role="GIS & Interactive Route Cartographer",
            description="Extracts spatial waypoints and generates touch-friendly Leaflet/GeoJSON map specifications for Romanian mountain trails.",
            capabilities=[
                "carpathian_coordinate_resolution",
                "waypoint_classification",
                "geojson_polyline_generation",
                "leaflet_spec_generation",
            ],
            inputs={
                "route_text": "Detailed mountain trail itinerary or recommendation dossier from Guide Agent",
                "user_context": "Raw user prompt to extract geographic intent",
            },
            outputs={
                "map_spec": "Structured JSON containing center coordinates, zoom level, waypoints with elevations, and polyline"
            },
        )

    def resolve_landmark_coordinates(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Directly looks up known Romanian mountain coordinates from the local ground-truth database.
        """
        clean_name = name.lower().strip()
        normalized = (
            clean_name.replace("â", "a")
            .replace("ă", "a")
            .replace("î", "i")
            .replace("ș", "s")
            .replace("ț", "t")
        )

        # Exact match
        if normalized in CARPATHIAN_LANDMARKS:
            entry = CARPATHIAN_LANDMARKS[normalized]
            return {"name": name, **entry}

        # Substring search
        for key, entry in CARPATHIAN_LANDMARKS.items():
            if key in normalized or normalized in key:
                return {"name": name, **entry}

        return None

    def _extract_waypoints_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Deterministic fallback extraction: scans dossier text for Romanian mountain landmarks.
        """
        found_waypoints: List[Dict[str, Any]] = []
        seen_keys = set()
        text_lower = text.lower()

        for key, data in CARPATHIAN_LANDMARKS.items():
            # Check for word boundary presence
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, text_lower) and key not in seen_keys:
                seen_keys.add(key)
                found_waypoints.append({
                    "name": data.get("desc", key.title()),
                    "type": data.get("type", "landmark"),
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "elevation": data.get("elevation", 0),
                    "description": data.get("desc", ""),
                })

        return found_waypoints

    def generate_map_spec(
        self,
        route_text: str,
        user_context: str = "",
        history_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Primary A2A interface: takes trail recommendation text from MountainAgent,
        invokes the Cartographer LLM (or fallback), and returns structured map JSON.
        Supports multi-turn context (history_text) when user references past routes.
        """
        combined_text = f"{route_text or ''}\n\n{history_text or ''}".strip()
        if not combined_text or len(combined_text) < 20:
            return None

        # Check if text or history actually references mountain routes or destinations
        has_route_keywords = any(
            k in combined_text.lower()
            for k in [
                "trail dossier", "dosar traseu", "traseu", "trail", "itinerary",
                "varful", "cabana", "peak", "summit", "elevation", "balea", "omu",
                "moldoveanu", "retezat", "bucegi", "fagaras", "piatra craiului", "malaiesti"
            ]
        )
        has_user_intent = any(
            k in user_context.lower()
            for k in ["traseu", "route", "hike", "drumetie", "map", "harta", "acest traseu", "this route"]
        )

        if not has_route_keywords and not has_user_intent:
            return None

        # 1. Attempt LLM Cartographer invocation if client is available
        if self.client:
            try:
                history_prompt = f"\nPreceding Conversation Context:\n{history_text}" if history_text else ""
                prompt = (
                    f"User Query: {user_context}\n\n"
                    f"{history_prompt}\n\n"
                    f"Alpine Guide Recommendation:\n{route_text}\n\n"
                    f"Produce the JSON map spec according to your system prompt instructions."
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=CARTOGRAPHER_SYSTEM_PROMPT,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                raw_json = response.text or ""
                clean_json = re.sub(r"^```json\s*", "", raw_json.strip())
                clean_json = re.sub(r"\s*```$", "", clean_json)

                parsed = json.loads(clean_json)
                if isinstance(parsed, dict) and "waypoints" in parsed and len(parsed["waypoints"]) > 0:
                    if "center" not in parsed or not isinstance(parsed["center"], dict):
                        w0 = parsed["waypoints"][0]
                        parsed["center"] = {"lat": w0["lat"], "lon": w0["lon"]}
                    if "polyline" not in parsed or len(parsed["polyline"]) == 0:
                        parsed["polyline"] = [[w["lat"], w["lon"]] for w in parsed["waypoints"]]
                    return parsed
            except Exception as e:
                logger.warning(f"LLM cartographer step failed or timed out: {e}. Using deterministic GIS fallback.")

        # 2. Resilient Fallback: Build Map Spec from Ground-Truth Database
        waypoints = self._extract_waypoints_from_text(route_text + " " + user_context)
        # If current turn lacks landmarks but history has them (e.g. user said "returneaza mi o harta cu acest traseu")
        if len(waypoints) < 2 and history_text:
            waypoints = self._extract_waypoints_from_text(route_text + " " + user_context + " " + history_text)

        if not waypoints:
            return None

        # Sort waypoints so trailhead comes first and summit comes last
        type_priority = {"trailhead": 0, "water": 1, "cabin": 2, "pass": 3, "landmark": 4, "summit": 5}
        waypoints.sort(key=lambda w: type_priority.get(w.get("type", "landmark"), 3))

        # Calculate geographic center
        avg_lat = sum(w["lat"] for w in waypoints) / len(waypoints)
        avg_lon = sum(w["lon"] for w in waypoints) / len(waypoints)

        polyline = [[w["lat"], w["lon"]] for w in waypoints]

        # Extract title from current text or historical text
        title = "Carpathian Trail Map"
        for line in (route_text + "\n" + (history_text or "")).splitlines():
            line_clean = line.strip()
            if any(k in line_clean.lower() for k in ["trail dossier:", "dosar traseu:", "dossier:", "traseu:"]):
                title = line_clean.split(":", 1)[-1].strip()
                break

        return {
            "trail_name": title,
            "massif": "Romanian Carpathians",
            "center": {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)},
            "zoom": 13,
            "waypoints": waypoints,
            "polyline": polyline,
        }

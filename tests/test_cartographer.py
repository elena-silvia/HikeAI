import pytest
from app.cartographer import CartographerAgent, CARPATHIAN_LANDMARKS
from app.agent import MountainAgent


def test_cartographer_initialization():
    cartographer = CartographerAgent(client=None)
    assert cartographer is not None
    assert len(CARPATHIAN_LANDMARKS) > 30


def test_cartographer_resolve_known_landmarks():
    cartographer = CartographerAgent(client=None)

    # Test exact match
    balea = cartographer.resolve_landmark_coordinates("balea lac")
    assert balea is not None
    assert balea["lat"] == 45.6042
    assert balea["lon"] == 24.6167
    assert balea["elevation"] == 2034
    assert balea["type"] == "trailhead"

    # Test diacritics normalization
    moldoveanu = cartographer.resolve_landmark_coordinates("Vârful Moldoveanu")
    assert moldoveanu is not None
    assert moldoveanu["lat"] == 45.5997
    assert moldoveanu["type"] == "summit"

    # Test unknown destination
    unknown = cartographer.resolve_landmark_coordinates("Unknown Peak Atlantis")
    assert unknown is None


def test_cartographer_extract_waypoints_from_text():
    cartographer = CartographerAgent(client=None)
    sample_text = (
        "Traseu recomandat: Plecare de la Balea Lac, urcare spre Saua Caprei, "
        "trecere pe langa Lacul Capra si ascensiune finala pe Varful Moldoveanu."
    )
    waypoints = cartographer._extract_waypoints_from_text(sample_text)
    assert len(waypoints) >= 3

    names = [w["name"].lower() for w in waypoints]
    assert any("balea" in n for n in names)
    assert any("capra" in n for n in names)
    assert any("moldoveanu" in n for n in names)


def test_cartographer_generate_map_spec_deterministic():
    cartographer = CartographerAgent(client=None)
    dossier = (
        "### Trail Dossier: Fagaras - Moldoveanu Peak via Balea Lac\n"
        "#### 1. Quick Summary\n"
        "- Massif: Fagaras Mountains\n"
        "- Starting Point: Balea Lac\n"
        "- Summit: Varful Moldoveanu\n"
        "#### 2. Itinerary\n"
        "- Stage 1: Balea Lac to Saua Caprei\n"
        "- Stage 2: Saua Caprei to Varful Moldoveanu\n"
    )
    spec = cartographer.generate_map_spec(route_text=dossier, user_context="Moldoveanu hike")
    assert spec is not None
    assert "waypoints" in spec
    assert len(spec["waypoints"]) >= 2
    assert "center" in spec
    assert "lat" in spec["center"]
    assert "lon" in spec["center"]
    assert "polyline" in spec
    assert len(spec["polyline"]) >= 2


def test_cartographer_empty_or_unrelated_text():
    cartographer = CartographerAgent(client=None)
    # Generic greetings should not produce map specs
    spec = cartographer.generate_map_spec("Hello there, how are you?", user_context="hi")
    assert spec is None


def test_agent_to_agent_integration():
    agent = MountainAgent()
    assert hasattr(agent, "cartographer")
    assert isinstance(agent.cartographer, CartographerAgent)

    session_id = "test_a2a_session"
    sample_response = (
        "### Trail Dossier: Bucegi - Omu Peak via Malaiesti\n"
        "#### 1. Quick Summary\n"
        "- Massif: Bucegi Mountains\n"
        "- Starting Point: Gura Diham\n"
        "- Summit: Varful Omu\n"
        "- Cabin: Cabana Malaiesti\n"
    )

    agent.last_responses[session_id] = sample_response
    # Simulate A2A cartographer call
    map_spec = agent.cartographer.generate_map_spec(
        route_text=sample_response,
        user_context="Traseu spre Varful Omu prin Malaiesti",
    )
    agent.last_maps[session_id] = map_spec

    retrieved_map = agent.get_last_map(session_id)
    assert retrieved_map is not None
    assert len(retrieved_map["waypoints"]) >= 2

    # Verify session reset clears map
    agent.reset_session(session_id)
    assert agent.get_last_map(session_id) is None


def test_agent_cards_metadata():
    agent = MountainAgent()
    assert agent.agent_card is not None
    assert agent.agent_card.agent_id == "mountain-guide-agent"
    assert "carpathian_route_recommendation" in agent.agent_card.capabilities

    cartographer = agent.cartographer
    assert cartographer.agent_card is not None
    assert cartographer.agent_card.agent_id == "cartographer-agent"
    assert "leaflet_spec_generation" in cartographer.agent_card.capabilities

    card_dict = cartographer.agent_card.to_dict()
    assert card_dict["name"] == "RoMountainCartographer"
    assert "inputs" in card_dict
    assert "outputs" in card_dict


def test_cartographer_multi_turn_pronoun_context():
    cartographer = CartographerAgent(client=None)

    # Historical turn: Guide recommended Gura Diham - Malaiesti - Omu Peak
    history_dossier = (
        "### Dosar Traseu: Gura Diham către Vârful Omu prin Cabana Mălăiești\n"
        "#### 1. Rezumat Rapid\n"
        "- Punct de plecare: Gura Diham\n"
        "- Vârf: Varful Omu\n"
        "- Cabană: Cabana Malaiesti\n"
    )

    # Current turn: User asks for a map referring to "this route" (no landmark names in prompt!)
    current_user_query = "returneaza mi o harta cu acest traseu"
    current_guide_reply = "Iata harta interactiva pentru traseul solicitat, afisata mai jos."

    spec = cartographer.generate_map_spec(
        route_text=current_guide_reply,
        user_context=current_user_query,
        history_text=history_dossier,
    )

    assert spec is not None
    assert "waypoints" in spec
    assert len(spec["waypoints"]) >= 2

    waypoint_names = [w["name"].lower() for w in spec["waypoints"]]
    assert any("omu" in n or "malaiesti" in n or "diham" in n for n in waypoint_names)
    assert spec["trail_name"] == "Gura Diham către Vârful Omu prin Cabana Mălăiești"

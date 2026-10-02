import pytest
from app.agent import MountainAgent


def test_agent_initialization():
    agent = MountainAgent()
    assert agent is not None
    assert len(agent.tools) == 3
    assert agent.config.model is not None


def test_agent_session_isolation():
    agent = MountainAgent()
    chat_1 = agent._get_or_create_chat("user_1")
    chat_2 = agent._get_or_create_chat("user_2")

    # Ensure different sessions get distinct chat objects
    assert chat_1 is not chat_2
    assert "user_1" in agent.sessions
    assert "user_2" in agent.sessions

    # Test reset session
    agent.reset_session("user_1")
    assert "user_1" not in agent.sessions
    assert "user_2" in agent.sessions


def test_agent_export_last_hike():
    agent = MountainAgent()
    session_id = "test_export_user"
    mock_response = (
        "### Trail Dossier: Bucegi - Omu Peak\n"
        "#### 1. Quick Summary\n"
        "- Massif: Bucegi Mountains\n"
        "- Duration: 5 hours\n"
    )
    agent.last_responses[session_id] = mock_response

    exported = agent.export_last_hike(session_id=session_id, user_name="Elena Test")
    assert exported is not None
    assert exported.exists()
    assert exported.suffix == ".md"

    text = exported.read_text(encoding="utf-8")
    assert "Bucegi - Omu Peak" in text

    # Cleanup
    try:
        exported.unlink()
    except OSError:
        pass


def test_system_prompt_language_and_map_rules():
    from app.prompts import SYSTEM_PROMPT
    assert "CRITICAL LANGUAGE DIRECTIVE" in SYSTEM_PROMPT
    assert "Dosar Traseu:" in SYSTEM_PROMPT
    assert "Rezumat Rapid" in SYSTEM_PROMPT
    assert "Numere de Urgență Salvamont" in SYSTEM_PROMPT
    assert "INTERACTIVE MAP AND A2A CARTOGRAPHER INTEGRATION" in SYSTEM_PROMPT
    assert "NEVER claim:" in SYSTEM_PROMPT


def test_agent_token_tracking():
    agent = MountainAgent()
    session_id = "test_token_user"

    # Default tokens when no turns occurred
    initial_turn = agent.get_last_turn_tokens(session_id)
    assert initial_turn["turn_total"] == 0
    assert initial_turn["session_total"] == 0

    # Simulate token tracking update
    agent.session_tokens[session_id] = {
        "prompt_tokens": 1200,
        "candidates_tokens": 450,
        "total_tokens": 1650,
        "turns_count": 1,
    }
    agent.last_turn_tokens[session_id] = {
        "turn_prompt": 1200,
        "turn_candidates": 450,
        "turn_total": 1650,
        "session_total": 1650,
    }

    turn = agent.get_last_turn_tokens(session_id)
    assert turn["turn_total"] == 1650
    assert turn["session_total"] == 1650

    cumulative = agent.get_session_tokens(session_id)
    assert cumulative["total_tokens"] == 1650
    assert cumulative["turns_count"] == 1

    # Verify session reset clears token memory
    agent.reset_session(session_id)
    assert agent.get_last_turn_tokens(session_id)["turn_total"] == 0
    assert agent.get_session_tokens(session_id)["total_tokens"] == 0

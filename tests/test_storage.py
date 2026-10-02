import os
import shutil
from pathlib import Path
import pytest
from app.storage import (
    save_chat_turn,
    get_user_history,
    export_hike_dossier,
    list_saved_hikes,
    DATA_DIR,
    SAVED_HIKES_DIR,
)


def test_save_and_retrieve_chat_turn():
    test_session = "test_user_123"
    user_msg = "Recommend an easy hiking route in Bucegi Mountains"
    asst_msg = "I recommend the Babele to Caraiman Cross trail (Red Stripe, ~1.5h)."

    save_chat_turn(
        session_id=test_session,
        user_message=user_msg,
        assistant_message=asst_msg,
        user_name="Elena Test",
    )

    history = get_user_history(test_session)
    assert len(history) >= 1
    last_turn = history[-1]
    assert last_turn["user_message"] == user_msg
    assert last_turn["assistant_message"] == asst_msg


def test_multi_user_isolation():
    user_a = "user_alpha"
    user_b = "user_beta"

    save_chat_turn(user_a, "Message A", "Response A", user_name="Alpha")
    save_chat_turn(user_b, "Message B", "Response B", user_name="Beta")

    hist_a = get_user_history(user_a)
    hist_b = get_user_history(user_b)

    assert any(turn["user_message"] == "Message A" for turn in hist_a)
    assert not any(turn["user_message"] == "Message B" for turn in hist_a)
    assert any(turn["user_message"] == "Message B" for turn in hist_b)


def test_export_hike_dossier():
    title = "Moldoveanu Summit Route"
    content = "Stage 1: Stana de Vale -> Moldoveanu Peak. Difficulty: Moderate."

    exported_file = export_hike_dossier(
        title=title,
        content=content,
        massif="Fagaras",
        difficulty="Moderate",
        user_name="Elena",
    )

    assert exported_file.exists()
    assert exported_file.suffix == ".md"

    # Verify content inside markdown file
    file_text = exported_file.read_text(encoding="utf-8")
    assert "Moldoveanu Summit Route" in file_text
    assert "Salvamont" in file_text
    assert "0-SALVAMONT" in file_text
    assert "112" in file_text

    # Verify listed in saved hikes
    saved = list_saved_hikes()
    assert any(h["filename"] == exported_file.name for h in saved)

    # Clean up test file
    try:
        exported_file.unlink()
    except OSError:
        pass


def test_export_hike_dossier_with_romanian_diacritics():
    # Title containing Romanian diacritics: Ș, Ț, ă, î, â
    title = "Dosar Traseu: Șaua Caprei către Vârful Mălăiești"
    content = "Traseu montan de legătură prin Bucegi."

    exported_file = export_hike_dossier(
        title=title,
        content=content,
        user_name="Elena",
    )

    assert exported_file.exists()
    assert exported_file.suffix == ".md"

    # Filename must be strictly ASCII to prevent Latin-1 HTTP header errors
    filename = exported_file.name
    filename.encode("ascii")  # Must not raise UnicodeEncodeError!
    assert "Saua_Caprei_catre_Varful_Malaiesti" in filename

    # File content inside must preserve full Romanian diacritics in UTF-8
    file_text = exported_file.read_text(encoding="utf-8")
    assert "Șaua Caprei" in file_text
    assert "Mălăiești" in file_text

    # Cleanup
    try:
        exported_file.unlink()
    except OSError:
        pass

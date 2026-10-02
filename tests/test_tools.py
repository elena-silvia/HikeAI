import pytest
from app.tools import (
    _find_peak_coordinates,
    get_mountain_weather,
    get_mountain_routes,
    read_safety_guidelines,
    ROMANIAN_PEAKS,
)


def test_find_peak_coordinates():
    # Test known peaks
    omu = _find_peak_coordinates("Vârful Omu")
    assert omu is not None
    assert round(omu[0], 2) == 45.45
    assert round(omu[1], 2) == 25.46

    moldoveanu = _find_peak_coordinates("Moldoveanu")
    assert moldoveanu is not None
    assert round(moldoveanu[0], 2) == 45.60

    # Test with diacritics
    ceahlau = _find_peak_coordinates("Ceahlău")
    assert ceahlau is not None
    assert "Toaca Peak" in ceahlau[2]

    # Test unknown destination returns None
    assert _find_peak_coordinates("Eiffel Tower") is None


def test_get_mountain_weather_live():
    # Live call to Open-Meteo API
    report = get_mountain_weather(destination="Omu")
    assert "Mountain Weather Forecast" in report
    assert "Temperature" in report
    assert "Wind" in report
    assert "Salvamont Safety Alerts" in report


def test_get_mountain_weather_fallback():
    # Call with unrecognized location falls back safely without error
    report = get_mountain_weather(destination="UnknownLocation")
    assert "Mountain Weather Forecast" in report
    assert "Temperature" in report


def test_get_mountain_routes_overpass_live():
    # Live call to Overpass API - verifies User-Agent and query parsing
    result = get_mountain_routes("Moldoveanu")
    assert isinstance(result, str)
    assert len(result) > 0
    # Should not crash with HTTP 406 or unhandled error
    assert "406" not in result
    assert "Error: unable to retrieve data" not in result


def test_read_safety_guidelines():
    content = read_safety_guidelines()
    assert "Salvamont" in content
    assert "112" in content
    assert "0725826668" in content or "0-SALVAMONT" in content

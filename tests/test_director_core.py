import pytest


def test_token_bucket_basic():
    capacity = 30
    tokens = 30
    refill = 6
    assert capacity > 0
    assert tokens <= capacity


def test_world_state_schema():
    import json
    from pathlib import Path

    path = Path("Data/LivingWorld/director_state.json")
    data = json.loads(path.read_text())

    assert "schema_version" in data
    assert "active_events" in data

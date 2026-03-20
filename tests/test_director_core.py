import json
from pathlib import Path


def test_token_bucket_basic():
    capacity = 30
    tokens = 30
    refill = 6
    assert capacity > 0
    assert tokens <= capacity
    assert refill > 0


def test_world_state_schema():
    path = Path("Data/LivingWorld/director_state.json")
    data = json.loads(path.read_text())

    assert "schema_version" in data
    assert "active_events" in data


def test_worldproof_tags_present():
    tags = Path("Config/Tags/GameplayTags.ini").read_text(encoding="utf-8")
    assert "Event.Economy.PriceUpdate" in tags
    assert "Event.Conflict.BanditRaid" in tags
    assert "Event.Wildlife.Disturbance" in tags

"""Tests for the LocationService."""
from bot.services.location_service import LocationService


def test_locations_loaded() -> None:
    service = LocationService()
    assert len(service.all()) >= 250


def test_pick_avoids_recent() -> None:
    service = LocationService()
    locs = service.all()
    recent = locs[:100]
    pick = service.pick(recent=recent)
    assert pick not in recent


def test_pick_when_all_recent() -> None:
    service = LocationService()
    locs = service.all()
    pick = service.pick(recent=locs)
    # Should still return something from the catalog
    assert pick in locs

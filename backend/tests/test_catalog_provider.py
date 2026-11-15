from types import SimpleNamespace

from app.services import catalog_provider
from app.services.sample_catalog import get_catalog


def test_demo_catalog_used_without_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    materials = catalog_provider.get_materials(force_reload=True)
    assert materials == get_catalog()
    assert len(materials) > 0


def test_invalid_database_url_falls_back_to_demo(monkeypatch):
    # A non-postgres URL must not crash the service.
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./app.db")
    materials = catalog_provider.get_materials(force_reload=True)
    assert materials == get_catalog()


def test_catalog_item_is_adapted_to_material():
    item = SimpleNamespace(
        item_id="course-42",
        item_type="course",
        title="Налоги для ИП",
        description="Разбор налоговых режимов.",
        topics=frozenset({"taxes", "accounting"}),
        tags=frozenset({"early"}),
        industries=frozenset({"any"}),
        is_available=True,
        url="/materials/course-42",
    )
    material = catalog_provider._to_material(item)
    assert material.material_id == "course-42"
    assert material.material_type == "course"
    assert material.topic in {"accounting", "taxes"}  # first sorted topic
    assert material.is_available is True
    assert material.is_paid is False  # unknown from the current catalog query

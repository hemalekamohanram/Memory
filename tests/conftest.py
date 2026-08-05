import pytest

from services.api.app.config import get_settings


@pytest.fixture(autouse=True)
def deterministic_settings(monkeypatch):
    """Keep tests offline even when a developer's .env enables live mode."""
    monkeypatch.setenv("ENGRAM_MODE", "mock")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

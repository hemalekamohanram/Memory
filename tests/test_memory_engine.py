from datetime import UTC, datetime, timedelta

from services.api.app.embeddings import DeterministicEmbeddingProvider, cosine_similarity
from services.api.app.memory_service import MemoryExtractionService, MemoryRetrievalService


def test_embeddings_are_deterministic_and_cluster_refresh_language():
    provider = DeterministicEmbeddingProvider(64)
    first = provider.embed("serializable refresh token transaction")
    assert first == provider.embed("serializable refresh token transaction")
    assert cosine_similarity(first, provider.embed("refresh token transaction retry")) > cosine_similarity(
        first, provider.embed("frontend typography spacing"))


def test_extraction_finds_incident_and_successful_fix():
    result = MemoryExtractionService().extract("INC-104", "Incident INC-104. The successful fix was a serializable transaction. Adding retries resolved the issue.")
    assert {item.memory_type for item in result} >= {"incident", "successful_fix"}


def test_recency_decays():
    now = datetime.now(UTC)
    assert MemoryRetrievalService.recency_score(now, now) > MemoryRetrievalService.recency_score(
        now - timedelta(days=500), now)


def test_status_adjustments_prefer_active():
    service = MemoryRetrievalService()
    assert service.status_adjustments["active"] > service.status_adjustments["disputed"]
    assert service.status_adjustments["superseded"] < 0.1
    assert service.status_adjustments["merged"] == 0

import io
import json

import pytest

from services.api.app.bedrock import BedrockAgentProvider, BedrockEmbeddingProvider, BedrockError
from services.api.app.config import get_settings


class FakeBedrock:
    def invoke_model(self, **_kwargs):
        dimension = get_settings().live_embedding_dimension
        return {"body": io.BytesIO(json.dumps({"embedding": [0.1] * dimension}).encode())}

    def converse(self, **kwargs):
        if "toolConfig" in kwargs:
            return {"output": {"message": {"content": [{"toolUse": {"input": {"memories": [{
                "memory_type": "incident",
                "title": "INC-104",
                "content": "Concurrent refreshes caused logouts.",
                "importance": 0.9,
                "confidence": 0.95,
                "evidence_excerpt": "INC-104 evidence",
            }]}}}]}}}
        return {"output": {"message": {"content": [{"text": "Use the known fix [memory-1]."}]}}}


def test_bedrock_embedding_validates_dimension():
    embedding = BedrockEmbeddingProvider(FakeBedrock()).embed("refresh token")
    assert len(embedding) == get_settings().live_embedding_dimension


def test_bedrock_structured_extraction_is_validated():
    candidates = BedrockAgentProvider(FakeBedrock()).extract("INC-104", "incident evidence")
    assert candidates[0].memory_type == "incident"


def test_bedrock_invalid_output_fails_closed():
    class Invalid(FakeBedrock):
        def converse(self, **_kwargs):
            return {"output": {"message": {"content": []}}}

    with pytest.raises(BedrockError):
        BedrockAgentProvider(Invalid()).extract("bad", "bad")

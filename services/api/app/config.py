from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    engram_mode: str = "mock"
    database_url: str = "sqlite+pysqlite:///./engram.db"
    web_origin: str = "http://localhost:3000"
    demo_organization_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    demo_user_id: UUID = UUID("00000000-0000-0000-0000-000000000002")
    embedding_dimension: int = Field(default=64, ge=16, le=4096)
    live_embedding_dimension: int = Field(default=1024, ge=256, le=4096)
    bedrock_region: str = "us-west-2"
    # Use the serverless global inference profile selected in the Bedrock console.
    # It avoids provisioned throughput while keeping the adapter on Bedrock's
    # Converse API.
    bedrock_chat_model_id: str = "global.amazon.nova-2-lite-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    s3_archive_bucket: str | None = None
    local_archive_dir: Path = Path("./local-archive")
    request_timeout_seconds: int = Field(default=30, ge=1, le=120)
    max_event_chars: int = Field(default=50_000, ge=1000)
    demo_api_key: str | None = None

    @property
    def effective_embedding_dimension(self) -> int:
        return self.live_embedding_dimension if self.engram_mode == "live" else self.embedding_dimension


@lru_cache
def get_settings() -> Settings:
    return Settings()

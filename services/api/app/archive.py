import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from .config import get_settings


class ArchiveService(ABC):
    @abstractmethod
    def store(self, project_id: str, event_id: str, payload: bytes) -> dict[str, str]: ...


class LocalArchiveService(ArchiveService):
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or get_settings().local_archive_dir

    def store(self, project_id: str, event_id: str, payload: bytes) -> dict[str, str]:
        target = self.root / project_id / f"{event_id}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return {"object_key": target.as_posix(), "sha256": hashlib.sha256(payload).hexdigest()}


class S3ArchiveService(ArchiveService):
    def __init__(self, bucket: str, client=None) -> None:
        if not bucket:
            raise ValueError("S3 archive bucket is required")
        if client is None:
            import boto3
            client = boto3.client("s3")
        self.bucket = bucket
        self.client = client

    def store(self, project_id: str, event_id: str, payload: bytes) -> dict[str, str]:
        key = f"projects/{project_id}/events/{event_id}.txt"
        digest = hashlib.sha256(payload).hexdigest()
        self.client.put_object(Bucket=self.bucket, Key=key, Body=payload,
                               ServerSideEncryption="AES256", Metadata={"sha256": digest})
        return {"object_key": key, "sha256": digest}


def get_archive_service() -> ArchiveService:
    settings = get_settings()
    if settings.engram_mode == "live":
        return S3ArchiveService(settings.s3_archive_bucket or "")
    return LocalArchiveService()

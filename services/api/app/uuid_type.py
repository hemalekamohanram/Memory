from typing import Any
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class UUIDString(TypeDecorator[str]):
    """String-friendly UUIDs locally; native UUID columns on CockroachDB."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        return dialect.type_descriptor(PostgreSQLUUID(as_uuid=False))

    def process_bind_param(self, value: str | UUID | None, _dialect: Dialect) -> str | None:
        return str(value) if value is not None else None

    def process_result_value(self, value: Any, _dialect: Dialect) -> str | None:
        return str(value) if value is not None else None

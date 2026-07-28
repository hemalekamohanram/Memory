from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine

from .config import get_settings


class VectorJSON(TypeDecorator[list[float]]):
    """SQLite JSON in mock mode; fixed-dimension CockroachDB VECTOR in live mode."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(Vector(get_settings().effective_embedding_dimension))

    def process_bind_param(self, value: list[float] | None, _dialect: Dialect):
        return value

    def process_result_value(self, value: Any, _dialect: Dialect) -> list[float] | None:
        if value is None:
            return None
        return [float(item) for item in value]

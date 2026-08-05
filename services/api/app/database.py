import re
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)


def cockroach_server_version_info(connection: object) -> tuple[int, ...]:
    """Parse CockroachDB's version string for SQLAlchemy's PostgreSQL dialect.

    CockroachDB v26 emits `CockroachDB CCL v26.2.1 ...`, which recent
    SQLAlchemy PostgreSQL dialects do not parse as a PostgreSQL version.
    Cockroach speaks the PostgreSQL wire protocol, so supplying its semantic
    version keeps dialect initialization and Alembic migrations compatible.
    """
    version = connection.exec_driver_sql("SELECT version()").scalar()  # type: ignore[attr-defined]
    match = re.search(r"v(\d+)\.(\d+)(?:\.(\d+))?", str(version))
    if not match:
        raise RuntimeError("Unable to parse CockroachDB server version")
    return tuple(int(part) for part in match.groups(default="0"))


if settings.engram_mode == "live" and not settings.database_url.startswith("sqlite"):
    engine.dialect._get_server_version_info = cockroach_server_version_info  # type: ignore[method-assign]

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session

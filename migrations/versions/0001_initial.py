"""Initial governed memory schema.

Revision ID: 0001
"""
from alembic import op

from services.api.app import models  # noqa: F401
from services.api.app.database import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

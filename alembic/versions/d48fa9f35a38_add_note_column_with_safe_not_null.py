"""Add note column with safe NOT NULL

Revision ID: d48fa9f35a38
Revises: 7939192e6c62
Create Date: 2026-08-30 04:28:16.777961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd48fa9f35a38'
down_revision: Union[str, Sequence[str], None] = '7939192e6c62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('subscriptions', sa.Column('note', sa.String(255), nullable=True))
    op.execute("UPDATE subscriptions SET note = '' WHERE note IS NULL")
    op.alter_column('subscriptions', 'note', nullable=False)

def downgrade() -> None:
    op.drop_column('subscriptions', 'note')

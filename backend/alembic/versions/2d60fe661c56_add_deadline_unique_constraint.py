"""add_deadline_unique_constraint

Revision ID: 2d60fe661c56
Revises: 4b42fea88b8e
Create Date: 2026-06-07 22:28:57.701324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d60fe661c56'
down_revision: Union[str, Sequence[str], None] = '4b42fea88b8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    1. Удаляем существующие дубли (оставляем самые свежие по updated_at).
    2. Добавляем unique constraint на (user_id, lesson_id, event_type, title).
    3. Добавляем индекс для быстрого поиска.
    """
    # Удаляем дубли перед добавлением constraint
    op.execute("""
        DELETE FROM deadline_events
        WHERE id NOT IN (
            SELECT DISTINCT ON (user_id, lesson_id, event_type, title) id
            FROM deadline_events
            ORDER BY user_id, lesson_id, event_type, title, updated_at DESC
        )
    """)

    # Unique constraint
    op.create_unique_constraint(
        'uq_deadline_event_user_lesson_type_title',
        'deadline_events',
        ['user_id', 'lesson_id', 'event_type', 'title']
    )

    # Индекс для быстрого поиска
    op.create_index(
        'ix_deadline_events_user_lesson_type_title',
        'deadline_events',
        ['user_id', 'lesson_id', 'event_type', 'title']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_deadline_events_user_lesson_type_title', table_name='deadline_events')
    op.drop_constraint('uq_deadline_event_user_lesson_type_title', 'deadline_events', type_='unique')

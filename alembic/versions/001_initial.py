"""Initial migration — creates all core tables."""

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, default=""),
        sa.Column("definition", sa.JSON, nullable=False),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("source", sa.String(50), default="local"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "task_instances",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String,
            sa.ForeignKey("workflow_definitions.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("trigger_type", sa.String(20), default="manual"),
        sa.Column("task_input", sa.Text, default=""),
        sa.Column("created_by", sa.String(100), default="api"),
        sa.Column("current_state_snapshot", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "node_executions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column(
            "task_id", sa.String, sa.ForeignKey("task_instances.id"), nullable=False
        ),
        sa.Column("node_id", sa.String, nullable=False),
        sa.Column("node_type", sa.String, nullable=False),
        sa.Column("status", sa.String(20), default="running"),
        sa.Column("input_snapshot", sa.JSON),
        sa.Column("output_snapshot", sa.JSON),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer),
    )
    op.create_table(
        "human_decisions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column(
            "task_id", sa.String, sa.ForeignKey("task_instances.id"), nullable=False
        ),
        sa.Column("node_id", sa.String, nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("feedback", sa.Text, default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", sa.String(100), default="api"),
    )


def downgrade():
    op.drop_table("human_decisions")
    op.drop_table("node_executions")
    op.drop_table("task_instances")
    op.drop_table("workflow_definitions")

"""collectors and incidents

Revision ID: 20260519_0002
Revises: 20260517_0001
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260519_0002"
down_revision = "20260517_0001"
branch_labels = None
depends_on = None


def _json_type():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_host", sa.String(length=255), nullable=True),
        sa.Column("affected_user", sa.String(length=255), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("alert_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_affected_host", "incidents", ["affected_host"])
    op.create_index("ix_incidents_affected_user", "incidents", ["affected_user"])
    op.create_index("ix_incidents_first_seen", "incidents", ["first_seen"])
    op.create_index("ix_incidents_last_seen", "incidents", ["last_seen"])

    op.add_column("alerts", sa.Column("incident_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_alerts_incident_id", "alerts", "incidents", ["incident_id"], ["id"])
    op.create_index("ix_alerts_incident_id", "alerts", ["incident_id"])

    op.create_table(
        "collection_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("interval_label", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_kind", sa.String(length=50), nullable=False, server_default="web-schedule"),
        sa.Column("event_profile", sa.String(length=80), nullable=False, server_default="mixed"),
        sa.Column("batch_size", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_collection_schedules_code", "collection_schedules", ["code"], unique=True)
    op.create_index("ix_collection_schedules_enabled", "collection_schedules", ["enabled"])

    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("collection_schedules.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("events_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alerts_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incidents_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details", _json_type(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_collection_runs_schedule_id", "collection_runs", ["schedule_id"])
    op.create_index("ix_collection_runs_status", "collection_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_collection_runs_status", table_name="collection_runs")
    op.drop_index("ix_collection_runs_schedule_id", table_name="collection_runs")
    op.drop_table("collection_runs")

    op.drop_index("ix_collection_schedules_enabled", table_name="collection_schedules")
    op.drop_index("ix_collection_schedules_code", table_name="collection_schedules")
    op.drop_table("collection_schedules")

    op.drop_index("ix_alerts_incident_id", table_name="alerts")
    op.drop_constraint("fk_alerts_incident_id", "alerts", type_="foreignkey")
    op.drop_column("alerts", "incident_id")

    op.drop_index("ix_incidents_last_seen", table_name="incidents")
    op.drop_index("ix_incidents_first_seen", table_name="incidents")
    op.drop_index("ix_incidents_affected_user", table_name="incidents")
    op.drop_index("ix_incidents_affected_host", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_table("incidents")

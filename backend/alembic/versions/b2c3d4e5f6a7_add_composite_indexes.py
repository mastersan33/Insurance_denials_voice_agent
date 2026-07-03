"""add_composite_indexes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-03 13:00:00.000000

Enterprise-grade composite indexes for:
- Call job queue ordering (status + priority + created_at)
- Billing case search (status + created_at)
- Transcript retrieval (session + sequence)
- Audit log search (action + resource_type + created_at)
- Call session active lookup (status + created_at)
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # call_jobs: queue ordering — most used query pattern
    op.create_index(
        "ix_call_jobs_status_priority_created",
        "call_jobs",
        ["status", "priority", "created_at"],
    )
    # call_jobs: billing case drill-down
    op.create_index(
        "ix_call_jobs_billing_case_status",
        "call_jobs",
        ["billing_case_id", "status"],
    )

    # billing_cases: list by status ordered by created_at (dashboard + list page)
    op.create_index(
        "ix_billing_cases_status_created",
        "billing_cases",
        ["status", "created_at"],
    )
    # billing_cases: payer drill-down for analytics
    op.create_index(
        "ix_billing_cases_payer_status",
        "billing_cases",
        ["payer_name", "status"],
    )

    # call_sessions: active lookup (initiated, ringing, in_progress)
    op.create_index(
        "ix_call_sessions_status_started",
        "call_sessions",
        ["status", "started_at"],
    )

    # transcripts: retrieval by session ordered by sequence (most common query)
    op.create_index(
        "ix_transcripts_session_sequence",
        "transcripts",
        ["call_session_id", "sequence_number"],
    )

    # audit_logs: search by action + resource_type + created_at
    op.create_index(
        "ix_audit_logs_action_resource_created",
        "audit_logs",
        ["action", "resource_type", "created_at"],
    )
    # audit_logs: actor timeline
    op.create_index(
        "ix_audit_logs_actor_created",
        "audit_logs",
        ["actor_id", "created_at"],
    )

    # tickets: open ticket count (dashboard)
    op.create_index(
        "ix_tickets_status_created",
        "tickets",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_call_jobs_status_priority_created", "call_jobs")
    op.drop_index("ix_call_jobs_billing_case_status", "call_jobs")
    op.drop_index("ix_billing_cases_status_created", "billing_cases")
    op.drop_index("ix_billing_cases_payer_status", "billing_cases")
    op.drop_index("ix_call_sessions_status_started", "call_sessions")
    op.drop_index("ix_transcripts_session_sequence", "transcripts")
    op.drop_index("ix_audit_logs_action_resource_created", "audit_logs")
    op.drop_index("ix_audit_logs_actor_created", "audit_logs")
    op.drop_index("ix_tickets_status_created", "tickets")

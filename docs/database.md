# Database Design

## Schema Overview

```
users ──────────────────────────────────────────────
  id (PK, UUID)
  email (UNIQUE INDEX)
  hashed_password
  full_name, role, is_active
  avatar_url, last_login_at
  organization_id (reserved)
  created_at, updated_at

billing_cases ───────────────────────────────────────
  id (PK, UUID)
  patient_name, patient_dob, subscriber_id
  payer_name (INDEX), payer_phone
  claim_number (INDEX), service_date
  cpt_codes, icd10_codes, amount_billed
  denial_code, denial_reason
  provider_name, provider_npi
  status (INDEX) — open|in_progress|appealing|resolved|closed
  priority — urgent|high|normal|low
  notes
  created_at, updated_at

call_jobs ───────────────────────────────────────────
  id (PK, UUID)
  billing_case_id (FK → billing_cases, INDEX)
  created_by (FK → users, INDEX)
  phone_number, status (INDEX)
  priority (INTEGER), max_attempts, attempt_count
  scheduled_at, completed_at
  outcome — resolved|escalated|failed|no_answer|etc
  outcome_notes
  created_at, updated_at

call_sessions ───────────────────────────────────────
  id (PK, UUID)
  call_job_id (FK → call_jobs, INDEX)
  twilio_call_sid (UNIQUE INDEX)
  status — initiated|ringing|in_progress|completed|failed
  direction, from_number, to_number
  started_at, ended_at, duration_seconds
  recording_url
  agent_phase, confidence_score
  outcome, outcome_details, error_message
  created_at, updated_at

transcripts ─────────────────────────────────────────
  id (PK, UUID)
  call_session_id (FK → call_sessions, INDEX)
  speaker — agent|payer|system
  text
  confidence, sequence_number
  timestamp_ms, created_at

call_events ─────────────────────────────────────────
  id (PK, UUID)
  call_session_id (FK → call_sessions, INDEX)
  event_type — phase_change|tool_call|escalation|etc
  data (JSON)
  created_at

conversation_memory ─────────────────────────────────
  id (PK, UUID)
  call_session_id (FK → call_sessions, UNIQUE INDEX)
  key_facts (JSON)
  phase_history (JSON)
  tool_results (JSON)
  created_at, updated_at

human_handoff ───────────────────────────────────────
  id (PK, UUID)
  call_session_id (FK → call_sessions, INDEX)
  reason, context_summary, agent_phase
  confidence_at_handoff
  assigned_to, status — pending|assigned|resolved
  resolution_notes
  created_at, updated_at

tickets ─────────────────────────────────────────────
  id (PK, UUID)
  title, description
  status (INDEX) — open|in_progress|resolved|closed
  priority — urgent|high|medium|low
  category, assigned_to
  resolution
  billing_case_id (FK, nullable)
  call_session_id (FK, nullable)
  created_at, updated_at

audit_logs ──────────────────────────────────────────
  id (PK, UUID)
  actor_id (FK → users, INDEX)
  actor_email (INDEX)
  action (INDEX) — entity.verb format
  resource_type (INDEX), resource_id
  ip_address, user_agent
  status — success|failure
  detail, metadata_ (JSON)
  created_at

refresh_tokens ──────────────────────────────────────
  id (PK, UUID)
  user_id (FK → users, INDEX, CASCADE DELETE)
  token_hash (UNIQUE INDEX)
  expires_at, revoked
  device_hint, ip_address
  created_at, updated_at

password_reset_tokens ───────────────────────────────
  id (PK, UUID)
  user_id (FK → users, INDEX, CASCADE DELETE)
  token_hash (UNIQUE INDEX)
  expires_at, used
  created_at, updated_at
```

---

## Indexes

| Table | Indexed Columns | Purpose |
|-------|----------------|---------|
| `users` | `email` (UNIQUE) | Login lookup |
| `billing_cases` | `status`, `payer_name`, `claim_number` | Filter + search |
| `call_jobs` | `status`, `billing_case_id`, `created_by` | Queue queries |
| `call_sessions` | `call_job_id`, `twilio_call_sid` (UNIQUE) | Join + webhook lookup |
| `transcripts` | `call_session_id` | Transcript fetch by session |
| `call_events` | `call_session_id` | Events by session |
| `tickets` | `status` | Filter by status |
| `human_handoff` | `call_session_id`, `status` | Pending handoff queries |
| `audit_logs` | `actor_id`, `actor_email`, `action`, `resource_type` | Audit search |
| `refresh_tokens` | `token_hash` (UNIQUE), `user_id` | Token validation + revocation |
| `password_reset_tokens` | `token_hash` (UNIQUE), `user_id` | Token lookup |

---

## Migrations

Managed by **Alembic**. Never modify an existing migration.

```bash
# Apply all pending migrations
cd backend && alembic upgrade head

# Check current revision
alembic current

# Create a new migration (auto-detect schema changes)
alembic revision --autogenerate -m "add_xyz_column"

# Rollback one step
alembic downgrade -1
```

**Migration rules:**
1. New columns must be nullable initially (existing rows have no value)
2. Add NOT NULL constraint in a separate subsequent migration after backfill
3. Test `upgrade` AND `downgrade` on staging before production

---

## Connection Pooling

| Parameter | Dev (SQLite) | Prod (PostgreSQL) |
|-----------|-------------|------------------|
| Pool type | StaticPool (n/a) | QueuePool |
| `pool_size` | — | 20 (configurable) |
| `max_overflow` | — | 10 |
| `pool_pre_ping` | disabled | enabled (detects stale connections) |

---

## Performance Queries

Avoid N+1:
- Use `selectinload()` / `joinedload()` for relationships
- Use `.options(selectinload(BillingCase.call_jobs))` not lazy loading in async context

Pagination:
- All list endpoints support `skip`/`limit`
- Default limit: 25–100 per page (capped at 200 for admin queries)

# API Reference

## Authentication

All protected endpoints require a JWT bearer token:
```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`.

---

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local | `http://localhost:8000` |
| Docker | `http://localhost:8000` |
| Production | `https://your-domain.com` |

---

## Auth Endpoints

### POST /api/v1/auth/register

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Secure123!",
  "full_name": "Jane Smith",
  "role": "operator"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "role": "operator",
  "is_active": true,
  "created_at": "2026-07-03T12:00:00Z"
}
```

**Errors:** 400 (email exists), 422 (validation), 429 (rate limited: 5/hr per IP)

---

### POST /api/v1/auth/login

**Request:**
```json
{ "email": "user@example.com", "password": "Secure123!" }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "...", "full_name": "...", "role": "operator" }
}
```
Sets `refresh_token` as an HttpOnly cookie.

**Errors:** 401 (invalid credentials), 429 (rate limited: 10/min per IP)

---

### POST /api/v1/auth/refresh

Refreshes the access token using the HttpOnly cookie.

**Response 200:** Same as login.

**Errors:** 401 (missing/expired/revoked refresh token)

---

### POST /api/v1/auth/logout

Revokes the current refresh token.

**Response 200:** `{ "message": "Logged out successfully" }`

---

### POST /api/v1/auth/logout-all

Revokes all refresh tokens for the current user.

**Response 200:** `{ "message": "Logged out from all devices" }`

---

## Billing Cases

### GET /api/v1/billing-cases

List billing cases with filters and pagination.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search in patient_name, payer_name, claim_number |
| `status` | string | open\|in_progress\|appealing\|resolved\|closed |
| `priority` | string | urgent\|high\|normal\|low |
| `skip` | int | Pagination offset (default: 0) |
| `limit` | int | Page size (default: 25, max: 100) |

**Response 200:**
```json
{
  "items": [ { "id": "uuid", "patient_name": "...", ... } ],
  "total": 142,
  "skip": 0,
  "limit": 25
}
```

---

### POST /api/v1/billing-cases

Create a new billing case.

**Request:** (all fields except `patient_name`, `payer_name`, `claim_number` are optional)
```json
{
  "patient_name": "John Doe",
  "payer_name": "United Healthcare",
  "payer_phone": "+18005551234",
  "claim_number": "CLM-2026-001",
  "denial_code": "CO-97",
  "denial_reason": "Service not covered",
  "amount_billed": 1500.00,
  "provider_name": "City Medical Center",
  "provider_npi": "1234567890",
  "priority": "high"
}
```

---

### PATCH /api/v1/billing-cases/{id}

Update a billing case (partial update, all fields optional).

---

### DELETE /api/v1/billing-cases/{id}

Delete a billing case. **Requires supervisor role.**

---

### POST /api/v1/billing-cases/bulk-import

Import billing cases from CSV file.

**Request:** `multipart/form-data` with `file` field (CSV).

**CSV columns:** `patient_name,payer_name,payer_phone,claim_number,denial_code,denial_reason,amount_billed,provider_name,provider_npi,priority`

---

## Call Jobs

### GET /api/v1/call-jobs

List call jobs with optional status filter.

**Query params:** `status`, `skip`, `limit`

---

### POST /api/v1/call-jobs

Create a new call job.

**Request:**
```json
{
  "billing_case_id": "uuid",
  "phone_number": "+18005551234",
  "priority": 1
}
```

---

### POST /api/v1/call-jobs/{id}/trigger

Immediately trigger a pending or failed job.

---

### POST /api/v1/call-jobs/{id}/cancel

Cancel a pending or scheduled job.

---

### POST /api/v1/call-jobs/queue/pause

Pause all pending jobs in the queue.

---

### POST /api/v1/call-jobs/queue/resume

Resume all paused jobs.

---

### POST /api/v1/call-jobs/queue/cancel-all

Cancel all pending jobs.

---

### POST /api/v1/call-jobs/queue/retry-failed

Re-queue all failed jobs (resets attempt count).

---

## Calls (Sessions)

### GET /api/v1/calls/active

Return all currently active call sessions.

---

### GET /api/v1/calls/{session_id}

Get full details of a call session.

**Response:**
```json
{
  "id": "uuid",
  "call_job_id": "uuid",
  "twilio_call_sid": "CA...",
  "status": "completed",
  "agent_phase": "wrap_up",
  "confidence_score": 0.92,
  "duration_seconds": 312,
  "outcome": "resolved",
  "outcome_details": "...",
  "started_at": "2026-07-03T14:00:00Z",
  "ended_at": "2026-07-03T14:05:12Z"
}
```

---

## Transcripts

### GET /api/v1/transcripts/{session_id}

Get full transcript for a call session.

**Response:** Array of transcript lines with `speaker`, `text`, `confidence`, `sequence_number`.

---

## Analytics

### GET /api/v1/analytics/summary

Overall KPI summary.

**Response:**
```json
{
  "total_calls": 1200,
  "resolution_rate": 68.5,
  "avg_duration_seconds": 287,
  "total_billing_cases": 840
}
```

---

### GET /api/v1/analytics/call-volume

Daily call volume over N days.

**Query:** `days` (default: 30)

---

### GET /api/v1/analytics/outcomes

Outcome breakdown (resolved, escalated, failed, etc.)

---

### GET /api/v1/analytics/payers

Top payers by call volume.

---

### GET /api/v1/analytics/denial-codes

Top denial codes by frequency.

---

## Dashboard

### GET /api/v1/dashboard/stats

Comprehensive dashboard stats snapshot.

Returns: total_calls, active_calls, completed, failed, resolution_rate, avg_duration, queue stats, 7-day call volume chart, outcome breakdown, recent activity.

---

## Tickets

### GET /api/v1/tickets

List tickets. **Query:** `status`, `skip`, `limit`

---

### POST /api/v1/tickets

Create a ticket.

**Request:**
```json
{
  "title": "Unable to reach United Healthcare billing dept",
  "description": "Tried 3 times, IVR loop",
  "priority": "high"
}
```

---

### PATCH /api/v1/tickets/{id}

Update ticket status or resolution.

---

## Human Handoff

### GET /api/v1/human-handoff

List handoff requests. **Query:** `status` (pending|assigned|resolved), `skip`, `limit`

---

### PATCH /api/v1/human-handoff/{id}

Update a handoff (assign, resolve).

**Request:**
```json
{
  "status": "resolved",
  "resolution_notes": "Called back manually, resolved denial",
  "assigned_to": "Jane Smith"
}
```

**Requires operator role.**

---

## Users

### GET /api/v1/users

List all users. **Requires supervisor role.**

---

### PATCH /api/v1/users/{id}

Change user role or active status. **Requires admin role.**

```json
{ "role": "supervisor", "is_active": true }
```

---

### DELETE /api/v1/users/{id}

Deactivate a user. **Requires admin role. Cannot deactivate self.**

---

## Reports

### GET /api/v1/reports/billing-cases

Export all billing cases.

**Query:** `fmt=csv` (default) or `fmt=json`

**Response:** File download (Content-Disposition: attachment)

---

### GET /api/v1/reports/calls

Export call sessions. **Query:** `fmt`

---

### GET /api/v1/reports/transcripts

Export transcripts. **Query:** `fmt`, `session_id` (optional)

---

## Audit Log

### GET /api/v1/audit

**Requires supervisor role.**

**Query:** `actor_id`, `action`, `resource_type`, `skip`, `limit`

---

## Health

### GET /health

`{ "status": "healthy" }` — liveness check

### GET /health/ready

`{ "status": "ready", "checks": { "database": true, "redis": true } }` — readiness check

### GET /health/system

CPU, memory, disk, Redis memory usage.

---

## Error Response Format

All errors return:
```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid authentication |
| 403 | Insufficient role |
| 404 | Resource not found |
| 409 | Conflict (e.g., email already exists) |
| 422 | Unprocessable entity (Pydantic validation) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (database/redis down) |

---

## WebSocket API

### Dashboard WebSocket

```
ws://host/ws/dashboard?token=<jwt_access_token>
```

**Server → Client messages:**
```json
{ "type": "stats", "data": { ...DashboardStats... } }
{ "type": "pong" }
```

**Client → Server:**
```json
{ "type": "ping" }
```

Connection closes with code `4001` on auth failure, `4003` on forbidden.

---

## Rate Limits Summary

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 10/min per IP |
| POST /auth/register | 5/hour per IP |
| All other endpoints | No application-level limit (configure Nginx if needed) |

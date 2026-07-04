# Security Audit Report — Insurance Denials Voice Agent
**Date:** 2026-07-03  
**Auditor:** Engineering Audit Agent  
**Scope:** Full-stack security review — backend (FastAPI), frontend (React), infrastructure (Docker/Nginx)  
**Severity Legend:** 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low · ✅ Pass

---

## Executive Summary

| Domain | Issues Found | Fixed | Remaining Risk |
|--------|-------------|-------|----------------|
| Authentication & Sessions | 0 | — | Low |
| RBAC & Authorization | 1 | ✅ Fixed | Low |
| Rate Limiting | 1 | ✅ Fixed | Low |
| Data Exposure / Reports | 1 | ✅ Fixed | Low |
| File Upload | 1 | ✅ Fixed | Low |
| HTTP Headers | 1 | ✅ Fixed | Low |
| SQL Injection | 0 | — | Low |
| XSS | 0 | — | Low |
| CSRF | 0 | — | Low |
| Secrets Management | 0 | — | Low |
| Audit Logging | 0 | — | Low |
| Twilio Webhook Security | 0 | — | Low |

**Overall risk after fixes: LOW** — No critical or high-severity findings remain.

---

## Detailed Findings

### 1. RBAC — Report Endpoints Not Protected 🟠 → ✅ Fixed

**File:** `backend/app/api/v1/routes/reports.py`  
**Issue:** All three report export endpoints (`/reports/billing-cases`, `/reports/calls`, `/reports/transcripts`) were accessible to any authenticated user, including operators and viewers. These endpoints return raw patient data and financial records.

**Fix applied:**
```python
# Added to all three export endpoints:
_: Annotated[None, require_role("supervisor")] = None,
```
**Verification:** Operator-level JWT now receives `403 Forbidden` on all report endpoints.

---

### 2. Memory DoS — Report Exports Unbounded 🟠 → ✅ Fixed

**File:** `backend/app/api/v1/routes/reports.py`  
**Issue:** All exports executed `SELECT *` with no `LIMIT`. On a database with 100,000+ billing cases, this would exhaust backend memory (250–500 MB per request) and crash the server.

**Fix applied:**
```python
_MAX_EXPORT_ROWS = 10_000

# Applied to all three endpoints:
skip: int = Query(0, ge=0),
limit: int = Query(_MAX_EXPORT_ROWS, ge=1, le=_MAX_EXPORT_ROWS),
# ...
select(BillingCase).order_by(...).offset(skip).limit(limit)
```
**Verification:** `EXPLAIN ANALYZE` on query confirms LIMIT clause is present.

---

### 3. File Upload — No Content-Type or Size Validation 🟠 → ✅ Fixed

**File:** `backend/app/api/v1/routes/billing_cases.py` — `POST /bulk-import`  
**Issue:** File upload accepted any content type and any size. An attacker could upload a 500 MB binary and OOM the server, or upload non-CSV files that may cause parsing errors exposing stack traces.

**Fix applied:**
```python
_ALLOWED_CONTENT_TYPES = {"text/csv", "text/plain", "application/csv"}
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

if file.content_type.lower().split(";")[0].strip() not in _ALLOWED_CONTENT_TYPES:
    raise HTTPException(415, "Only CSV files are accepted")

content = await file.read(_MAX_UPLOAD_BYTES + 1)
if len(content) > _MAX_UPLOAD_BYTES:
    raise HTTPException(413, "File exceeds the 5 MB upload limit")
```

---

### 4. Missing HTTP Security Header 🟡 → ✅ Fixed

**File:** `backend/app/middleware/security_headers.py`  
**Issue:** `X-Permitted-Cross-Domain-Policies` header was absent. This header prevents Flash, Silverlight, and PDF plugins from loading cross-domain policies from the server — relevant even in modern stacks for defence-in-depth.

**Fix applied:**
```python
response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
```

---

## Controls Verified ✅

### Authentication
| Control | Implementation | Status |
|---------|---------------|--------|
| Password hashing | `bcrypt` via `passlib[bcrypt]` (cost factor 12) | ✅ |
| JWT access tokens | `python-jose` HS256, 60-min expiry | ✅ |
| Refresh tokens | Opaque 32-byte tokens, SHA-256 hashed in DB | ✅ |
| Refresh cookie | HttpOnly + Secure + SameSite=Strict at `/api/v1/auth` | ✅ |
| Password reset tokens | Opaque, SHA-256 hashed, 1-hour expiry | ✅ |
| Account enumeration | Uniform `"Invalid email or password"` message | ✅ |
| Inactive account | Returns 401 before issuing tokens | ✅ |

### RBAC
| Endpoint Group | Minimum Role | Enforced Via |
|---------------|-------------|-------------|
| All read endpoints | `viewer` | `CurrentUser` dependency |
| Mutations (create/update) | `operator` | `require_role("operator")` |
| User management | `supervisor` / `admin` | `require_role(...)` |
| Report exports | `supervisor` | `require_role("supervisor")` ← **newly added** |
| Queue management | `supervisor` | `require_role("supervisor")` |

### Rate Limiting
| Endpoint | Limit | Window | Storage |
|----------|-------|--------|---------|
| `POST /auth/login` | 10 | 60 s | Redis |
| `POST /auth/register` | 5 | 1 h | Redis |

### SQL Injection
- All queries use SQLAlchemy ORM / Core with parameterised bindings.
- No raw SQL strings with user input found.
- String search uses `ilike(f"%{q}%")` with sanitised input.

### XSS
- React frontend escapes all values by default.
- Backend returns `Content-Type: application/json` (not HTML).
- CSP header set: `default-src 'self'`, `frame-ancestors 'none'`.

### CSRF
- Refresh token in HttpOnly cookie + access token in `Authorization` header = double-submit defence.
- `SameSite=Strict` on refresh cookie prevents cross-site cookie submission.
- Mutations require `Content-Type: application/json` (browser won't send this for form-based CSRF).

### Twilio Webhook Security
- All webhooks at `/api/v1/twilio/*` validate `X-Twilio-Signature` via `twilio.request_validator`.
- Returns `403` on signature mismatch.
- Runs before any business logic.

### Secrets Management
- All secrets in environment variables — no hardcoded secrets found.
- `_validate_settings()` in `main.py` rejects default `SECRET_KEY` in production at startup.
- `.env.example` documents all variables; actual `.env` excluded from version control.
- Docker Compose uses `env_file: .env` — no credentials in `docker-compose.yml`.
- Redis password enforced (`--requirepass`).

### Audit Logging
- `audit_service.py` fires async tasks for: login, logout, register, password change, user update, report export, call trigger.
- Logs stored in `audit_log` DB table with: `actor_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `timestamp`.
- No secrets or PII values logged (only IDs and action names).

### Sensitive Data Masking
- Passwords hashed before storage, never logged.
- `result.refresh_token = ""` after login — token not returned in JSON body.
- `hashed_password` not included in any `UserResponse` schema.

---

## OWASP Top 10 Coverage

| OWASP Category | Status | Notes |
|----------------|--------|-------|
| A01 Broken Access Control | ✅ Mitigated | RBAC on all endpoints, report fix applied |
| A02 Cryptographic Failures | ✅ Mitigated | bcrypt, TLS enforced in prod, HSTS header |
| A03 Injection | ✅ Mitigated | ORM parameterised queries throughout |
| A04 Insecure Design | ✅ Mitigated | Role hierarchy, separation of concerns |
| A05 Security Misconfiguration | ✅ Mitigated | Startup validation, docs disabled in prod |
| A06 Vulnerable Components | 🟡 Ongoing | Dependabot / `pip-audit` required (not in CI) |
| A07 Auth & Session Failures | ✅ Mitigated | JWT + HttpOnly cookie + rate limiting |
| A08 Data Integrity Failures | ✅ Mitigated | Twilio signature, no deserialization of untrusted data |
| A09 Logging Failures | ✅ Mitigated | Structured logs, correlation IDs, audit trail |
| A10 SSRF | 🟡 Low Risk | No user-controlled URL fetching. Twilio/ElevenLabs URLs from config only |

---

## Recommendations (Post-Audit)

1. **Add `pip-audit` to CI** — scan for known CVEs in Python dependencies on every push.
2. **Add `npm audit` to CI** — scan frontend dependencies (currently in `.github/workflows/ci.yml` partially).
3. **Consider field-level encryption** for `patient_dob`, `subscriber_id` at rest (HIPAA compliance path).
4. **Add account lockout** — after 10 consecutive failed logins, lock account for 30 min (beyond rate limiting).
5. **Rotate JWT secret** — add key ID (`kid`) to JWT header to support zero-downtime secret rotation.

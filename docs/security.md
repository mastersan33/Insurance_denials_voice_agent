# Security Architecture

## Authentication

### Access Tokens (JWT)
- Algorithm: HS256
- Expiry: 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Stored: `localStorage` (frontend)
- Payload: `{ sub: user_id, type: "access", exp: timestamp }`
- The `type` claim prevents refresh tokens from being used as access tokens

### Refresh Tokens (Opaque)
- 64-byte cryptographically random token (`secrets.token_urlsafe(64)`)
- Stored: **SHA-256 hashed** in `refresh_tokens` table — raw token never persisted
- Transport: **HttpOnly, Secure, SameSite=Strict cookie** — JS cannot read it
- Expiry: 30 days, rotated on every use
- Revocation: `POST /auth/logout` and `POST /auth/logout-all`

### Password Storage
- bcrypt via `passlib[bcrypt]` — timing-safe comparison

### Password Reset
- 48-byte random token, SHA-256 hashed, single-use, expires 60 minutes

---

## Authorisation (RBAC)

```
admin (3) > supervisor (2) > operator (1) > viewer (0)
```

Enforced via `require_role("min_role")` FastAPI dependency on every protected endpoint.

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 10 requests | 60 seconds / IP |
| `POST /auth/register` | 5 requests | 3600 seconds / IP |

Redis-based. Fails open (if Redis is down, requests proceed).

---

## Twilio Webhook Security

- HMAC-SHA1 signature validation via `validate_twilio_signature` dependency
- Reconstructs signed URL (respects reverse proxy headers)
- HTTP 403 on invalid signature
- Bypassed only when `TWILIO_AUTH_TOKEN` is empty (local dev)

---

## HTTP Security Headers

| Header | Value |
|--------|-------|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | camera=(), microphone=(), geolocation=(), payment=() |
| Content-Security-Policy | default-src 'self'; ... |
| Strict-Transport-Security | max-age=31536000; includeSubDomains (prod only) |
| Cache-Control on /api/ | no-store, no-cache, must-revalidate |

---

## SQL Injection Prevention

SQLAlchemy ORM / Core parameterised queries only. No raw SQL string concatenation.

---

## OWASP Top 10 Coverage

| Risk | Mitigation |
|------|-----------|
| A01 Broken Access Control | RBAC via require_role |
| A02 Cryptographic Failures | bcrypt, SHA-256 hashing, HTTPS/HSTS |
| A03 Injection | Parameterised queries, Pydantic validation |
| A04 Insecure Design | Stateless JWT, token rotation |
| A05 Security Misconfiguration | Startup validation rejects default secrets in prod |
| A06 Vulnerable Components | Pinned requirements.txt |
| A07 Auth Failures | Rate limiting, bcrypt timing-safe |
| A09 Logging Failures | Structured JSON logs, audit trail, request IDs |

---

## Production Security Checklist

- [ ] `SECRET_KEY` set to 64-byte random value
- [ ] `POSTGRES_PASSWORD` strong unique value
- [ ] `REDIS_PASSWORD` set (Redis auth enabled)
- [ ] `TWILIO_AUTH_TOKEN` configured
- [ ] `ENVIRONMENT=production` (enables HSTS, disables /docs)
- [ ] CORS origins locked to production domain
- [ ] All API keys rotated from dev
- [ ] TLS certificate on load balancer
- [ ] Database not exposed on public network
- [ ] Redis not exposed on public network

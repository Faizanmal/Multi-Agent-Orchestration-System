# Authentication Architecture

## Overview

This document describes authentication and authorization system
added to the Multi-Agent AI platform. It follows OWASP ASVS Level 2, NIST
SP 800-63B, OAuth 2.1, and OpenID Connect 1.0 best practices.

---

## Supported Authentication Methods

| Method | Provider | Endpoint |
|--------|----------|----------|
| Email / Password | Django (custom) | `POST /api/auth/v2/login/` |
| Google | OpenID Connect | `POST /api/auth/google/` → callback |
| GitHub | OAuth 2.0 | `POST /api/auth/github/` → callback |
| Firebase | Firebase Admin SDK | `POST /api/auth/firebase/` |

---

## Token Architecture

### Access Token (JWT)
- Algorithm: HS256
- Lifetime: **15 minutes**
- Claims: `sub`, `email`, `role`, `sessionId`, `provider`, `jti`, `iss`, `aud`, `iat`, `exp`, `type`
- Signed with `JWT_SECRET` env var

### Refresh Token (Opaque)
- 64-byte URL-safe random string
- SHA-256 hashed before storage in `RefreshToken` table
- Lifetime: **30 days**
- Rotation: new pair issued on every `/api/auth/refresh/` call
- Theft detection: entire token family revoked on reuse of revoked token

### Refresh Token Family
Each login creates a new "family" (UUID). All rotated tokens in a session share
the same family. If a revoked token is presented again, the entire family is
invalidated — preventing token theft.

---

## Database Models

| Model | Purpose |
|-------|---------|
| `CustomUser` | Core user (email login, roles) |
| `AuthProvider` | Linked OAuth providers per user |
| `OAuthState` | Short-lived CSRF state tokens for OAuth |
| `RefreshToken` | Hashed refresh tokens with rotation metadata |
| `AuditLog` | Immutable audit trail |
| `BruteForceRecord` | Failure tracking for lockout |
| `UserSession` | Legacy session model (preserved) |

---

## Security Layers

### 1. CSRF Protection (OAuth)
- Every OAuth flow generates a cryptographically random `state` parameter
- State is persisted in `OAuthState` model with 10-minute TTL
- Callback validates state before proceeding
- State is marked `used=True` immediately after validation

### 2. Brute Force Protection
Implemented in `authentication/brute_force.py`:

| Endpoint | Max Attempts | Lockout Duration |
|----------|-------------|-----------------|
| `login` | 5 | 15 minutes |
| `password_reset` | 3 | 60 minutes |
| `google_callback` | 10 | 30 minutes |
| `github_callback` | 10 | 30 minutes |
| `token_refresh` | 20 | 10 minutes |

### 3. Rate Limiting
Two layers:
- **DRF throttling**: `AnonRateThrottle` + `UserRateThrottle`
- **Middleware**: `RateLimitMiddleware` in `security_middleware.py`

### 4. Security Headers
Applied by `SecurityHeadersMiddleware`:
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Referrer-Policy`
- `Permissions-Policy`

### 5. Input Sanitization
- All auth inputs are `.strip()`-ed and length-checked
- Email is normalized to lowercase
- Password length enforced server-side (≥ 8 chars)

---

## RBAC (Role-Based Access Control)

| Role | Level | Key Permissions |
|------|-------|-----------------|
| `viewer` | 1 | view_agent, view_session, view_message |
| `user` | 2 | + create_session, send_message |
| `developer` | 3 | + create_agent, execute_workflow |
| `analyst` | 3 | + export_data, create_report |
| `admin` | 4 | + manage_users, manage_settings |
| `super_admin` | 5 | All permissions |

Permissions are cached for 5 minutes per user (invalidated on role change).

---

## Audit Logging

All authentication events are written to `AuditLog` (immutable).

**Events logged:**
- login, logout, login_failed
- register
- oauth_login, oauth_login_failed
- provider_linked, provider_unlinked
- token_refresh
- logout_all, session_revoked
- password_reset, password_change
- account_deleted
- admin_action

**Never logged:** passwords, tokens, secrets, Firebase ID tokens, OAuth access tokens.

---

## OAuth Flows

### Google OAuth
1. Frontend: `POST /api/auth/google/` → receives `authorization_url`
2. Frontend: redirect browser to `authorization_url`
3. User authenticates with Google
4. Google: redirect to `GET /api/auth/google/callback/?code=...&state=...`
5. Backend: validate state, exchange code, verify ID token via `google-auth`
6. Backend: resolve user (create/link), issue JWT pair
7. Backend: return `{ access_token, refresh_token, user }`
8. Frontend callback page: stores tokens, redirects to `/dashboard`

### GitHub OAuth
Same 8-step flow using GitHub's Authorization Code grant. Verified email
is fetched from `/user/emails` API. Users without public email are handled
gracefully.

### Firebase
1. Client: signs in with Firebase SDK, gets `idToken`
2. Frontend: `POST /api/auth/firebase/` with `{ id_token }`
3. Backend: verifies token with Firebase Admin SDK (`check_revoked=True`)
4. Backend: resolves/creates user, issues JWT pair

---

## Account Linking

A single user account can be linked to multiple providers:
- Email/Password
- Google (via `AuthProvider` record)
- GitHub (via `AuthProvider` record)
- Firebase (via `AuthProvider` record)

**Linking**: Initiating an OAuth flow while authenticated links that provider
to the existing account. If the OAuth email matches an existing account,
the provider is linked rather than creating a duplicate.

**Unlinking**: `DELETE /api/auth/unlink/{provider}/`. Blocked if the provider
is the user's only login method and no password is set.

---

## Session Management

Sessions are tracked via `RefreshToken` records:
- Each login creates a new refresh token with device/IP metadata
- `/api/sessions/list/` returns all active sessions
- `/api/sessions/{id}/revoke/` revokes a specific session
- `POST /api/auth/logout-all/` revokes every session

---

## API Endpoint Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/v2/register/` | Public | Register with email/password |
| POST | `/api/auth/v2/login/` | Public | Login with email/password |
| POST | `/api/auth/refresh/` | Public | Rotate refresh token |
| POST | `/api/auth/logout-current/` | Bearer | Logout current device |
| POST | `/api/auth/logout-all/` | Bearer | Logout all devices |
| POST | `/api/auth/firebase/` | Public | Firebase token exchange |
| POST | `/api/auth/google/` | Public | Start Google OAuth |
| GET | `/api/auth/google/callback/` | Public | Google OAuth callback |
| POST | `/api/auth/github/` | Public | Start GitHub OAuth |
| GET | `/api/auth/github/callback/` | Public | GitHub OAuth callback |
| POST | `/api/auth/link/google/` | Bearer | Link Google account |
| POST | `/api/auth/link/github/` | Bearer | Link GitHub account |
| DELETE | `/api/auth/unlink/google/` | Bearer | Unlink Google |
| DELETE | `/api/auth/unlink/github/` | Bearer | Unlink GitHub |
| GET | `/api/auth/me/` | Bearer | Get current user profile |
| PATCH | `/api/auth/profile/update/` | Bearer | Update profile |
| DELETE | `/api/auth/account/` | Bearer | Delete account |
| GET | `/api/sessions/list/` | Bearer | List active sessions |
| DELETE | `/api/sessions/{id}/revoke/` | Bearer | Revoke session |
| GET | `/api/auth/audit-log/` | Bearer | View audit log |

---

## Threat Model Summary

| Threat | Mitigation |
|--------|-----------|
| Brute force login | IP + email lockout, progressive delays |
| Token theft | Refresh token families, theft detection |
| CSRF (OAuth) | State parameter validated server-side |
| Session hijacking | Short-lived JWTs, refresh token rotation |
| SQL injection | Django ORM (parameterized queries) |
| XSS | CSP headers, input sanitization |
| Clickjacking | X-Frame-Options: DENY |
| Credential exposure | No plaintext passwords; hashed refresh tokens |
| Open redirect | OAuth callbacks validated against stored state |
| Account enumeration | Login always returns "Invalid credentials" |
| Mass assignment | Only allowlisted fields updated in profile |
| Privilege escalation | RBAC enforced at view layer with role hierarchy |

---

## Files Created / Modified

```
backend/authentication/
├── models.py                      ← Added 5 new models
├── jwt_auth.py                    ← Replaced with service-backed implementation
├── brute_force.py                 ← NEW: Brute force protection
├── advanced_views.py            ← NEW: All API endpoints
├── urls.py                        ← Extended with all new routes
├── services/
│   ├── __init__.py
│   ├── jwt_service.py             ← NEW: Consolidated JWT + refresh logic
│   ├── firebase_service.py        ← NEW: Firebase Admin SDK
│   ├── google_oauth_service.py    ← NEW: Google OAuth/OIDC
│   ├── github_oauth_service.py    ← NEW: GitHub OAuth
│   ├── session_service.py         ← NEW: Device parsing + session queries
│   ├── audit_service.py           ← NEW: Audit log writer
│   └── account_linking_service.py ← NEW: Link/unlink providers
├── tests/
│   ├── test_jwt_service.py        ← NEW: 16 JWT unit tests
│   ├── test_advanced_views.py   ← NEW: 26 integration tests
│   ├── test_rbac.py               ← NEW: 10 RBAC tests
│   ├── test_brute_force.py        ← NEW: 5 brute force tests
│   └── test_account_linking.py    ← NEW: 7 linking tests
└── migrations/
    └── 0003_advanced_auth.py    ← NEW: DB migration

backend/backend/settings.py        ← Added Firebase/Google/GitHub/JWT config
backend/requirements.txt           ← Added 7 new packages

frontend/src/
├── app/layout.tsx                 ← Added AuthProvider
├── contexts/AuthContext.tsx       ← Full OAuth + session methods
├── app/(auth)/login/page.tsx      ← Real auth wired up
├── app/(auth)/google/callback/page.tsx  ← NEW
└── app/(auth)/github/callback/page.tsx  ← NEW

.env.auth.example                  ← NEW: Auth env var documentation
```

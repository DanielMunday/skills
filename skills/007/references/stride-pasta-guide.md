# STRIDE & PASTA Threat Modeling Guide

> Practical guide for threat modeling systems, APIs, and AI agents.
> Use this when performing `007 threat-model` or any security analysis that requires structured threat identification.

---

## When to Use What

| Method | Best For | Effort | Output |
|--------|----------|--------|--------|
| **STRIDE** | Component-level analysis, quick threat identification | Low-Medium | List of threats per component |
| **PASTA** | Full system risk analysis, business-aligned | Medium-High | Prioritized attack scenarios |
| **Both** | Critical systems, compliance requirements | High | Complete threat landscape |

**Rule of thumb:**
- Quick code review or PR? → STRIDE on changed components
- New system design or architecture review? → PASTA full process
- Production system with sensitive data? → Both

---

## STRIDE Walkthrough

### S - Spoofing (Identity)

**Question:** Can someone pretend to be another user, service, or component?

```python
# API without authentication
GET /api/users/123/data  # Anyone can access any user's data

# Forged JWT with weak secret
jwt.encode({"user_id": "admin", "role": "superuser"}, "password123")
```

**Mitigations:** Strong authentication (OAuth 2.0, mTLS), HMAC signature validation, API key rotation.

---

### T - Tampering (Data Integrity)

**Question:** Can someone modify data in transit, at rest, or in processing?

```python
# SQL injection modifying data
POST /api/transfer {"amount": "100; UPDATE accounts SET balance=999999 WHERE id=1"}
```

**Mitigations:** Input validation/sanitization, HTTPS everywhere, signed artifacts, database constraints.

---

### R - Repudiation (Accountability)

**Question:** Can someone perform an action and deny it later?

```python
# No audit logging on financial transactions
def transfer_money(from_acc, to_acc, amount):
    db.execute("UPDATE accounts ...")  # No log of who did this, when, or why
```

**Mitigations:** Immutable audit logs (append-only), centralized logging (SIEM), signed log entries.

---

### I - Information Disclosure

**Question:** Can someone access data they shouldn't see?

```python
# Stack trace in production API response
{
  "error": "NullPointerException at com.app.UserService.getUser(UserService.java:42)",
  "database": "postgresql://admin:s3cret@db.internal:5432/users"
}
```

**Mitigations:** Generic error messages, secrets in vault, access control on all endpoints, disable debug in production.

---

### D - Denial of Service

**Question:** Can someone make the system unavailable?

```python
# Unbounded query with no pagination
GET /api/users  # Returns 10 million records, crashes server

# ReDoS
import re
re.match(r"(a+)+$", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!")
```

**Mitigations:** Rate limiting, pagination, query limits, circuit breakers, resource quotas.

---

### E - Elevation of Privilege

**Question:** Can someone gain permissions they shouldn't have?

```python
# IDOR
GET /api/users/123/admin-panel  # Only checks if user is logged in, not if they're admin

# Role manipulation via mass assignment
POST /api/register {"name": "John", "email": "john@test.com", "role": "admin"}
```

**Mitigations:** RBAC, allowlist for assignable fields, input path validation, principle of least privilege.

---

## PASTA 7-Stage Walkthrough

### Stage 1: Define Objectives

```
Business objective: "Process payments securely"
Security objective: "Prevent unauthorized transactions and data exposure"
Compliance: PCI-DSS, LGPD
Risk appetite: LOW (financial data)
```

### Stage 2: Define Technical Scope

```
Components:
- Frontend: React SPA (app.example.com)
- API Gateway: Kong (api.example.com)
- Backend: FastAPI (internal)
- Database: PostgreSQL (internal)
- External: Stripe API, SendGrid
```

### Stage 3: Application Decomposition

```
Trust boundaries:
  [Internet] --HTTPS--> [WAF/CDN] --HTTPS--> [API Gateway]
  [API Gateway] --mTLS--> [Backend Services]
  [Backend] --TLS--> [Database]
```

### Stage 4-7: Threat Analysis → Vulnerability Analysis → Attack Modeling → Risk Analysis

Apply STRIDE to each data flow crossing a trust boundary, then build attack trees, score by business impact.

---

## Building Attack Trees

```
GOAL: Steal user payment data
├── OR: Compromise database directly
│   ├── AND: Find SQL injection point
│   └── AND: Access database credentials
├── OR: Intercept data in transit
│   ├── Downgrade HTTPS to HTTP
│   └── Compromise TLS certificate
├── OR: Exploit API vulnerability
│   └── AND: BOLA on payment endpoint
└── OR: Social engineering
    ├── Phish admin credentials
    └── Compromise developer laptop
```

---

## Threat Documentation Template

```markdown
### THREAT-{ID}: {Short Title}

**Category:** STRIDE category (S/T/R/I/D/E)
**Component:** Affected system component
**Attack Vector:** How the attacker exploits this
**Prerequisites:** What the attacker needs

**Impact:**
- Confidentiality: HIGH/MEDIUM/LOW
- Integrity: HIGH/MEDIUM/LOW
- Availability: HIGH/MEDIUM/LOW

**Probability:** HIGH/MEDIUM/LOW
**Severity:** CRITICAL/HIGH/MEDIUM/LOW

**Mitigation:**
- [ ] Short-term fix
- [ ] Long-term fix
- [ ] Monitoring/alerting to add

**Status:** OPEN | MITIGATED | ACCEPTED | TRANSFERRED
```

---

## Example: Threat Modeling a Webhook Endpoint

| Category | Threat | Severity | Mitigation |
|----------|--------|----------|------------|
| **Spoofing** | Attacker sends fake events | CRITICAL | Verify HMAC signature |
| **Tampering** | Payload modified in transit | HIGH | HTTPS + signature verification |
| **Repudiation** | Cannot prove event was processed | MEDIUM | Log all webhook events with idempotency key |
| **Info Disclosure** | Error responses leak internal state | MEDIUM | Return generic 200/400 |
| **DoS** | Flood endpoint with fake events | HIGH | Rate limit by IP, verify signature before processing |
| **EoP** | Webhook triggers admin-level operations | HIGH | Webhook handler runs with minimal permissions |

---

## Example: Threat Modeling an AI Agent with Tool Access

| Category | Threat | Severity | Mitigation |
|----------|--------|----------|------------|
| **Spoofing** | Prompt injection makes agent impersonate admin | CRITICAL | Input sanitization, system prompt hardening |
| **Tampering** | Agent modifies files/DB beyond intended scope | CRITICAL | Read-only by default, allowlist of writable paths |
| **Repudiation** | Cannot trace which agent action caused damage | HIGH | Log every tool call with full context |
| **Info Disclosure** | Agent leaks secrets from context/env to output | CRITICAL | Strip secrets before context injection, output filtering |
| **DoS** | Agent enters infinite loop, burns API credits | HIGH | Iteration limits, token budgets, timeout per operation |
| **EoP** | Agent escapes sandbox via tool chaining | CRITICAL | Least-privilege tool access, no shell access |

---

## Quick Reference: Severity Matrix

| | Low Impact | Medium Impact | High Impact |
|---|---|---|---|
| **High Probability** | MEDIUM | HIGH | CRITICAL |
| **Medium Probability** | LOW | MEDIUM | HIGH |
| **Low Probability** | LOW | LOW | MEDIUM |

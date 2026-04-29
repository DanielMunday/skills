# API Security Patterns & Anti-Patterns

> Reference for securing REST APIs, webhooks, and service-to-service communication.
> Use during `007 audit`, `007 threat-model`, and code reviews of API code.

---

## 1. Authentication Patterns

### API Keys

```yaml
# GOOD: API key in header
Authorization: ApiKey sk-live-abc123def456

# BAD: API key in URL (logged in server logs, browser history, referrer headers)
GET /api/data?api_key=sk-live-abc123def456

api_keys:
  - Prefix keys for identification: sk-live-, sk-test-, pk-
  - Store hashed (SHA-256), not plaintext
  - Rotate regularly (90 days max)
  - Scope to specific permissions/resources
  - Rate limit per key
  - Revoke immediately on compromise
  - Different keys per environment (dev/staging/prod)
```

### OAuth 2.0

```yaml
oauth2_flows:
  server_to_server: client_credentials
  web_app_with_backend: authorization_code + PKCE
  single_page_app: authorization_code + PKCE (no client secret)
  mobile_app: authorization_code + PKCE
  NEVER_USE: implicit_grant

tokens:
  access_token_lifetime: 15_minutes
  refresh_token_lifetime: 7_days
  refresh_token_rotation: true
  store_tokens: httponly_secure_cookie
  revocation: implement_revocation_endpoint
```

### JWT Best Practices

```python
jwt_config = {
    "algorithm": "RS256",
    "expiration": 900,
    "issuer": "auth.example.com",
    "audience": "api.example.com",
    "required_claims": ["sub", "exp", "iat", "iss", "aud"],
}

jwt_antipatterns = [
    "algorithm: none",
    "algorithm: HS256",  # with weak/shared secret
    "exp: far_future",
    "no audience check",
    "secret in code",
    "JWT in URL parameter",
]

def validate_jwt(token: str) -> dict:
    return jwt.decode(
        token,
        key=PUBLIC_KEY,
        algorithms=["RS256"],
        audience="api.example.com",
        issuer="auth.example.com",
        options={"require": ["exp", "iat", "sub"]},
    )
```

---

## 2. Rate Limiting Strategies

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

```yaml
rate_limits:
  unauthenticated:
    requests_per_minute: 20
    requests_per_hour: 100

  authenticated_free:
    requests_per_minute: 60
    requests_per_hour: 1000

  authenticated_paid:
    requests_per_minute: 300
    requests_per_hour: 10000

  headers:
    X-RateLimit-Limit: "60"
    X-RateLimit-Remaining: "45"
    X-RateLimit-Reset: "1620000060"
    Retry-After: "30"
```

---

## 3. Input Validation

```python
from pydantic import BaseModel, Field, validator

class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    age: int = Field(ge=13, le=150)
    role: str = Field(default="user")

    @validator("role")
    def restrict_role(cls, v):
        if v not in ("user", "viewer"):
            return "user"
        return v

    class Config:
        extra = "forbid"
```

---

## 4. Webhook Security

```python
import hmac
import hashlib
import time

def verify_webhook(payload: bytes, headers: dict, secret: str) -> bool:
    signature = headers.get("X-Webhook-Signature")
    timestamp = headers.get("X-Webhook-Timestamp")

    if not signature or not timestamp:
        return False

    if abs(time.time() - int(timestamp)) > 300:
        return False

    signed_payload = f"{timestamp}.{payload.decode()}"
    expected = hmac.new(
        secret.encode(), signed_payload.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)
```

```yaml
webhook_security:
  sending:
    - Sign every payload with HMAC-SHA256
    - Include timestamp in signature
    - Send unique event ID for idempotency
    - Use HTTPS only
    - Implement retry with exponential backoff
    - Rotate signing secrets periodically

  receiving:
    - Verify signature BEFORE any processing
    - Reject requests older than 5 minutes
    - Implement idempotency (store processed event IDs)
    - Return 200 quickly, process async
    - Rate limit incoming webhooks
    - Log all webhook events for audit
```

---

## 5. CORS Configuration

```python
CORS_CONFIG = {
    "allowed_origins": [
        "https://app.example.com",
        "https://admin.example.com",
    ],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
    "allowed_headers": ["Authorization", "Content-Type"],
    "allow_credentials": True,
    "max_age": 3600,
    "expose_headers": ["X-RateLimit-Remaining"],
}

cors_antipatterns = [
    "Access-Control-Allow-Origin: *",
    "reflect Origin header as Allow-Origin",
    "Access-Control-Allow-Origin: null",
]
```

---

## 6. Security Headers Checklist

```yaml
security_headers:
  X-Content-Type-Options: "nosniff"
  X-Frame-Options: "DENY"
  X-XSS-Protection: "0"
  Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
  Content-Security-Policy: "default-src 'self'; script-src 'self'"
  Referrer-Policy: "strict-origin-when-cross-origin"
  Permissions-Policy: "camera=(), microphone=(), geolocation=()"
  Cache-Control: "no-store, no-cache, must-revalidate, private"
```

---

## 7. Common API Vulnerabilities

### BOLA / IDOR

```python
# VULNERABLE
@app.get("/api/users/{user_id}/orders")
def get_orders(user_id: int):
    return db.query(Order).filter(Order.user_id == user_id).all()

# SECURE
@app.get("/api/users/{user_id}/orders")
def get_orders(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Forbidden")
    return db.query(Order).filter(Order.user_id == user_id).all()
```

### Mass Assignment

```python
# VULNERABLE
@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: dict):
    db.query(User).filter(User.id == user_id).update(data)

# SECURE
class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None

@app.put("/api/users/{user_id}")
def update_user(user_id: int, data: UserUpdateRequest):
    db.query(User).filter(User.id == user_id).update(data.dict(exclude_unset=True))
```

---

## 8. Idempotency Patterns

```python
class IdempotencyMiddleware:
    def __init__(self, cache):
        self.cache = cache

    async def process(self, idempotency_key: str, handler):
        cached = await self.cache.get(f"idempotency:{idempotency_key}")
        if cached:
            return cached

        lock = await self.cache.lock(f"lock:{idempotency_key}", timeout=30)
        if not lock:
            raise HTTPException(409, "Request already in progress")

        try:
            result = await handler()
            await self.cache.set(f"idempotency:{idempotency_key}", result, ttl=86400)
            return result
        finally:
            await lock.release()
```

---

## Quick Security Review Checklist

```
Authentication:
[ ] All endpoints require authentication (unless explicitly public)
[ ] API keys are in headers, not URLs
[ ] JWTs use RS256 with short expiry
[ ] OAuth 2.0 with PKCE for public clients
[ ] Token rotation implemented

Authorization:
[ ] Ownership check on every data access (BOLA prevention)
[ ] Role check on every privileged operation
[ ] Mass assignment protection
[ ] Response schemas filter sensitive fields

Input/Output:
[ ] Schema validation on all inputs
[ ] Size limits on all fields, arrays, and files
[ ] Parameterized queries
[ ] Generic error messages

Transport:
[ ] HTTPS everywhere (TLS 1.2+)
[ ] Security headers set
[ ] CORS explicitly configured
[ ] HSTS enabled

Operations:
[ ] Rate limiting per user/IP
[ ] Webhook signatures verified
[ ] Idempotency keys for mutations
[ ] Dependencies scanned for CVEs
```

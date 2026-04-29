# OWASP Top 10 Checklists

> Quick-reference checklists for the three most relevant OWASP Top 10 lists.
> Use during code reviews, security audits, and threat modeling.

---

## OWASP Web Application Top 10 (2021)

| # | Vulnerability | Description | Detection Patterns | Fix |
|---|--------------|-------------|-------------------|-----|
| **A01** | **Broken Access Control** | Users can act outside their intended permissions. | `GET /admin` accessible without admin role; user A accesses user B data via ID manipulation. | Deny by default. Enforce server-side access control. Log access failures. |
| **A02** | **Cryptographic Failures** | Sensitive data exposed due to weak or missing encryption. | Passwords stored as MD5/SHA1; HTTP endpoints serving sensitive data; hardcoded encryption keys. | HTTPS everywhere. TLS 1.2+. bcrypt/argon2 for passwords. Encrypt data at rest. |
| **A03** | **Injection** | Untrusted data sent to interpreter without validation. | String concatenation in queries: `f"SELECT * FROM users WHERE id={input}"`; `os.system(user_input)`. | Parameterized queries. ORM usage. Input validation (allowlist). Escape output. |
| **A04** | **Insecure Design** | Missing or ineffective security controls at design level. | No rate limit on password reset; unlimited free trial creation; no fraud detection. | Threat model during design. Secure design patterns. Limit resource consumption by user. |
| **A05** | **Security Misconfiguration** | Default configs, open cloud storage, unnecessary features enabled. | Default admin credentials; S3 bucket public; stack traces in production; CORS `*`. | Hardened defaults. Remove unused features. Automated config scanning. |
| **A06** | **Vulnerable Components** | Using libraries/frameworks with known vulnerabilities. | `npm audit` / `pip-audit` findings; CVE matches in dependency tree; EOL runtime versions. | Dependency scanning in CI/CD. Automated updates. Remove unused dependencies. |
| **A07** | **Auth Failures** | Broken authentication allows credential stuffing, brute force, session hijacking. | No rate limit on login; session ID in URL; no MFA option; weak password policy. | MFA. Rate limit login attempts. Secure session management. Rotate session on privilege change. |
| **A08** | **Software/Data Integrity** | Insecure CI/CD pipelines, unsigned updates, deserialization of untrusted data. | `pickle.loads(user_data)`; CDN scripts without SRI hashes; unsigned artifacts. | SRI for external scripts. Signed artifacts. Avoid deserializing untrusted data. |
| **A09** | **Logging/Monitoring Failures** | Insufficient logging, missing alerts, no incident response capability. | No logs for login failures; logs without user context; no alerting on suspicious patterns. | Log all auth events. Centralized logging. Alert on anomalies. Retention policy. |
| **A10** | **SSRF** | Server-side request forgery. | `fetch(user_provided_url)`; URL parameter for image processing; webhook URL without validation. | Allowlist for outbound URLs/IPs. Block private IP ranges. Disable HTTP redirects. |

---

## OWASP API Security Top 10 (2023)

| # | Vulnerability | Description | Detection Patterns | Fix |
|---|--------------|-------------|-------------------|-----|
| **API1** | **Broken Object Level Authorization (BOLA)** | API exposes endpoints that handle object IDs without ownership checks. | `GET /api/v1/users/{id}/orders` without ownership check; sequential/predictable IDs. | Check object ownership in every request. Use random UUIDs. Authorization middleware on all data endpoints. |
| **API2** | **Broken Authentication** | Weak or missing authentication mechanisms. | API keys in URLs; no token expiration; missing auth on internal APIs. | OAuth 2.0 / JWT with short expiry. Auth on ALL endpoints. Never expose credentials in responses. |
| **API3** | **Broken Object Property Level Authorization** | API exposes all object properties, allowing mass assignment or excessive data exposure. | Response includes `password_hash`, `internal_id`, `is_admin`; PUT/PATCH accepts `role` field. | Explicit response schemas. Block mass assignment. Separate read/write DTOs. |
| **API4** | **Unrestricted Resource Consumption** | API doesn't limit requests, payload sizes, or resource usage. | No pagination; unlimited file upload size; no rate limiting. | Rate limiting per user/IP. Pagination. Payload size limits. Timeouts on all operations. |
| **API5** | **Broken Function Level Authorization** | Missing authorization checks on administrative or privileged API functions. | `DELETE /api/users/{id}` accessible to regular users; admin endpoints without role check. | RBAC enforcement. Deny by default. Admin endpoints on separate route group with middleware. |
| **API6** | **Unrestricted Access to Sensitive Business Flows** | Automated abuse of legitimate business flows. | Automated account creation; bulk coupon redemption; no CAPTCHA on sensitive flows. | Rate limit business-critical flows. CAPTCHA/device fingerprinting. Anomaly detection. |
| **API7** | **Server Side Request Forgery (SSRF)** | API fetches remote resources without validating user-supplied URLs. | `POST /api/import {"url": "http://169.254.169.254/"}`. | URL allowlisting. Block internal IP ranges. Disable redirects. Network segmentation. |
| **API8** | **Security Misconfiguration** | Permissive CORS, verbose errors, default credentials. | `Access-Control-Allow-Origin: *`; detailed error messages with stack traces. | Hardened configs. Restrictive CORS. Generic error responses. Security headers. |
| **API9** | **Improper Inventory Management** | Deprecated/unpatched API versions still accessible. | `/api/v1/` still active alongside `/api/v3/`; internal debug endpoints exposed. | API inventory/catalog. Deprecate and remove old versions. API gateway as single entry point. |
| **API10** | **Unsafe Consumption of APIs** | API trusts data from third-party APIs without validation. | Blindly trusting webhook payloads; no validation on third-party API responses. | Validate ALL external API responses. Timeout and circuit breakers. TLS for all external calls. |

---

## OWASP LLM Top 10 (2025)

| # | Vulnerability | Description | Detection Patterns | Fix |
|---|--------------|-------------|-------------------|-----|
| **LLM01** | **Prompt Injection** | Attacker manipulates LLM via crafted input or poisoned context. | User input contains "ignore previous instructions"; unexpected tool calls after processing. | Input sanitization. Separate system/user prompts. Output validation. Human-in-the-loop for sensitive actions. |
| **LLM02** | **Sensitive Information Disclosure** | LLM reveals confidential data from training data, system prompts, or context. | Model outputs API keys, internal URLs, PII; system prompt extraction. | Strip secrets from context. Output filtering. Session isolation. |
| **LLM03** | **Supply Chain Vulnerabilities** | Compromised training data, model weights, plugins, or dependencies. | Poisoned fine-tuning datasets; malicious third-party plugins; tampered model files. | Verify model integrity. Audit plugins/tools. Signed artifacts. |
| **LLM04** | **Data and Model Poisoning** | Attacker corrupts training/fine-tuning data to influence model behavior. | Biased outputs after fine-tuning; backdoor triggers in model responses. | Data validation pipeline. Anomaly detection on training data. Regular model evaluation. |
| **LLM05** | **Improper Output Handling** | LLM output passed to downstream systems without sanitization. | LLM output rendered as HTML without escaping; LLM-generated SQL executed directly. | Treat LLM output as untrusted. Sanitize before rendering. Never pass LLM output to `eval()`. |
| **LLM06** | **Excessive Agency** | LLM agent has too many permissions, can perform destructive actions without approval. | Agent can delete files, send emails, modify databases without confirmation. | Least-privilege tool access. Human-in-the-loop for destructive actions. Read-only by default. |
| **LLM07** | **System Prompt Leakage** | Attacker extracts the system prompt. | Prompts like "what are your instructions?"; indirect extraction via role-play. | Don't rely on system prompt secrecy for security. Defense in depth. Monitor for extraction attempts. |
| **LLM08** | **Vector and Embedding Weaknesses** | Manipulation of RAG retrieval through poisoned embeddings or adversarial documents. | Irrelevant documents surfacing in RAG; poisoned knowledge base entries. | Validate RAG sources. Access control on knowledge base. Regular KB audits. |
| **LLM09** | **Misinformation** | LLM generates false/misleading content presented as fact. | Confident assertions about nonexistent APIs; fabricated citations; incorrect code. | Grounding with verified sources (RAG). Confidence scoring. Human review for critical outputs. |
| **LLM10** | **Unbounded Consumption** | Excessive resource usage through crafted prompts. | Extremely long context inputs; recursive agent loops; no budget limits. | Token limits per request/session. Budget caps per user. Iteration limits for agents. |

---

## Quick Audit Checklist

```
[ ] Authentication on all endpoints (A07/API2)
[ ] Authorization checks on every data access (A01/API1/API5)
[ ] Input validation and parameterized queries (A03)
[ ] No sensitive data in logs or error messages (A09/API8)
[ ] Dependencies up to date, no known CVEs (A06)
[ ] Rate limiting on all public endpoints (API4)
[ ] HTTPS everywhere, TLS 1.2+ (A02)
[ ] Security headers set (CSP, HSTS, X-Frame-Options) (A05)
[ ] LLM output treated as untrusted (LLM05)
[ ] Agent tool access follows least privilege (LLM06)
[ ] Prompt injection defenses in place (LLM01)
[ ] Token/cost budgets configured (LLM10)
```

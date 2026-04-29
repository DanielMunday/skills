# Incident Response Playbooks

> Extended playbooks for common security incidents.
> Each follows 5 phases: Contain, Assess, Remediate, Prevent, Document.
> Use with `007 incident` or when responding to any security event.

---

## Playbook 1: Data Breach

**Severity:** CRITICAL | **Response Time:** Immediate (< 15 minutes to begin containment)

### Phase 1: Contain
- [ ] Identify the source of the breach
- [ ] Revoke compromised credentials immediately
- [ ] Isolate affected systems from the network
- [ ] Block the attacker's IP/access path if identifiable
- [ ] Preserve forensic evidence (do NOT wipe or restart affected systems yet)

### Phase 2: Assess
- [ ] Determine what data was exposed
- [ ] Determine scope: how many users/records affected
- [ ] Identify the attack timeline
- [ ] Review access logs to trace the attacker's actions

### Phase 3: Remediate
- [ ] Patch the vulnerability that was exploited
- [ ] Force password reset for all affected users
- [ ] Rotate all potentially compromised secrets
- [ ] Clean malware/backdoors if installed

### Phase 4: Prevent
- [ ] Implement missing access controls
- [ ] Add monitoring for the attack pattern used
- [ ] Enable encryption at rest for exposed data stores
- [ ] Review and restrict access permissions

### Phase 5: Document
- [ ] Complete incident timeline with timestamps
- [ ] Root cause analysis (RCA)
- [ ] Regulatory notifications (LGPD: 72 hours, GDPR: 72 hours)
- [ ] User notification if PII was exposed

---

## Playbook 2: DDoS / DoS

**Severity:** HIGH | **Response Time:** < 5 minutes to begin mitigation

### Phase 1: Contain
- [ ] Confirm it is an attack (not a legitimate traffic spike)
- [ ] Activate CDN/WAF DDoS protection
- [ ] Enable aggressive rate limiting
- [ ] Block obvious attack source IPs/ranges at the edge
- [ ] Scale infrastructure if possible

### Phase 4: Prevent
- [ ] Implement permanent rate limiting
- [ ] Deploy CDN with DDoS protection for all public endpoints
- [ ] Set up auto-scaling with cost limits
- [ ] Implement challenge-based protection for sensitive endpoints

---

## Playbook 3: Ransomware

**Severity:** CRITICAL | **Response Time:** Immediate (< 10 minutes to isolate)

### Phase 1: Contain
- [ ] IMMEDIATELY disconnect affected systems from network
- [ ] Do NOT power off systems (preserves forensic evidence in memory)
- [ ] Identify patient zero (first infected system)
- [ ] Isolate backup systems to prevent encryption

### Phase 2: Assess
- [ ] Identify the ransomware variant (check ransom note, file extensions)
- [ ] Check if backups are intact and uncompromised
- [ ] Check for decryption tools (NoMoreRansom.org)
- [ ] Determine entry point

### Phase 4: Prevent
- [ ] Implement network segmentation
- [ ] Implement 3-2-1 backup strategy (3 copies, 2 media types, 1 offsite)
- [ ] Air-gapped or immutable backup storage
- [ ] Regular backup restoration tests

---

## Playbook 4: Supply Chain Compromise

**Severity:** CRITICAL | **Response Time:** < 30 minutes to assess, < 2 hours to contain

### Phase 1: Contain
- [ ] Identify the compromised dependency/package/vendor
- [ ] Pin to last known good version immediately
- [ ] Halt all deployments until assessment is complete
- [ ] Check if compromised code was executed in production

### Phase 4: Prevent
- [ ] Implement dependency pinning with lock files
- [ ] Enable integrity checking (checksums, signatures)
- [ ] Set up automated vulnerability scanning (Dependabot, Snyk, pip-audit)
- [ ] Implement SBOM (Software Bill of Materials)

---

## Playbook 5: Token/Secret Leaked

**Severity:** CRITICAL | **Response Time:** IMMEDIATE

### Phase 1: Contain
- [ ] Revoke the token/key **immediately**
- [ ] If exposed in public repository: revoke NOW, history can be cleaned later
- [ ] Verify if there are other secrets in the same commit/file

### Phase 2: Assess
- [ ] When did the leak occur?
- [ ] Which systems does the secret access?
- [ ] Is there evidence of unauthorized use?

### Phase 3: Remediate
- [ ] Generate a new secret
- [ ] Update all systems that use the secret
- [ ] Move secret to vault/secrets manager if not already there

### Phase 4: Prevent
- [ ] Implement pre-commit hook to detect secrets (gitleaks, detect-secrets)
- [ ] Review secret management policy
- [ ] Train team on secret hygiene

---

## Playbook 6: Prompt Injection / Jailbreak

**Severity:** HIGH | **Response Time:** URGENT

### Phase 1: Contain
- [ ] Identify the malicious prompt
- [ ] Check if the agent executed unauthorized actions
- [ ] Suspend the agent if necessary

### Phase 2: Assess
- [ ] What actions did the agent perform?
- [ ] What data was accessed/leaked?
- [ ] Is there cascade to other agents?

### Phase 3: Remediate
- [ ] Strengthen system prompt with guardrails
- [ ] Add input filter
- [ ] Limit tools available to the agent
- [ ] Add content filter on output

---

## Playbook 7: Credential Stuffing

**Severity:** HIGH | **Response Time:** < 30 minutes

### Phase 1: Contain
- [ ] Enable aggressive rate limiting on login endpoints
- [ ] Block attacking IP ranges at WAF/CDN level
- [ ] Enable CAPTCHA on login forms
- [ ] Temporarily lock accounts with multiple failed attempts

### Phase 4: Prevent
- [ ] Implement MFA
- [ ] Deploy credential stuffing detection
- [ ] Check passwords against breach databases on registration/change
- [ ] Device fingerprinting and anomaly detection

---

## Severity Classification Reference

| Severity | Examples | Response Time | Escalation |
|----------|---------|---------------|------------|
| **CRITICAL** | Data breach, ransomware, active exploitation | < 15 min | Immediate: CEO, CTO, Legal |
| **HIGH** | DDoS, credential stuffing, supply chain compromise | < 30 min | Within 1 hour: CTO, Engineering Lead |
| **MEDIUM** | API abuse, single account compromise | < 2 hours | Within 4 hours: Engineering Lead |
| **LOW** | Failed attack attempt, minor misconfiguration | < 24 hours | Next business day: Team Lead |

---

## General Communication Template

```
SUBJECT: [{SEVERITY}] Security Incident - {Brief Description}

STATUS: {Active / Contained / Resolved}
SEVERITY: {CRITICAL / HIGH / MEDIUM / LOW}
INCIDENT ID: INC-{YYYY}-{NNN}
DETECTED: {timestamp}
INCIDENT COMMANDER: {name}

SUMMARY:
{2-3 sentences describing what happened, what is affected, and current status.}

IMPACT:
- Systems: {affected systems}
- Data: {type of data affected}
- Users: {number of affected users}

CURRENT STATUS:
- Phase: {Contain / Assess / Remediate / Prevent / Document}
- Actions completed: {list}
- Actions in progress: {list}

NEXT UPDATE: {timestamp}
CONTACT: {incident commander contact}
```

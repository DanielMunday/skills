"""007 Full Audit -- Complete 6-phase security audit orchestrator.

Executes the full 007 security analysis pipeline:
  Phase 1: Surface mapping (files, entry points, dependencies)
  Phase 2: Threat modeling hints (STRIDE component flags)
  Phase 3: Security checklist (aggregates all scanner results)
  Phase 4: Red team scenarios (attack narratives from findings)
  Phase 5: Blue team recommendations (remediation by severity/effort)
  Phase 6: Final verdict (weighted domain scores)

Usage:
    python full_audit.py --target /path/to/project
    python full_audit.py --target /path/to/project --output json
    python full_audit.py --target /path/to/project --verbose
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    BASE_DIR, DATA_DIR, REPORTS_DIR,
    SCORING_WEIGHTS, SCORING_LABELS, SCORE_HISTORY_PATH,
    SCANNABLE_EXTENSIONS, SKIP_DIRECTORIES, LIMITS,
    ensure_directories, get_verdict, get_timestamp,
    log_audit_event, setup_logging, calculate_weighted_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent / "scanners"))

import secrets_scanner
import dependency_scanner
import injection_scanner
import quick_scan

logger = setup_logging("007-full-audit")


# ---------------------------------------------------------------------------
# Red Team Scenario Templates
# ---------------------------------------------------------------------------

_RED_TEAM_TEMPLATES = {
    "secret": (
        "SCENARIO: Credential Theft\n"
        "PERSONA: External attacker or malicious insider\n"
        "STEPS:\n"
        "  1. Attacker discovers hardcoded secret via public repo scan or code review\n"
        "  2. Uses secret to authenticate to target service\n"
        "  3. Exfiltrates data or performs unauthorized actions\n"
        "DANO: Full access to dependent systems until secret is rotated\n"
        "DIFICULDADE: facil"
    ),
    "sql_injection": (
        "SCENARIO: SQL Injection → Data Exfiltration\n"
        "PERSONA: Usuario malicioso com acesso a endpoint vulneravel\n"
        "STEPS:\n"
        "  1. Attacker identifies unsanitized input field\n"
        "  2. Injects UNION SELECT payload to extract sensitive tables\n"
        "  3. Dumps user credentials or PII\n"
        "DANO: Full database compromise\n"
        "DIFICULDADE: medio"
    ),
    "code_injection": (
        "SCENARIO: Remote Code Execution via eval/exec\n"
        "PERSONA: Usuario malicioso\n"
        "STEPS:\n"
        "  1. Attacker submits crafted payload to eval/exec endpoint\n"
        "  2. Executes OS commands with application privileges\n"
        "  3. Establishes persistence or exfiltrates secrets\n"
        "DANO: Full server compromise\n"
        "DIFICULDADE: medio"
    ),
    "command_injection": (
        "SCENARIO: OS Command Injection\n"
        "PERSONA: Usuario malicioso\n"
        "STEPS:\n"
        "  1. Attacker injects shell metacharacters (;, |, &&) into input\n"
        "  2. Application passes unsanitized input to shell\n"
        "  3. Attacker executes arbitrary commands\n"
        "DANO: Server compromise, lateral movement\n"
        "DIFICULDADE: medio"
    ),
    "prompt_injection": (
        "SCENARIO: Prompt Injection → Agent Hijacking\n"
        "PERSONA: Usuario malicioso interagindo com agente IA\n"
        "STEPS:\n"
        "  1. Attacker crafts input containing 'ignore previous instructions'\n"
        "  2. Agent follows attacker instructions instead of system prompt\n"
        "  3. Agent leaks secrets, exfiltrates data, or performs unauthorized actions\n"
        "DANO: Agent takeover, data leakage, unauthorized tool execution\n"
        "DIFICULDADE: facil"
    ),
    "supply_chain": (
        "SCENARIO: Compromised Dependency\n"
        "PERSONA: Supply chain attacker\n"
        "STEPS:\n"
        "  1. Attacker publishes malicious version of a dependency\n"
        "  2. Unpinned dependency pulled during build\n"
        "  3. Malicious code executes at import or install time\n"
        "DANO: Full code execution in build/production environment\n"
        "DIFICULDADE: medio"
    ),
    "ssrf": (
        "SCENARIO: SSRF → Internal Service Access\n"
        "PERSONA: External attacker\n"
        "STEPS:\n"
        "  1. Attacker submits internal URL (e.g. http://169.254.169.254/)\n"
        "  2. Server fetches the URL and returns response\n"
        "  3. Attacker reads cloud metadata, internal services\n"
        "DANO: Cloud credential theft, internal network access\n"
        "DIFICULDADE: facil"
    ),
    "path_traversal": (
        "SCENARIO: Path Traversal → Arbitrary File Read\n"
        "PERSONA: External attacker\n"
        "STEPS:\n"
        "  1. Attacker submits path like ../../etc/passwd\n"
        "  2. Application reads and returns file outside intended directory\n"
        "  3. Attacker reads sensitive configs, secrets, source code\n"
        "DANO: Information disclosure, potential credential theft\n"
        "DIFICULDADE: facil"
    ),
}


# ---------------------------------------------------------------------------
# Blue Team Recommendation Templates
# ---------------------------------------------------------------------------

_BLUE_TEAM_TEMPLATES = {
    "secret": [
        "Move all secrets to environment variables or a secrets manager (Vault, AWS SSM)",
        "Add pre-commit hooks to detect secrets (gitleaks, detect-secrets)",
        "Implement automatic secret rotation (90-day maximum)",
        "Audit git history for accidentally committed secrets",
    ],
    "sql_injection": [
        "Replace all string concatenation in SQL with parameterized queries",
        "Use an ORM (SQLAlchemy, Django ORM) to abstract query construction",
        "Add input validation and type checking at all API boundaries",
        "Enable WAF rules for SQL injection patterns",
    ],
    "code_injection": [
        "Remove all uses of eval() and exec() with external input",
        "Replace with safe alternatives (ast.literal_eval for data parsing)",
        "Run code execution in a sandboxed environment (Docker, nsjail)",
        "Add static analysis (Semgrep, Bandit) to CI/CD pipeline",
    ],
    "command_injection": [
        "Replace os.system() and shell=True subprocess with shell=False equivalents",
        "Use allowlists for allowed commands",
        "Validate and sanitize all inputs before passing to shell commands",
    ],
    "prompt_injection": [
        "Add input sanitization to strip/detect injection patterns",
        "Implement dual-LLM validation (one LLM processes, another validates)",
        "Add output filtering to catch unexpected sensitive data",
        "Implement human-in-the-loop for destructive agent actions",
        "Add iteration and cost limits to agent execution",
    ],
    "supply_chain": [
        "Pin all dependencies to exact versions with hashes",
        "Add automated dependency scanning to CI/CD (Dependabot, pip-audit, npm audit)",
        "Review and approve all dependency updates via pull requests",
        "Generate and maintain a Software Bill of Materials (SBOM)",
    ],
    "ssrf": [
        "Implement URL allowlist for all outbound HTTP requests",
        "Block private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x)",
        "Disable HTTP redirects or validate redirect destinations",
        "Use network egress filtering at infrastructure level",
    ],
    "path_traversal": [
        "Use Path.resolve() and verify the result is within the allowed base directory",
        "Avoid passing user-controlled paths to file operations",
        "Use allowlists for permitted file extensions and directories",
    ],
}


# ---------------------------------------------------------------------------
# Phase 1: Surface Mapping
# ---------------------------------------------------------------------------

def phase1_surface_map(target: Path) -> dict:
    """Inventory the project surface: files, entry points, dependencies."""
    surface = {
        "total_files": 0,
        "file_types": {},
        "entry_points": [],
        "dependency_files": [],
        "config_files": [],
        "sensitive_files": [],
    }

    _ENTRY_POINT_NAMES = {"main.py", "app.py", "server.py", "index.js", "index.ts", "manage.py"}
    _DEP_FILES = {"requirements.txt", "package.json", "pyproject.toml", "Pipfile", "go.mod"}
    _SENSITIVE_NAMES = {".env", ".env.local", ".env.production"}
    _CONFIG_EXTS = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".json"}

    for root, dirs, filenames in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]
        for fname in filenames:
            surface["total_files"] += 1
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()

            surface["file_types"][ext] = surface["file_types"].get(ext, 0) + 1

            if fname.lower() in _ENTRY_POINT_NAMES:
                surface["entry_points"].append(str(fpath))
            if fname in _DEP_FILES or fname.startswith("requirements"):
                surface["dependency_files"].append(str(fpath))
            if fname.lower() in _SENSITIVE_NAMES or fname.lower().startswith(".env"):
                surface["sensitive_files"].append(str(fpath))
            if ext in _CONFIG_EXTS:
                surface["config_files"].append(str(fpath))

    return surface


# ---------------------------------------------------------------------------
# Phase 2: Threat Modeling Hints
# ---------------------------------------------------------------------------

def phase2_threat_hints(findings: list[dict]) -> list[str]:
    """Generate STRIDE-based threat modeling hints from scanner findings."""
    hints = []
    injection_types = {f.get("injection_type") for f in findings if f.get("injection_type")}
    patterns = {f.get("pattern") for f in findings if f.get("pattern")}

    if "code_injection" in injection_types or "command_injection" in injection_types:
        hints.append("[STRIDE-T] Tampering via code/command injection detected — verify all exec/eval inputs")
    if "sql_injection" in injection_types:
        hints.append("[STRIDE-T] SQL injection patterns found — parameterize ALL queries")
    if "prompt_injection" in injection_types:
        hints.append("[STRIDE-S] Spoofing/Tampering via prompt injection — harden system prompts")
    if "ssrf" in injection_types:
        hints.append("[STRIDE-I] Information Disclosure via SSRF — implement URL allowlist")
    if "path_traversal" in injection_types:
        hints.append("[STRIDE-I] Path traversal detected — validate and contain file paths")
    if any("secret" in str(p) for p in patterns):
        hints.append("[STRIDE-I] Hardcoded secrets detected — move to secrets manager immediately")
    if any("supply_chain" in str(f.get("type", "")) for f in findings):
        hints.append("[STRIDE-T] Supply chain risk — pin dependencies and enable integrity checks")

    if not hints:
        hints.append("[STRIDE] No critical threat indicators detected in automated scan")

    return hints


# ---------------------------------------------------------------------------
# Phase 4: Red Team Scenarios
# ---------------------------------------------------------------------------

def phase4_red_team(findings: list[dict]) -> list[str]:
    """Generate red team attack scenarios based on actual findings."""
    scenarios = []
    seen_types: set[str] = set()

    type_map = {
        "secret": "secret",
        "supply_chain": "supply_chain",
    }
    injection_map = {
        "sql_injection": "sql_injection",
        "code_injection": "code_injection",
        "command_injection": "command_injection",
        "prompt_injection": "prompt_injection",
        "ssrf": "ssrf",
        "path_traversal": "path_traversal",
    }

    for finding in findings:
        ftype = finding.get("type", "")
        itype = finding.get("injection_type", "")

        key = injection_map.get(itype) or type_map.get(ftype)
        if key and key not in seen_types:
            seen_types.add(key)
            template = _RED_TEAM_TEMPLATES.get(key)
            if template:
                scenarios.append(template)

    return scenarios


# ---------------------------------------------------------------------------
# Phase 5: Blue Team Recommendations
# ---------------------------------------------------------------------------

def phase5_blue_team(findings: list[dict]) -> dict[str, list[str]]:
    """Generate prioritized blue team recommendations from findings."""
    recommendations: dict[str, set[str]] = {}
    seen_keys: set[str] = set()

    for finding in findings:
        ftype = finding.get("type", "")
        itype = finding.get("injection_type", "")

        keys = []
        if itype:
            keys.append(itype)
        if ftype in ("secret", "supply_chain"):
            keys.append(ftype)

        for key in keys:
            if key not in seen_keys and key in _BLUE_TEAM_TEMPLATES:
                seen_keys.add(key)
                sev = finding.get("severity", "INFO")
                recommendations.setdefault(sev, set()).update(_BLUE_TEAM_TEMPLATES[key])

    return {sev: list(recs) for sev, recs in recommendations.items()}


# ---------------------------------------------------------------------------
# Phase 6: Scoring
# ---------------------------------------------------------------------------

def phase6_score(
    secrets_report: dict,
    dep_report: dict,
    inj_report: dict,
    quick_report: dict,
) -> tuple[dict[str, float], float, dict]:
    """Compute per-domain scores and final weighted verdict."""
    def _score_from_count(count: int) -> float:
        deduction = min(count * 5, 100)
        return max(0.0, float(100 - deduction))

    domain_scores: dict[str, float] = {
        "secrets":          float(secrets_report.get("score", 50)),
        "input_validation": float(inj_report.get("score", 50)),
        "authn_authz":      50.0,
        "data_protection":  float(secrets_report.get("score", 50)),
        "resilience":       50.0,
        "monitoring":       50.0,
        "supply_chain":     float(dep_report.get("score", 50)),
        "compliance":       float(quick_report.get("score", 50)),
    }

    final_score = calculate_weighted_score(domain_scores)
    verdict = get_verdict(final_score)
    return domain_scores, final_score, verdict


# ---------------------------------------------------------------------------
# Report Formatters
# ---------------------------------------------------------------------------

def _bar(score: float, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return "[" + "#" * filled + "." * (width - filled) + "]"


def format_text_report(
    target: str,
    surface: dict,
    threat_hints: list[str],
    all_findings: list[dict],
    red_team: list[str],
    blue_team: dict[str, list[str]],
    domain_scores: dict[str, float],
    final_score: float,
    verdict: dict,
    elapsed: float,
) -> str:
    lines: list[str] = []

    lines.append("=" * 72)
    lines.append("  007 FULL SECURITY AUDIT REPORT")
    lines.append("=" * 72)
    lines.append(f"  Target:    {target}")
    lines.append(f"  Timestamp: {get_timestamp()}")
    lines.append(f"  Duration:  {elapsed:.2f}s")
    lines.append("")

    # Phase 1
    lines.append("━" * 72)
    lines.append("  FASE 1: SUPERFICIE DE ATAQUE")
    lines.append("━" * 72)
    lines.append(f"  Total files:       {surface['total_files']}")
    lines.append(f"  Entry points:      {len(surface['entry_points'])}")
    lines.append(f"  Dependency files:  {len(surface['dependency_files'])}")
    lines.append(f"  Sensitive files:   {len(surface['sensitive_files'])}")
    for sf in surface["sensitive_files"]:
        lines.append(f"    [!] {sf}")
    lines.append("")

    # Phase 2
    lines.append("━" * 72)
    lines.append("  FASE 2: THREAT MODEL HINTS (STRIDE)")
    lines.append("━" * 72)
    for hint in threat_hints:
        lines.append(f"  {hint}")
    lines.append("")

    # Phase 3
    lines.append("━" * 72)
    lines.append("  FASE 3: CHECKLIST — FINDINGS SUMMARY")
    lines.append("━" * 72)
    from collections import Counter
    sev_counts = Counter(f.get("severity", "INFO") for f in all_findings)
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        count = sev_counts.get(sev, 0)
        bar = "#" * min(count, 40)
        lines.append(f"    {sev:<10} {count:>5}  {bar}")
    lines.append("")

    # Phase 4
    if red_team:
        lines.append("━" * 72)
        lines.append("  FASE 4: RED TEAM SCENARIOS")
        lines.append("━" * 72)
        for i, scenario in enumerate(red_team, 1):
            lines.append(f"  Scenario {i}:")
            for scenario_line in scenario.splitlines():
                lines.append(f"    {scenario_line}")
            lines.append("")

    # Phase 5
    if blue_team:
        lines.append("━" * 72)
        lines.append("  FASE 5: BLUE TEAM RECOMMENDATIONS")
        lines.append("━" * 72)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            recs = blue_team.get(sev, [])
            if recs:
                lines.append(f"  [{sev}]")
                for rec in recs:
                    lines.append(f"    • {rec}")
        lines.append("")

    # Phase 6
    lines.append("━" * 72)
    lines.append("  FASE 6: SCORING & VEREDITO")
    lines.append("━" * 72)
    lines.append(f"    {'Domain':<30} {'Weight':>6}  {'Score':>5}  Bar")
    lines.append(f"    {'-'*30} {'-'*6}  {'-'*5}  {'-'*22}")
    for domain, weight in SCORING_WEIGHTS.items():
        score = domain_scores.get(domain, 0.0)
        label = SCORING_LABELS.get(domain, domain)
        lines.append(f"    {label:<30} {weight*100:>5.0f}%  {score:>5.1f}  {_bar(score)}")
    lines.append("")
    lines.append("=" * 72)
    lines.append(f"  FINAL SCORE:  {final_score:.1f} / 100")
    lines.append(f"  VERDICT:      {verdict['emoji']} {verdict['label']}")
    lines.append(f"                {verdict['description']}")
    lines.append("=" * 72)
    lines.append("")

    return "\n".join(lines)


def build_json_report(
    target: str,
    surface: dict,
    threat_hints: list[str],
    all_findings: list[dict],
    red_team: list[str],
    blue_team: dict[str, list[str]],
    domain_scores: dict[str, float],
    final_score: float,
    verdict: dict,
    elapsed: float,
) -> dict:
    return {
        "report": "full_audit",
        "target": target,
        "timestamp": get_timestamp(),
        "duration_seconds": round(elapsed, 3),
        "surface": surface,
        "threat_hints": threat_hints,
        "total_findings": len(all_findings),
        "red_team_scenarios": len(red_team),
        "blue_team_recommendations": {k: len(v) for k, v in blue_team.items()},
        "domain_scores": domain_scores,
        "final_score": final_score,
        "verdict": {
            "label": verdict["label"],
            "description": verdict["description"],
            "emoji": verdict["emoji"],
        },
    }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_audit(
    target_path: str,
    output_format: str = "text",
    verbose: bool = False,
) -> dict:
    if verbose:
        logger.setLevel("DEBUG")

    ensure_directories()

    target = Path(target_path).resolve()
    if not target.exists():
        logger.error("Target path does not exist: %s", target)
        sys.exit(1)
    if not target.is_dir():
        logger.error("Target is not a directory: %s", target)
        sys.exit(1)

    logger.info("Starting full 6-phase audit of %s", target)
    start_time = time.time()
    target_str = str(target)

    # Run all scanners
    logger.info("Phase 3: Running scanners...")
    try:
        secrets_report = secrets_scanner.run_scan(target_str, "json", verbose)
    except SystemExit:
        secrets_report = {"findings": [], "score": 50}

    try:
        dep_report = dependency_scanner.run_scan(target_str, "json", verbose)
    except SystemExit:
        dep_report = {"findings": [], "score": 50}

    try:
        inj_report = injection_scanner.run_scan(target_str, "json", verbose)
    except SystemExit:
        inj_report = {"findings": [], "score": 50}

    try:
        quick_report = quick_scan.run_scan(target_str, "json", verbose)
    except SystemExit:
        quick_report = {"findings": [], "score": 50}

    all_findings = (
        secrets_report.get("findings", []) +
        dep_report.get("findings", []) +
        inj_report.get("findings", []) +
        quick_report.get("findings", [])
    )

    # Phases
    logger.info("Phase 1: Surface mapping...")
    surface = phase1_surface_map(target)

    logger.info("Phase 2: Threat modeling hints...")
    threat_hints = phase2_threat_hints(all_findings)

    logger.info("Phase 4: Red team scenarios...")
    red_team = phase4_red_team(all_findings)

    logger.info("Phase 5: Blue team recommendations...")
    blue_team = phase5_blue_team(all_findings)

    logger.info("Phase 6: Scoring...")
    domain_scores, final_score, verdict = phase6_score(
        secrets_report, dep_report, inj_report, quick_report
    )

    elapsed = time.time() - start_time
    logger.info("Full audit complete in %.2fs: score=%.1f, verdict=%s",
                elapsed, final_score, verdict["label"])

    log_audit_event(
        action="full_audit",
        target=target_str,
        result=f"final_score={final_score}, verdict={verdict['label']}, findings={len(all_findings)}",
        details={"domain_scores": domain_scores, "duration_seconds": round(elapsed, 3)},
    )

    report = build_json_report(
        target=target_str,
        surface=surface,
        threat_hints=threat_hints,
        all_findings=all_findings,
        red_team=red_team,
        blue_team=blue_team,
        domain_scores=domain_scores,
        final_score=final_score,
        verdict=verdict,
        elapsed=elapsed,
    )

    if output_format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_text_report(
            target=target_str,
            surface=surface,
            threat_hints=threat_hints,
            all_findings=all_findings,
            red_team=red_team,
            blue_team=blue_team,
            domain_scores=domain_scores,
            final_score=final_score,
            verdict=verdict,
            elapsed=elapsed,
        ))

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="007 Full Audit -- Complete 6-phase security audit.",
        epilog="Example: python full_audit.py --target ./my-project --output json",
    )
    parser.add_argument("--target", required=True, help="Path to the directory to audit.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--verbose", action="store_true", default=False)

    args = parser.parse_args()
    run_audit(target_path=args.target, output_format=args.output, verbose=args.verbose)

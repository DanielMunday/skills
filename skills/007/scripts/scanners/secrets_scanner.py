"""007 Secrets Scanner -- Deep scanner for secrets and credentials.

Analyzes source files, config files, .env files, Docker files, and CI/CD
configs for hardcoded secrets, high-entropy strings, base64-encoded tokens,
and URL-embedded credentials.

Usage:
    python secrets_scanner.py --target /path/to/project
    python secrets_scanner.py --target /path/to/project --output json --verbose
"""

import argparse
import base64
import json
import math
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = config.setup_logging("007-secrets-scanner")

_EXTRA_PATTERN_DEFS = [
    ("url_embedded_credentials", r"""https?://[^:\s]+:[^@\s]+@[^\s/]+""", "HIGH"),
    ("stripe_key", r"""(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{20,}""", "CRITICAL"),
    ("google_api_key", r"""AIza[0-9A-Za-z\-_]{35}""", "HIGH"),
    ("sendgrid_key", r"""SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}""", "CRITICAL"),
    ("npm_token", r"""(?:npm_)[A-Za-z0-9]{36}""", "CRITICAL"),
    ("jwt_token", r"""eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}""", "MEDIUM"),
    ("azure_storage_key", r"""(?i)(?:accountkey|storage[_-]?key)\s*[:=]\s*['\"]\S{44,}['\"]""", "CRITICAL"),
]

EXTRA_PATTERNS = [(name, re.compile(pattern), severity)
                  for name, pattern, severity in _EXTRA_PATTERN_DEFS]

ALL_SECRET_PATTERNS = list(config.SECRET_PATTERNS) + EXTRA_PATTERNS

ENV_FILE_PATTERNS = {".env", ".env.local", ".env.production", ".env.staging",
                     ".env.development", ".env.test", ".env.example", ".env.sample"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
SHELL_EXTENSIONS = {".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"}
DOCKER_PREFIXES = ("Dockerfile", "dockerfile", "docker-compose")
PRIVATE_KEY_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}

_TEST_FILE_PATTERNS = re.compile(
    r"""(?i)(?:^test_|_test\.py$|\.test\.[jt]sx?$|\.spec\.[jt]sx?$|__tests__|fixtures?[/\\])"""
)
_PLACEHOLDER_PATTERN = re.compile(
    r"""(?i)(?:example|placeholder|changeme|xxx+|your[_-]?key[_-]?here|"""
    r"""insert[_-]?here|replace[_-]?me|todo|fixme|dummy|fake|sample|test123)"""
)
_COMMENT_LINE_RE = re.compile(r"""^\s*(?:#|//|/\*|\*|;)""", re.IGNORECASE)
_MARKDOWN_CODE_FENCE = re.compile(r"""^\s*```""")


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    length = len(s)
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


_BASE64_RE = re.compile(r"""[A-Za-z0-9+/]{20,}={0,2}""")


def _check_base64_secret(token: str) -> bool:
    padded = token + "=" * (-len(token) % 4)
    try:
        decoded = base64.b64decode(padded, validate=True)
        decoded_str = decoded.decode("ascii", errors="replace")
        return shannon_entropy(decoded_str) > 4.0 and len(decoded) >= 12
    except Exception:
        return False


_IP_RE = re.compile(r"""\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b""")
_SAFE_IP_PREFIXES = ("127.", "0.", "10.", "192.168.", "169.254.", "255.")


def _is_private_or_localhost(ip: str) -> bool:
    if ip.startswith(_SAFE_IP_PREFIXES):
        return True
    parts = ip.split(".")
    try:
        if parts[0] == "172" and 16 <= int(parts[1]) <= 31:
            return True
    except (IndexError, ValueError):
        pass
    return False


def _classify_file(filepath: Path) -> str:
    name = filepath.name.lower()
    suffix = filepath.suffix.lower()
    if name.startswith(".env") or name in ENV_FILE_PATTERNS:
        return "env"
    if suffix in PRIVATE_KEY_EXTENSIONS:
        return "private_key"
    if suffix in CONFIG_EXTENSIONS:
        return "config"
    if suffix in SHELL_EXTENSIONS:
        return "shell"
    if any(name.startswith(p) for p in DOCKER_PREFIXES):
        return "docker"
    if suffix in config.SCANNABLE_EXTENSIONS:
        return "source"
    return "other"


def _should_scan_file(filepath: Path) -> bool:
    name = filepath.name.lower()
    suffix = filepath.suffix.lower()
    if name.startswith(".env"):
        return True
    if suffix in PRIVATE_KEY_EXTENSIONS:
        return True
    if any(name.startswith(p) for p in DOCKER_PREFIXES):
        return True
    for ext in config.SCANNABLE_EXTENSIONS:
        if name.endswith(ext):
            return True
    return suffix in config.SCANNABLE_EXTENSIONS


def collect_files(target: Path) -> list[Path]:
    files: list[Path] = []
    max_files = config.LIMITS["max_files_per_scan"]
    for root, dirs, filenames in os.walk(target):
        dirs[:] = [d for d in dirs if d not in config.SKIP_DIRECTORIES]
        for fname in filenames:
            if len(files) >= max_files:
                return files
            fpath = Path(root) / fname
            if _should_scan_file(fpath):
                files.append(fpath)
    return files


def _redact(text: str, keep: int = 6) -> str:
    text = text.strip()
    return text if len(text) <= keep else text[:keep] + "****"


def _snippet(line: str, match_start: int, context: int = 50) -> str:
    start = max(0, match_start - context // 2)
    end = min(len(line), match_start + context)
    return _redact(line[start:end].strip())


def scan_file(filepath: Path, verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    max_findings = config.LIMITS["max_findings_per_file"]
    file_str = str(filepath)
    file_category = _classify_file(filepath)
    is_test = bool(_TEST_FILE_PATTERNS.search(filepath.name))
    is_env_ex = filepath.name.lower() in (".env.example", ".env.sample", ".env.template")

    if filepath.suffix.lower() in PRIVATE_KEY_EXTENSIONS:
        findings.append({"type": "secret", "pattern": "private_key_file",
                         "severity": "MEDIUM" if is_test else "CRITICAL",
                         "file": file_str, "line": 0,
                         "snippet": f"Private key file: {filepath.name}", "category": file_category})

    try:
        size = filepath.stat().st_size
    except OSError:
        return findings
    if size > config.LIMITS["max_file_size_bytes"]:
        return findings

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    lines = text.splitlines()
    in_markdown_code_block = False

    for line_num, line in enumerate(lines, start=1):
        if len(findings) >= max_findings:
            break
        stripped = line.strip()
        if not stripped:
            continue
        if _MARKDOWN_CODE_FENCE.match(stripped):
            in_markdown_code_block = not in_markdown_code_block
            continue

        is_comment = bool(_COMMENT_LINE_RE.match(stripped))
        is_placeholder = bool(_PLACEHOLDER_PATTERN.search(stripped))

        for pattern_name, regex, severity in ALL_SECRET_PATTERNS:
            m = regex.search(line)
            if not m:
                continue
            if is_comment or in_markdown_code_block or is_placeholder:
                continue
            adjusted_severity = severity
            if is_test:
                sev_w = config.SEVERITY.get(severity, 1)
                adjusted_severity = "MEDIUM" if sev_w >= config.SEVERITY["HIGH"] else "LOW"
            if is_env_ex and not is_placeholder:
                adjusted_severity = "MEDIUM"
            findings.append({"type": "secret", "pattern": pattern_name, "severity": adjusted_severity,
                              "file": file_str, "line": line_num,
                              "snippet": _snippet(line, m.start()), "category": file_category})

        for token_match in re.finditer(r"""['\"][^\'\"]{16,}['\"]""", line):
            if len(findings) >= max_findings:
                break
            token = token_match.group(0)[1:-1]
            ent = shannon_entropy(token)
            if ent > 4.5 and not is_comment and not in_markdown_code_block and not is_placeholder:
                already = any(f["file"] == file_str and f["line"] == line_num for f in findings)
                if not already:
                    sev = "HIGH" if ent > 5.0 else "MEDIUM"
                    if is_test:
                        sev = "LOW"
                    findings.append({"type": "secret", "pattern": "high_entropy_string",
                                     "severity": sev, "file": file_str, "line": line_num,
                                     "snippet": _redact(token), "category": file_category,
                                     "entropy": round(ent, 2)})

    return findings


SCORE_DEDUCTIONS = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}


def aggregate_by_severity(findings):
    counts = {sev: 0 for sev in config.SEVERITY}
    for f in findings:
        sev = f.get("severity", "INFO")
        if sev in counts:
            counts[sev] += 1
    return counts


def aggregate_by_pattern(findings):
    counts: dict[str, int] = {}
    for f in findings:
        p = f.get("pattern", "unknown")
        counts[p] = counts.get(p, 0) + 1
    return counts


def aggregate_by_category(findings):
    counts: dict[str, int] = {}
    for f in findings:
        c = f.get("category", "other")
        counts[c] = counts.get(c, 0) + 1
    return counts


def compute_score(findings) -> int:
    score = 100
    for f in findings:
        score -= SCORE_DEDUCTIONS.get(f["severity"], 0)
    return max(0, score)


def build_json_report(target, total_files, findings, severity_counts, pattern_counts,
                      category_counts, score, verdict, elapsed) -> dict:
    return {"scan": "secrets_scanner", "target": target, "timestamp": config.get_timestamp(),
            "duration_seconds": round(elapsed, 3), "total_files_scanned": total_files,
            "total_findings": len(findings), "severity_counts": severity_counts,
            "pattern_counts": pattern_counts, "category_counts": category_counts,
            "score": score, "verdict": {"label": verdict["label"],
            "description": verdict["description"], "emoji": verdict["emoji"]},
            "findings": findings}


def run_scan(target_path: str, output_format: str = "text",
             verbose: bool = False, include_low: bool = False) -> dict:
    if verbose:
        logger.setLevel("DEBUG")
    config.ensure_directories()
    target = Path(target_path).resolve()
    if not target.exists() or not target.is_dir():
        logger.error("Invalid target: %s", target)
        sys.exit(1)
    logger.info("Starting deep secrets scan of %s", target)
    start_time = time.time()
    files = collect_files(target)
    all_findings: list[dict] = []
    max_report = config.LIMITS["max_report_findings"]
    for fpath in files:
        if len(all_findings) >= max_report:
            break
        remaining = max_report - len(all_findings)
        all_findings.extend(scan_file(fpath, verbose=verbose)[:remaining])
    elapsed = time.time() - start_time
    severity_counts = aggregate_by_severity(all_findings)
    pattern_counts = aggregate_by_pattern(all_findings)
    category_counts = aggregate_by_category(all_findings)
    score = compute_score(all_findings)
    verdict = config.get_verdict(score)
    config.log_audit_event("secrets_scan", str(target),
                           f"score={score}, findings={len(all_findings)}, verdict={verdict['label']}",
                           {"total_files": len(files), "severity_counts": severity_counts,
                            "duration_seconds": round(elapsed, 3)})
    report = build_json_report(str(target), len(files), all_findings, severity_counts,
                               pattern_counts, category_counts, score, verdict, elapsed)
    if output_format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"007 Secrets Scanner\nTarget: {str(target)}\nFindings: {len(all_findings)}\nScore: {score}/100\nVerdict: {verdict['emoji']} {verdict['label']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="007 Secrets Scanner")
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--include-low", action="store_true", default=False)
    args = parser.parse_args()
    run_scan(target_path=args.target, output_format=args.output,
             verbose=args.verbose, include_low=args.include_low)

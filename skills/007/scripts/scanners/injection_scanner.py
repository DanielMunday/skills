"""007 Injection Scanner -- Specialized scanner for injection vulnerabilities.

Detects code injection, SQL injection, command injection, prompt injection,
XSS, SSRF, and path traversal patterns across Python, JavaScript/Node.js,
and shell codebases. Performs context-aware analysis to reduce false positives.

Usage:
    python injection_scanner.py --target /path/to/project
    python injection_scanner.py --target /path/to/project --output json
    python injection_scanner.py --target /path/to/project --include-low
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = config.setup_logging("007-injection-scanner")

_USER_INPUT_MARKERS = re.compile(
    r"(?:request\.(?:args|form|json|data|files|values|headers|cookies)|"
    r"request\.GET|request\.POST|request\.query_params|"
    r"sys\.argv|input\s*\(|os\.environ|"
    r"flask\.request|django\.http|"
    r"req\.(?:body|params|query|headers|cookies)|"
    r"process\.argv|window\.location|document\.location|"
    r"URLSearchParams|event\.(?:target|data))",
    re.IGNORECASE,
)

_COMMENT_LINE_RE = re.compile(r"^\s*(?:#|//|/\*|\*|;)", re.IGNORECASE)
_MARKDOWN_CODE_FENCE = re.compile(r"^\s*```")
_TEST_FILE_RE = re.compile(
    r"(?i)(?:^test_|_test\.py$|\.test\.[jt]sx?$|\.spec\.[jt]sx?$|__tests__|tests[/\\])"
)


def _is_comment_line(line: str) -> bool:
    return bool(_COMMENT_LINE_RE.match(line))


def _is_test_file(filepath: Path) -> bool:
    return bool(_TEST_FILE_RE.search(filepath.name)) or bool(_TEST_FILE_RE.search(str(filepath)))


def _lower_severity(severity: str) -> str:
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    idx = order.index(severity) if severity in order else 0
    return order[min(idx + 1, len(order) - 1)]


def _has_user_input(line: str) -> bool:
    return bool(_USER_INPUT_MARKERS.search(line))


def _has_variable_interpolation(line: str) -> bool:
    if re.search(r"(?<!\{)\{[^{}\s][^{}]*\}(?!\})", line):
        return True
    if ".format(" in line:
        return True
    if re.search(r"%[sdifr]", line) and "%" in line:
        return True
    return False


def _only_hardcoded_string(line: str) -> bool:
    if _has_variable_interpolation(line) or _has_user_input(line):
        return False
    paren = line.find("(")
    if paren == -1:
        return False
    inside = line[paren:]
    return bool(re.match(r"""\(\s*['\"]{1,3}[^'\"]*['\"]{1,3}\s*\)""", inside))


_INJECTION_DEFS: list[tuple[str, str, str, str, str]] = [
    # Code injection
    ("py_eval_any", r"\beval\s*\(", "CRITICAL", "code_injection",
     "eval() usage -- verify input is not user-controlled"),
    ("py_exec_any", r"\bexec\s*\(", "CRITICAL", "code_injection",
     "exec() usage -- verify input is not user-controlled"),
    ("js_eval_any", r"\beval\s*\(", "CRITICAL", "code_injection",
     "eval() in JavaScript -- verify input is not user-controlled"),
    ("js_function_constructor", r"\bnew\s+Function\s*\(", "CRITICAL", "code_injection",
     "Function() constructor -- equivalent to eval"),
    ("template_injection_fstring",
     r"(?:render|template|jinja|mako|render_template_string)\s*\(.*\bf['\"]",
     "CRITICAL", "code_injection", "f-string in template rendering context"),

    # Command injection
    ("subprocess_shell_true",
     r"\bsubprocess\.(?:call|run|Popen|check_output|check_call)\s*\([^)]*shell\s*=\s*True",
     "CRITICAL", "command_injection", "subprocess with shell=True"),
    ("os_system_var", r"\bos\.system\s*\(", "CRITICAL", "command_injection",
     "os.system() -- always uses a shell"),
    ("os_popen_var", r"\bos\.popen\s*\(", "HIGH", "command_injection", "os.popen()"),
    ("child_process_exec", r"\b(?:child_process\.exec|execSync)\s*\(", "CRITICAL",
     "command_injection", "child_process.exec() -- uses shell by default"),

    # SQL injection
    ("sql_fstring",
     r"(?i)\bf['\"](?:[^'\"]*?)(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|UNION)\b",
     "CRITICAL", "sql_injection", "f-string in SQL query"),
    ("sql_format_method",
     r"(?i)(?:['\"](?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^'\"]*['\"])\.format\s*\(",
     "CRITICAL", "sql_injection", ".format() in SQL query string"),
    ("sql_percent_format",
     r"(?i)(?:cursor\.execute|execute|executemany)\s*\(\s*['\"][^'\"]*(?:SELECT|INSERT|UPDATE|DELETE)\b[^'\"]*%[sd]",
     "CRITICAL", "sql_injection", "%-format in cursor.execute()"),
    ("sql_fstring_execute",
     r"(?i)(?:cursor\.execute|execute|executemany)\s*\(\s*f['\"]",
     "CRITICAL", "sql_injection", "f-string in execute() call"),

    # Prompt injection
    ("prompt_injection_fstring",
     r"(?i)(?:prompt|system_prompt|user_prompt|message|messages)\s*=\s*f['\"][^'\"]*\{(?:user|input|query|request|data)",
     "HIGH", "prompt_injection", "User input directly in LLM prompt via f-string"),
    ("prompt_injection_concat",
     r"(?i)(?:prompt|system_prompt|messages?)\s*(?:=|\+=)\s*[^=\n]*(?:user_input|user_message|request\.(?:body|data|form|json)|input\()",
     "HIGH", "prompt_injection", "User input concatenated into LLM prompt"),

    # XSS
    ("xss_innerhtml", r"\.innerHTML\s*=\s*(?!['\"])", "HIGH", "xss",
     "innerHTML assignment with variable (XSS risk)"),
    ("xss_dangerously_set", r"\bdangerouslySetInnerHTML\s*=\s*\{", "HIGH", "xss",
     "dangerouslySetInnerHTML in React"),
    ("xss_document_write", r"\bdocument\.write\s*\(", "MEDIUM", "xss",
     "document.write() usage"),

    # SSRF
    ("ssrf_requests",
     r"\brequests\.(?:get|post|put|patch|delete|head|options|request)\s*\([^)]*(?:\bvar\b|\bdata\b|\brequest\b|\burl\b|\bf['\"])",
     "HIGH", "ssrf", "requests with potentially user-controlled URL"),
    ("ssrf_fetch",
     r"\bfetch\s*\([^)]*(?:\bvar\b|\bdata\b|\breq\b|\burl\b|\$\{)",
     "HIGH", "ssrf", "fetch() with potentially user-controlled URL"),
    ("ssrf_no_allowlist", r"\brequests\.(?:get|post|put|patch|delete)\s*\(", "MEDIUM", "ssrf",
     "HTTP request without visible URL allowlist validation"),

    # Path traversal
    ("path_traversal_open",
     r"\bopen\s*\([^)]*(?:\brequest\b|\bparams?\b|\bquery\b|\bform\b|\buser\b|\bargv\b|\binput\s*\()",
     "HIGH", "path_traversal", "open() with user-controlled path"),
    ("path_traversal_join",
     r"\bos\.path\.join\s*\([^)]*(?:\brequest\b|\bparams?\b|\bquery\b|\bform\b|\buser\b|\bargv\b)",
     "HIGH", "path_traversal", "os.path.join with user input"),
    ("path_traversal_send_file",
     r"\bsend_file\s*\([^)]*(?:\brequest\b|\bparams?\b|\bquery\b|\bform\b|\buser\b)",
     "HIGH", "path_traversal", "send_file() with user-controlled path"),
]

INJECTION_PATTERNS: list[tuple[str, re.Pattern, str, str, str]] = []
for _name, _pat, _sev, _itype, _desc in _INJECTION_DEFS:
    try:
        INJECTION_PATTERNS.append((_name, re.compile(_pat), _sev, _itype, _desc))
    except re.error as exc:
        logger.warning("Failed to compile pattern %s: %s", _name, exc)

SCORE_DEDUCTIONS = {"CRITICAL": 12, "HIGH": 6, "MEDIUM": 3, "LOW": 1, "INFO": 0}


def _should_scan_file(filepath: Path) -> bool:
    name = filepath.name.lower()
    suffix = filepath.suffix.lower()
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


def _snippet(line: str, match_start: int, context: int = 80) -> str:
    start = max(0, match_start - context // 4)
    end = min(len(line), match_start + context)
    raw = line[start:end].strip()
    return raw[:context] + "..." if len(raw) > context else raw


def scan_file(filepath: Path, verbose: bool = False) -> list[dict]:
    findings: list[dict] = []
    max_findings = config.LIMITS["max_findings_per_file"]
    file_str = str(filepath)
    is_test = _is_test_file(filepath)

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
    in_markdown_block = False

    _CONTEXT_WINDOW = 5
    line_has_user_input = [False] * len(lines)
    for idx, ln in enumerate(lines):
        if _has_user_input(ln):
            lo = max(0, idx - _CONTEXT_WINDOW)
            hi = min(len(lines), idx + _CONTEXT_WINDOW + 1)
            for j in range(lo, hi):
                line_has_user_input[j] = True

    line_patterns: dict[int, set[str]] = {}

    for line_idx, line in enumerate(lines):
        if len(findings) >= max_findings:
            break
        line_num = line_idx + 1
        stripped = line.strip()
        if not stripped:
            continue
        if _MARKDOWN_CODE_FENCE.match(stripped):
            in_markdown_block = not in_markdown_block
            continue
        if _is_comment_line(stripped) or in_markdown_block:
            continue

        for pat_name, regex, base_severity, injection_type, description in INJECTION_PATTERNS:
            m = regex.search(line)
            if not m:
                continue

            if line_num not in line_patterns:
                line_patterns[line_num] = set()

            group_key = injection_type + ":" + pat_name.rsplit("_", 1)[0]
            if group_key in line_patterns.get(line_num, set()):
                continue
            line_patterns[line_num].add(group_key)

            adjusted_severity = base_severity
            if _only_hardcoded_string(line):
                adjusted_severity = "INFO"
            elif not line_has_user_input[line_idx] and not _has_user_input(line):
                if not _has_variable_interpolation(line):
                    adjusted_severity = _lower_severity(base_severity)
                    if pat_name.endswith("_any"):
                        adjusted_severity = _lower_severity(adjusted_severity)

            if is_test:
                adjusted_severity = _lower_severity(adjusted_severity)

            findings.append({
                "type": "injection", "injection_type": injection_type,
                "pattern": pat_name, "severity": adjusted_severity,
                "file": file_str, "line": line_num,
                "snippet": _snippet(line, m.start()), "description": description,
                "has_user_input_nearby": line_has_user_input[line_idx],
            })

    return findings


def aggregate_by_severity(findings):
    counts = {sev: 0 for sev in config.SEVERITY}
    for f in findings:
        sev = f.get("severity", "INFO")
        if sev in counts:
            counts[sev] += 1
    return counts


def aggregate_by_injection_type(findings):
    counts: dict[str, int] = {}
    for f in findings:
        itype = f.get("injection_type", "unknown")
        counts[itype] = counts.get(itype, 0) + 1
    return counts


def compute_score(findings) -> int:
    score = 100
    for f in findings:
        score -= SCORE_DEDUCTIONS.get(f["severity"], 0)
    return max(0, score)


def build_json_report(target, total_files, findings, severity_counts,
                      type_counts, score, verdict, elapsed) -> dict:
    return {"scan": "injection_scanner", "target": target, "timestamp": config.get_timestamp(),
            "duration_seconds": round(elapsed, 3), "total_files_scanned": total_files,
            "total_findings": len(findings), "severity_counts": severity_counts,
            "injection_type_counts": type_counts, "score": score,
            "verdict": {"label": verdict["label"], "description": verdict["description"],
                        "emoji": verdict["emoji"]}, "findings": findings}


def run_scan(target_path: str, output_format: str = "text",
             verbose: bool = False, include_low: bool = False) -> dict:
    if verbose:
        logger.setLevel("DEBUG")
    config.ensure_directories()
    target = Path(target_path).resolve()
    if not target.exists() or not target.is_dir():
        logger.error("Invalid target: %s", target)
        sys.exit(1)
    logger.info("Starting injection scan of %s", target)
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
    type_counts = aggregate_by_injection_type(all_findings)
    score = compute_score(all_findings)
    verdict = config.get_verdict(score)
    config.log_audit_event("injection_scan", str(target),
                           f"score={score}, findings={len(all_findings)}, verdict={verdict['label']}",
                           {"total_files": len(files), "severity_counts": severity_counts,
                            "injection_type_counts": type_counts,
                            "duration_seconds": round(elapsed, 3)})
    report = build_json_report(str(target), len(files), all_findings,
                               severity_counts, type_counts, score, verdict, elapsed)
    if output_format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"007 Injection Scanner\nTarget: {str(target)}\nFiles: {len(files)}\n"
              f"Findings: {len(all_findings)}\nScore: {score}/100\n"
              f"Verdict: {verdict['emoji']} {verdict['label']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="007 Injection Scanner")
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--include-low", action="store_true", default=False)
    args = parser.parse_args()
    run_scan(target_path=args.target, output_format=args.output,
             verbose=args.verbose, include_low=args.include_low)

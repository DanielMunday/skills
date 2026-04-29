"""007 Dependency Scanner -- Supply chain and dependency security analyzer.

Analyzes dependency files (requirements.txt, package.json, Dockerfiles, etc.)
for version pinning, known risky patterns, and supply chain best practices.

Usage:
    python dependency_scanner.py --target /path/to/project
    python dependency_scanner.py --target /path/to/project --output json
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

logger = config.setup_logging("007-dependency-scanner")

PYTHON_DEP_FILES = {
    "requirements.txt", "requirements-dev.txt", "requirements_dev.txt",
    "requirements-test.txt", "requirements_test.txt",
    "setup.py", "setup.cfg", "pyproject.toml", "Pipfile", "Pipfile.lock",
}
NODE_DEP_FILES = {"package.json", "package-lock.json", "yarn.lock"}
DOCKER_PREFIXES = ("Dockerfile", "dockerfile", "docker-compose")
ALL_DEP_FILES = PYTHON_DEP_FILES | NODE_DEP_FILES
_REQUIREMENTS_RE = re.compile(r"^requirements[-_]?\w*\.txt$", re.IGNORECASE)

_PY_COMMENT_RE = re.compile(r"^\s*#")
_PY_OPTION_RE = re.compile(r"^\s*-")
_PY_BLANK_RE = re.compile(r"^\s*$")
_PY_PINNED_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9._-]*)(?:\[.*?\])?\s*==\s*[\d]")
_PY_PACKAGE_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9._-]*)")
_PY_HASH_RE = re.compile(r"--hash[=:]")

_RISKY_PYTHON_PACKAGES = {
    "pyyaml": "yaml.load() without SafeLoader enables arbitrary code execution",
    "pickle": "allows arbitrary code execution during deserialization",
    "shelve": "uses pickle internally, same risks",
    "marshal": "can execute arbitrary code during deserialization",
    "dill": "extends pickle with same code execution risks",
    "jsonpickle": "can deserialize to arbitrary objects",
}

_NODE_EXACT_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_NODE_LOOSE_INDICATORS = re.compile(r"^[\^~*><=]|latest|next|canary", re.IGNORECASE)
_NODE_RISKY_SCRIPTS = re.compile(
    r"(?:curl|wget|fetch|http|eval|exec|child_process|\.sh\b|powershell)", re.IGNORECASE
)

_DOCKER_FROM_RE = re.compile(r"^\s*FROM\s+(\S+)", re.IGNORECASE)
_DOCKER_USER_RE = re.compile(r"^\s*USER\s+", re.IGNORECASE)
_DOCKER_COPY_SENSITIVE_RE = re.compile(
    r"^\s*(?:COPY|ADD)\s+.*?(?:\.env|\.key|\.pem|\.p12|id_rsa|\.secret)", re.IGNORECASE
)
_DOCKER_CURL_PIPE_RE = re.compile(
    r"(?:curl|wget)\s+[^|]*\|\s*(?:bash|sh|zsh|python|perl|ruby|node)", re.IGNORECASE
)
_DOCKER_TRUSTED_BASES = {
    "python", "node", "golang", "ruby", "alpine", "ubuntu", "debian",
    "nginx", "redis", "postgres", "mysql", "mongo",
    "mcr.microsoft.com/", "gcr.io/", "ghcr.io/",
}

SCORE_DEDUCTIONS = {"CRITICAL": 15, "HIGH": 7, "MEDIUM": 3, "LOW": 1, "INFO": 0}


def _make_finding(file, line, severity, description, recommendation, pattern="dependency") -> dict:
    return {"type": "supply_chain", "pattern": pattern, "severity": severity,
            "file": file, "line": line, "description": description,
            "recommendation": recommendation}


def analyze_requirements_txt(filepath: Path, verbose: bool = False) -> dict:
    findings: list[dict] = []
    file_str = str(filepath)
    deps_total = deps_pinned = deps_hashed = 0
    deps_unpinned: list[str] = []

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"deps_total": 0, "deps_pinned": 0, "deps_hashed": 0,
                "deps_unpinned": [], "findings": findings}

    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if _PY_COMMENT_RE.match(line) or _PY_OPTION_RE.match(line) or _PY_BLANK_RE.match(line):
            continue
        line_no_comment = re.sub(r"\s+#.*$", "", line)
        pkg_match = _PY_PACKAGE_RE.match(line_no_comment)
        if not pkg_match:
            continue
        pkg_name = pkg_match.group(1).lower()
        deps_total += 1
        is_pinned = bool(_PY_PINNED_RE.match(line_no_comment))
        has_hash = bool(_PY_HASH_RE.search(raw_line))
        if is_pinned:
            deps_pinned += 1
        else:
            deps_unpinned.append(pkg_name)
            findings.append(_make_finding(file_str, line_num, "HIGH",
                f"Dependency '{pkg_name}' is not pinned to an exact version",
                f"Pin to exact version: {pkg_name}==<version>", "unpinned_dependency"))
        if has_hash:
            deps_hashed += 1
        if pkg_name in _RISKY_PYTHON_PACKAGES:
            findings.append(_make_finding(file_str, line_num, "MEDIUM",
                f"Risky package '{pkg_name}': {_RISKY_PYTHON_PACKAGES[pkg_name]}",
                f"Review usage of '{pkg_name}' and ensure safe configuration", "risky_package"))

    if deps_total > 0 and deps_hashed == 0:
        findings.append(_make_finding(file_str, 0, "LOW",
            "No hash verification used for any dependency",
            "Consider using --hash for supply chain integrity", "no_hash_verification"))

    return {"deps_total": deps_total, "deps_pinned": deps_pinned, "deps_hashed": deps_hashed,
            "deps_unpinned": deps_unpinned, "findings": findings}


def analyze_package_json(filepath: Path, verbose: bool = False) -> dict:
    findings: list[dict] = []
    file_str = str(filepath)
    deps_total = deps_pinned = dev_deps_total = 0
    deps_unpinned: list[str] = []

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(_make_finding(file_str, 0, "MEDIUM",
            f"Could not parse package.json: {exc}", "Fix JSON syntax errors", "invalid_manifest"))
        return {"deps_total": 0, "deps_pinned": 0, "deps_unpinned": [],
                "dev_deps_total": 0, "findings": findings}

    def _find_line(key: str) -> int:
        for i, ln in enumerate(text.splitlines(), 1):
            if f'"{key}"' in ln:
                return i
        return 0

    for section_name in ("dependencies", "devDependencies"):
        deps = data.get(section_name, {})
        if not isinstance(deps, dict):
            continue
        is_dev = section_name == "devDependencies"
        for pkg_name, version_spec in deps.items():
            if not isinstance(version_spec, str):
                continue
            if is_dev:
                dev_deps_total += 1
            deps_total += 1
            line_num = _find_line(pkg_name)
            if _NODE_EXACT_VERSION_RE.match(version_spec):
                deps_pinned += 1
            elif _NODE_LOOSE_INDICATORS.match(version_spec):
                deps_unpinned.append(pkg_name)
                severity = "MEDIUM" if is_dev else "HIGH"
                findings.append(_make_finding(file_str, line_num, severity,
                    f"{'Dev d' if is_dev else 'D'}ependency '{pkg_name}' uses loose version '{version_spec}'",
                    f"Pin to exact version: \"{pkg_name}\": \"{version_spec.lstrip('^~')}\"",
                    "unpinned_dependency"))

    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        for script_name, script_cmd in scripts.items():
            if not isinstance(script_cmd, str):
                continue
            if script_name in ("postinstall", "preinstall", "install") and _NODE_RISKY_SCRIPTS.search(script_cmd):
                findings.append(_make_finding(file_str, _find_line(script_name), "CRITICAL",
                    f"Risky '{script_name}' lifecycle script: may execute arbitrary code",
                    f"Audit the '{script_name}' script: {script_cmd[:120]}", "risky_lifecycle_script"))

    return {"deps_total": deps_total, "deps_pinned": deps_pinned, "deps_unpinned": deps_unpinned,
            "dev_deps_total": dev_deps_total, "findings": findings}


def analyze_dockerfile(filepath: Path, verbose: bool = False) -> dict:
    findings: list[dict] = []
    file_str = str(filepath)
    base_images: list[str] = []
    has_user_directive = False

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"base_images": [], "findings": findings}

    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        from_match = _DOCKER_FROM_RE.match(line)
        if from_match:
            image = from_match.group(1)
            base_images.append(image)
            image_core = image.lower().split()[0]
            if image_core != "scratch":
                if ":" not in image_core or image_core.endswith(":latest"):
                    findings.append(_make_finding(file_str, line_num, "HIGH",
                        f"Base image '{image_core}' uses ':latest' or no version tag",
                        "Pin base image to a specific version tag (e.g., python:3.12-slim)",
                        "unpinned_base_image"))
                is_trusted = any(image_core.startswith(p) for p in _DOCKER_TRUSTED_BASES)
                if not is_trusted:
                    findings.append(_make_finding(file_str, line_num, "MEDIUM",
                        f"Base image '{image_core}' is from an unverified source",
                        "Use official images from Docker Hub or trusted registries",
                        "untrusted_base_image"))

        if _DOCKER_USER_RE.match(line):
            has_user_directive = True
        if _DOCKER_COPY_SENSITIVE_RE.match(line):
            findings.append(_make_finding(file_str, line_num, "CRITICAL",
                "COPY/ADD of potentially sensitive file (keys, .env, certificates)",
                "Use Docker secrets or build args instead", "sensitive_file_in_image"))
        if _DOCKER_CURL_PIPE_RE.search(line):
            findings.append(_make_finding(file_str, line_num, "CRITICAL",
                "Pipe-to-shell pattern detected (curl|bash). Remote code execution risk",
                "Download scripts first, verify checksum, then execute", "curl_pipe_bash"))

    if base_images and not has_user_directive:
        findings.append(_make_finding(file_str, 0, "MEDIUM",
            "Dockerfile has no USER directive -- container runs as root by default",
            "Add 'USER nonroot' before the final CMD/ENTRYPOINT", "running_as_root"))

    return {"base_images": base_images, "findings": findings}


def discover_dependency_files(target: Path) -> list[Path]:
    found: list[Path] = []
    for root, dirs, filenames in os.walk(target):
        dirs[:] = [d for d in dirs if d not in config.SKIP_DIRECTORIES]
        for fname in filenames:
            fpath = Path(root) / fname
            fname_lower = fname.lower()
            if fname in ALL_DEP_FILES:
                found.append(fpath)
                continue
            if _REQUIREMENTS_RE.match(fname):
                found.append(fpath)
                continue
            if any(fname_lower.startswith(p.lower()) for p in DOCKER_PREFIXES):
                found.append(fpath)
    return found


def scan_dependency_file(filepath: Path, verbose: bool = False) -> dict:
    fname = filepath.name.lower()
    if _REQUIREMENTS_RE.match(filepath.name):
        return analyze_requirements_txt(filepath, verbose=verbose)
    if fname == "pyproject.toml":
        return {"deps_total": 0, "deps_pinned": 0, "deps_unpinned": [], "findings": []}
    if fname == "pipfile":
        return {"deps_total": 0, "deps_pinned": 0, "deps_unpinned": [], "findings": []}
    if fname in ("pipfile.lock", "setup.py", "setup.cfg"):
        return {"deps_total": 0, "deps_pinned": 0, "deps_unpinned": [], "findings": []}
    if fname == "package.json":
        return analyze_package_json(filepath, verbose=verbose)
    if fname in ("package-lock.json", "yarn.lock"):
        return {"deps_total": 0, "deps_pinned": 0, "deps_unpinned": [], "findings": []}
    if fname.startswith("dockerfile"):
        return analyze_dockerfile(filepath, verbose=verbose)
    if fname.startswith("docker-compose"):
        return {"services": [], "findings": []}
    return {"findings": []}


def compute_supply_chain_score(findings: list[dict], pinning_pct: float) -> int:
    pinning_score = pinning_pct * 0.5
    finding_base = 50.0
    for f in findings:
        finding_base -= SCORE_DEDUCTIONS.get(f.get("severity", "INFO"), 0)
    return max(0, min(100, round(pinning_score + max(0.0, finding_base))))


def aggregate_by_severity(findings):
    counts = {sev: 0 for sev in config.SEVERITY}
    for f in findings:
        sev = f.get("severity", "INFO")
        if sev in counts:
            counts[sev] += 1
    return counts


def build_json_report(target, dep_files, total_deps, total_pinned, pinning_pct,
                      findings, severity_counts, score, verdict, elapsed) -> dict:
    return {"scan": "dependency_scanner", "target": target, "timestamp": config.get_timestamp(),
            "duration_seconds": round(elapsed, 3), "dependency_files": dep_files,
            "total_dependencies": total_deps, "total_pinned": total_pinned,
            "pinning_coverage_pct": round(pinning_pct, 1), "total_findings": len(findings),
            "severity_counts": severity_counts, "score": score,
            "verdict": {"label": verdict["label"], "description": verdict["description"],
                        "emoji": verdict["emoji"]}, "findings": findings}


def run_scan(target_path: str, output_format: str = "text", verbose: bool = False) -> dict:
    if verbose:
        logger.setLevel("DEBUG")
    config.ensure_directories()
    target = Path(target_path).resolve()
    if not target.exists() or not target.is_dir():
        logger.error("Invalid target: %s", target)
        sys.exit(1)
    logger.info("Starting dependency scan of %s", target)
    start_time = time.time()
    dep_file_paths = discover_dependency_files(target)
    dep_files = [str(p) for p in dep_file_paths]
    all_findings: list[dict] = []
    total_deps = total_pinned = 0
    for fpath in dep_file_paths:
        result = scan_dependency_file(fpath, verbose=verbose)
        all_findings.extend(result.get("findings", []))
        total_deps += result.get("deps_total", 0)
        total_pinned += result.get("deps_pinned", 0)
    max_report = config.LIMITS["max_report_findings"]
    if len(all_findings) > max_report:
        all_findings = all_findings[:max_report]
    elapsed = time.time() - start_time
    pinning_pct = (total_pinned / total_deps * 100.0) if total_deps > 0 else 100.0
    severity_counts = aggregate_by_severity(all_findings)
    score = compute_supply_chain_score(all_findings, pinning_pct)
    verdict = config.get_verdict(score)
    config.log_audit_event("dependency_scan", str(target),
                           f"score={score}, findings={len(all_findings)}, verdict={verdict['label']}",
                           {"dependency_files": len(dep_files), "total_dependencies": total_deps,
                            "pinning_coverage_pct": round(pinning_pct, 1),
                            "duration_seconds": round(elapsed, 3)})
    report = build_json_report(str(target), dep_files, total_deps, total_pinned,
                               pinning_pct, all_findings, severity_counts, score, verdict, elapsed)
    if output_format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"007 Dependency Scanner\nTarget: {str(target)}\nDep files: {len(dep_files)}\n"
              f"Total deps: {total_deps} (pinned: {total_pinned}, {pinning_pct:.1f}%)\n"
              f"Findings: {len(all_findings)}\nScore: {score}/100\n"
              f"Verdict: {verdict['emoji']} {verdict['label']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="007 Dependency Scanner")
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()
    run_scan(target_path=args.target, output_format=args.output, verbose=args.verbose)

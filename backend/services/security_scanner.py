"""
security_scanner.py
────────────────────
Feature 3: Security Vulnerability Detection Engine.

Analyzes source code for security vulnerabilities without executing target code:
  1. Bandit static security scanner for Python files (subprocess execution with JSON output).
  2. Language-agnostic regex/pattern scanner across (.py, .js, .ts, .env, .json, .java, etc.):
     - Hardcoded credentials, secrets, tokens, API keys (with secret masking)
     - Potential SQL Injection (string concatenation / f-strings in queries)
     - Potential Command Injection (`os.system`, `subprocess(..., shell=True)`, `eval`, `exec`)
     - Weak hashing / crypto (`md5`, `sha1`, insecure random)
     - Dangerous production configurations (`DEBUG = True`)

Security:
  - Never executes, imports, or modifies analyzed code.
  - Normalizes every finding into `RawFinding` with category="Security".
  - Always masks discovered secret strings so raw passwords/keys are never leaked.
"""

import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from models.finding import ConfidenceLevel, RawFinding

logger = logging.getLogger(__name__)

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", ".vite", "build", ".idea", ".vscode"
}

SECURITY_SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".env", ".json", ".java", ".c", ".cpp", ".html", ".yml", ".yaml"
}


# ── Secret Masking Utility ───────────────────────────────────────────────────

def mask_secret(value: str) -> str:
    """
    Masks sensitive values (e.g., API keys, passwords, tokens).
    Retains first 2 and last 2 characters if length > 6, otherwise replaces entirely.
    """
    clean_val = value.strip("\"' \t\r\n")
    if len(clean_val) <= 6:
        return "******"
    return f"{clean_val[:2]}****{clean_val[-2:]}"


def sanitize_snippet(snippet: str, secret_match: str) -> str:
    """
    Replaces any sensitive secret occurrence in the code snippet with its masked form.
    """
    if not secret_match or not snippet:
        return snippet
    masked = mask_secret(secret_match)
    return snippet.replace(secret_match, masked)


# ── 1. Static Security Patterns ──────────────────────────────────────────────

# Pattern tuple: (regex_pattern, rule_id, description_template, confidence, is_secret_detector)
SECURITY_PATTERNS = [
    # --- Hardcoded Secrets & Keys ---
    (
        r"""(?i)(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token|private[_-]?key|password|passwd|pwd)\s*[:=]\s*["']([a-zA-Z0-9_\-\.\/+=]{8,})["']""",
        "SEC-HARDCODED-SECRET",
        "Potential hardcoded credential or secret key detected.",
        "Detected",
        True
    ),
    (
        r"""(?i)(?:AWS|AMAZON)_(?:ACCESS_KEY_ID|SECRET_ACCESS_KEY)\s*[:=]\s*["']([A-Za-z0-9/+=]{16,})["']""",
        "SEC-AWS-CREDENTIAL",
        "Hardcoded AWS credential identifier or secret key detected.",
        "Detected",
        True
    ),
    (
        r"""ghp_[a-zA-Z0-9]{36}""",
        "SEC-GITHUB-TOKEN",
        "Hardcoded GitHub Personal Access Token detected.",
        "Detected",
        True
    ),
    # --- SQL Injection Patterns ---
    (
        r"""(?i)\b(?:execute|cursor\.execute|rawQuery)\s*\(\s*(?:f["'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{|["'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?["']\s*\+)""",
        "SEC-SQL-INJECTION",
        "Potential SQL injection: Raw SQL query constructed with dynamic string concatenation or f-string.",
        "Potential",
        False
    ),
    (
        r"""(?i)\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b.*?['"]\s*\+\s*[a-zA-Z0-9_]+""",
        "SEC-SQLI-CONCAT",
        "Potential SQL injection via raw query string concatenation.",
        "Potential",
        False
    ),
    # --- Command Injection / Dangerous Execution ---
    (
        r"""\bos\.system\s*\(""",
        "SEC-OS-SYSTEM",
        "Use of 'os.system()' can lead to command injection vulnerabilities. Prefer subprocess.run with shell=False.",
        "Potential",
        False
    ),
    (
        r"""\bsubprocess\.(?:Popen|run|call|check_output|check_call)\s*\(.*?\bshell\s*=\s*True""",
        "SEC-SUBPROCESS-SHELL",
        "Subprocess call with 'shell=True' allows command injection if untrusted input is included.",
        "Detected",
        False
    ),
    (
        r"""\b(?:eval|exec)\s*\(""",
        "SEC-DYNAMIC-EXEC",
        "Dynamic code execution via 'eval()' or 'exec()' allows arbitrary code execution if untrusted input is passed.",
        "Detected",
        False
    ),
    # --- Weak Cryptography & Hashing ---
    (
        r"""(?i)\b(?:hashlib\.md5|hashlib\.sha1|crypto\.createHash\s*\(\s*['"](?:md5|sha1)['"]\))\s*\(""",
        "SEC-WEAK-HASH",
        "Weak hashing algorithm (MD5/SHA1) detected. Insecure against collision attacks; use SHA-256 or bcrypt/argon2 for passwords.",
        "Detected",
        False
    ),
    (
        r"""(?i)\b(?:DES|RC4|Blowfish)\b""",
        "SEC-WEAK-CIPHER",
        "Deprecated or weak encryption cipher detected (DES/RC4/Blowfish). Use AES-GCM or ChaCha20-Poly1305.",
        "Potential",
        False
    ),
    # --- Debug / Production Misconfiguration ---
    (
        r"""(?i)^\s*DEBUG\s*=\s*True\b""",
        "SEC-DEBUG-ENABLED",
        "Debug mode explicitly enabled ('DEBUG = True'). Exposes detailed stack traces and secrets in production.",
        "Potential",
        False
    ),
]


def scan_file_for_patterns(content: str, relative_path: str) -> List[RawFinding]:
    """
    Applies security regex patterns against source content.
    Automatically masks secret values to prevent credential leakage.
    """
    findings: List[RawFinding] = []
    lines = content.splitlines()

    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.strip()

        # Skip comment lines
        if stripped.startswith(("//", "#", "/*", "*")):
            # Still check .env files or potential secrets in comments
            if not relative_path.endswith(".env"):
                continue

        for pattern, rule_id, message, confidence, is_secret in SECURITY_PATTERNS:
            match = re.search(pattern, line)
            if match:
                snippet = stripped
                col = match.start() + 1

                # If this pattern captures a secret group, mask it
                if is_secret and match.groups():
                    raw_secret = match.group(1)
                    snippet = sanitize_snippet(stripped, raw_secret)
                    message_extra = f" Secret value masked: {mask_secret(raw_secret)}"
                    full_msg = f"{message}{message_extra}"
                else:
                    full_msg = message

                findings.append(RawFinding(
                    rule_id=rule_id,
                    tool="pattern-security",
                    category="Security",
                    file_path=relative_path,
                    line_number=line_num,
                    column_number=col,
                    raw_message=full_msg,
                    confidence=confidence,  # type: ignore
                    code_snippet=snippet,
                ))

    return findings


# ── 2. Bandit Static Security Scanner for Python ─────────────────────────────

def _map_bandit_confidence(issue_confidence: str) -> ConfidenceLevel:
    """
    Maps Bandit's issue confidence (HIGH/MEDIUM/LOW) to our normalized confidence.
    """
    if issue_confidence.upper() == "HIGH":
        return "Detected"
    return "Potential"


def run_bandit_on_project(project_dir: Path) -> List[RawFinding]:
    """
    Runs bandit CLI against python files in project_dir with JSON output format.
    Never executes target code.
    """
    findings: List[RawFinding] = []
    project_root = project_dir.resolve()

    # Locate bandit binary
    venv_bandit = project_root.parent / "venv" / "Scripts" / "bandit.exe"
    if not venv_bandit.exists():
        venv_bandit = Path(sys.prefix) / "Scripts" / "bandit.exe"
    bandit_cmd = str(venv_bandit) if venv_bandit.exists() else shutil.which("bandit")

    if not bandit_cmd:
        logger.warning("Bandit executable not found. Skipping Bandit analysis.")
        return findings

    try:
        proc = subprocess.run(
            [
                bandit_cmd,
                "-r",
                str(project_root),
                "-f", "json",
                "-q",
                "--exclude", "*/venv/*,*/.venv/*,*/node_modules/*,*/tests/*",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
            check=False,
        )

        output_str = proc.stdout.strip()
        if output_str:
            data = json.loads(output_str)
            results = data.get("results", [])
            for res in results:
                file_abs = Path(res.get("filename", ""))
                try:
                    rel_file = file_abs.relative_to(project_root).as_posix()
                except ValueError:
                    rel_file = file_abs.name

                test_id = res.get("test_id", "B000")
                test_name = res.get("test_name", "bandit_issue")
                issue_text = res.get("issue_text", "")
                confidence = _map_bandit_confidence(res.get("issue_confidence", "MEDIUM"))
                line_no = res.get("line_number", 1)

                code_snippet = res.get("code")
                if code_snippet:
                    # Take the first line of the snippet
                    code_snippet = code_snippet.strip().splitlines()[0]

                findings.append(RawFinding(
                    rule_id=f"BANDIT-{test_id}",
                    tool="bandit",
                    category="Security",
                    file_path=rel_file,
                    line_number=line_no,
                    column_number=None,
                    raw_message=f"[{test_name}] {issue_text}",
                    confidence=confidence,
                    code_snippet=code_snippet,
                ))
    except Exception as exc:
        logger.error(f"Error running Bandit security scan: {exc}")

    return findings


# ── 3. Unified Security Scanner Entrypoint ───────────────────────────────────

def scan_security_in_project(project_dir: Path) -> List[RawFinding]:
    """
    Main entrypoint for Feature 3:
    1. Runs Bandit on Python files.
    2. Runs Language-Agnostic Regex Security patterns across all supported files.
    3. Deduplicates and sorts findings by file and line number.
    """
    all_findings: List[RawFinding] = []
    project_root = project_dir.resolve()

    # 1. Custom Pattern Scanner across files
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in SKIP_DIRS for part in path.parts):
            continue

        ext = path.suffix.lower()
        if ext in SECURITY_SUPPORTED_EXTENSIONS or path.name.startswith(".env"):
            try:
                rel_path = path.relative_to(project_root).as_posix()
            except ValueError:
                rel_path = path.name

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                findings = scan_file_for_patterns(content, rel_path)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Failed scanning security patterns in {rel_path}: {e}")

    # 2. Bandit scan on Python files
    bandit_findings = run_bandit_on_project(project_root)
    all_findings.extend(bandit_findings)

    # 3. Deduplication on (file_path, line_number, rule_id)
    seen = set()
    deduped: List[RawFinding] = []
    for f in all_findings:
        key = (f.file_path, f.line_number, f.rule_id)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    deduped.sort(key=lambda x: (x.file_path, x.line_number))
    return deduped

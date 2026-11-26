"""
tests/test_security_scanner.py
──────────────────────────────
Unit tests verifying Feature 3 (Security Vulnerability Detection):
- Secret masking
- Hardcoded keys/credentials
- SQL Injection patterns
- Command injection / eval
- Weak crypto / hashing
- Debug mode in config
- Bandit subprocess scanner integration
"""

import tempfile
from pathlib import Path
from services.security_scanner import (
    mask_secret,
    scan_file_for_patterns,
    scan_security_in_project,
)


def test_secret_masking():
    short_secret = "12345"
    assert mask_secret(short_secret) == "******"

    long_secret = "sk_live_abcdef1234567890"
    masked = mask_secret(long_secret)
    assert masked.startswith("sk")
    assert masked.endswith("90")
    assert "abcdef" not in masked
    assert "****" in masked


def test_hardcoded_secrets_detection():
    sample = """
    API_KEY = "my_super_secret_api_key_12345"
    db_password = "supersecretpassword123"
    """
    findings = scan_file_for_patterns(sample, "config.py")
    rule_ids = {f.rule_id for f in findings}
    assert "SEC-HARDCODED-SECRET" in rule_ids
    # Verify masking in message or snippet
    for f in findings:
        assert "supersecretpassword123" not in f.raw_message
        if f.code_snippet:
            assert "supersecretpassword123" not in f.code_snippet
        assert f.category == "Security"


def test_sql_injection_detection():
    py_sample = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
    js_sample = 'const query = "SELECT * FROM items WHERE name = " + itemName;'

    py_findings = scan_file_for_patterns(py_sample, "db.py")
    js_findings = scan_file_for_patterns(js_sample, "service.js")

    assert any(f.rule_id == "SEC-SQL-INJECTION" for f in py_findings)
    assert any(f.rule_id == "SEC-SQLI-CONCAT" for f in js_findings)
    assert all(f.category == "Security" for f in py_findings + js_findings)


def test_command_injection_and_dynamic_exec():
    sample = """
    import os
    import subprocess
    os.system("ls " + path)
    subprocess.Popen(cmd, shell=True)
    eval(user_expression)
    """
    findings = scan_file_for_patterns(sample, "executor.py")
    rule_ids = {f.rule_id for f in findings}
    assert "SEC-OS-SYSTEM" in rule_ids
    assert "SEC-SUBPROCESS-SHELL" in rule_ids
    assert "SEC-DYNAMIC-EXEC" in rule_ids


def test_weak_cryptography_and_debug_mode():
    sample = """
    import hashlib
    token = hashlib.md5(b"test").hexdigest()
    DEBUG = True
    """
    findings = scan_file_for_patterns(sample, "settings.py")
    rule_ids = {f.rule_id for f in findings}
    assert "SEC-WEAK-HASH" in rule_ids
    assert "SEC-DEBUG-ENABLED" in rule_ids


def test_project_security_scan_with_bandit():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        vuln_py = tmp_path / "vulnerable.py"
        vuln_py.write_text(
            "import subprocess\n"
            "subprocess.call('echo hi', shell=True)\n"
            "eval('1+1')\n"
        )

        vuln_env = tmp_path / ".env"
        vuln_env.write_text("SECRET_KEY=\"very_secret_token_123456789\"\n")

        findings = scan_security_in_project(tmp_path)
        assert len(findings) > 0

        rule_ids = {f.rule_id for f in findings}
        # Bandit catches B602 (shell=True) or B307 (eval)
        assert any("BANDIT" in r for r in rule_ids)
        # Custom scanner catches the secret
        assert "SEC-HARDCODED-SECRET" in rule_ids

        # Ensure all are categorized as Security
        assert all(f.category == "Security" for f in findings)

"""
tests/test_explainer.py
───────────────────────
Unit tests for Feature 5 (Explainable Issue Analysis) and Feature 6 (Severity Classification):
- 9 required fields present in every ExplainedIssue
- Severity mappings (Critical, High, Medium, Low)
- Fallback templating for unmapped rule IDs
- Multi-line read-only code snippet context
- Full pipeline integration check
"""

import tempfile
from pathlib import Path
from models.finding import RawFinding
from services.explainer import (
    determine_severity,
    explain_all_findings,
    explain_finding,
    get_context_snippet,
    get_knowledge_base,
)


def test_knowledge_base_loading():
    kb = get_knowledge_base()
    assert len(kb) > 15
    assert "AST-SYNTAX-ERROR" in kb
    assert "SEC-SQL-INJECTION" in kb
    assert "QUAL-HIGH-COMPLEXITY" in kb


def test_nine_required_fields_presence():
    raw = RawFinding(
        rule_id="AST-SYNTAX-ERROR",
        tool="ast",
        category="Bug",
        file_path="app.py",
        line_number=10,
        column_number=5,
        raw_message="Syntax error at line 10",
        confidence="Detected",
        code_snippet="def foo(\n",
    )

    issue = explain_finding(raw, 1)

    # All 9 required fields
    assert issue.title == "Syntax Error"
    assert issue.category == "Bug"
    assert issue.file_name == "app.py"
    assert issue.line_number == 10
    assert issue.explanation != ""
    assert issue.why_it_matters != ""
    assert issue.possible_impact != ""
    assert issue.severity == "Critical"
    assert issue.recommendation != ""

    # Additional metadata
    assert issue.detection_type == "Detected"
    assert issue.code_snippet is not None


def test_severity_classification_rules():
    kb = get_knowledge_base()

    # Critical: SQL Injection, Syntax error, Hardcoded secret
    crit_sql = RawFinding(
        rule_id="SEC-SQL-INJECTION", tool="pattern-security", category="Security",
        file_path="db.py", line_number=5, raw_message="SQLi", confidence="Potential"
    )
    assert determine_severity(crit_sql, kb.get("SEC-SQL-INJECTION")) == "Critical"

    # High: Undefined variable
    high_undef = RawFinding(
        rule_id="RUFF-F821", tool="ruff", category="Bug",
        file_path="main.py", line_number=12, raw_message="Undefined name 'x'", confidence="Detected"
    )
    assert determine_severity(high_undef, kb.get("RUFF-F821")) == "High"

    # Medium: Mutable default
    med_default = RawFinding(
        rule_id="AST-MUTABLE-DEFAULT", tool="ast", category="Bug",
        file_path="utils.py", line_number=2, raw_message="Mutable default", confidence="Potential"
    )
    assert determine_severity(med_default, kb.get("AST-MUTABLE-DEFAULT")) == "Medium"

    # Low: Unused import, console log
    low_import = RawFinding(
        rule_id="RUFF-F401", tool="ruff", category="Code Quality",
        file_path="core.py", line_number=1, raw_message="Unused import", confidence="Detected"
    )
    assert determine_severity(low_import, kb.get("RUFF-F401")) == "Low"


def test_fallback_template_for_unmapped_rules():
    raw = RawFinding(
        rule_id="CUSTOM-UNKNOWN-CHECK-999",
        tool="custom",
        category="Security",
        file_path="handler.py",
        line_number=20,
        raw_message="Unusual configuration detected",
        confidence="Potential",
    )

    issue = explain_finding(raw, 5)
    assert "CUSTOM-UNKNOWN-CHECK-999" in issue.title
    assert issue.category == "Security"
    assert issue.severity in {"Critical", "High", "Medium", "Low"}
    assert "vulnerability" in issue.explanation.lower()
    assert issue.recommendation != ""


def test_context_snippet_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "sample.py"
        test_file.write_text(
            "line 1\n"
            "line 2\n"
            "line 3\n"
            "def broken_function():\n"
            "    line 5\n"
            "    line 6\n"
        )

        snippet = get_context_snippet(tmp_path, "sample.py", 4, context_lines=2)
        assert snippet is not None
        assert "▶    4 | def broken_function():" in snippet
        assert "2 | line 2" in snippet
        assert "6 |     line 6" in snippet

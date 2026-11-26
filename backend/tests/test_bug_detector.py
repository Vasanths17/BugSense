"""
tests/test_bug_detector.py
──────────────────────────
Unit tests verifying static bug detection without executing user code.
"""

import tempfile
from pathlib import Path
from services.bug_detector import (
    analyze_python_ast,
    analyze_js_patterns,
    detect_bugs_in_project,
)


def test_syntax_error_detection():
    buggy_code = "def broken(\n    print('missing paren'"
    findings = analyze_python_ast(buggy_code, "sample.py")
    assert any(f.rule_id == "AST-SYNTAX-ERROR" for f in findings)
    assert any(f.confidence == "Detected" for f in findings)


def test_mutable_default_argument():
    code = "def append_item(x, target=[]):\n    target.append(x)\n    return target\n"
    findings = analyze_python_ast(code, "utils.py")
    assert any(f.rule_id == "AST-MUTABLE-DEFAULT" for f in findings)
    assert any(f.confidence == "Potential" for f in findings)


def test_bare_except_detection():
    code = "try:\n    1 / 0\nexcept:\n    pass\n"
    findings = analyze_python_ast(code, "calc.py")
    assert any(f.rule_id == "AST-BARE-EXCEPT" for f in findings)
    assert any(f.confidence == "Potential" for f in findings)


def test_duplicate_dict_key():
    code = "data = {'name': 'alice', 'age': 30, 'name': 'bob'}\n"
    findings = analyze_python_ast(code, "config.py")
    assert any(f.rule_id == "AST-DUPLICATE-DICT-KEY" for f in findings)
    assert any(f.confidence == "Detected" for f in findings)


def test_self_assignment():
    code = "def reset():\n    x = 10\n    x = x\n    return x\n"
    findings = analyze_python_ast(code, "state.py")
    assert any(f.rule_id == "AST-SELF-ASSIGNMENT" for f in findings)
    assert any(f.confidence == "Detected" for f in findings)


def test_unreachable_code():
    code = "def get_val():\n    return 42\n    print('never reached')\n"
    findings = analyze_python_ast(code, "logic.py")
    assert any(f.rule_id == "AST-UNREACHABLE-CODE" for f in findings)
    assert any(f.confidence == "Detected" for f in findings)


def test_js_pattern_checks():
    js_code = """
    var user = "admin";
    if (user == "admin") {
        console.log("Logged in");
    }
    try {
        doSomething();
    } catch (e) {}
    """
    findings = analyze_js_patterns(js_code, "app.js")
    rule_ids = {f.rule_id for f in findings}
    assert "JS-VAR-USAGE" in rule_ids
    assert "JS-LOOSE-EQUALITY" in rule_ids
    assert "JS-CONSOLE-LOG" in rule_ids
    assert "JS-EMPTY-CATCH" in rule_ids


def test_project_level_detection_with_ruff():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        py_file = tmp_path / "main.py"
        py_file.write_text(
            "import os\n"  # Unused import
            "def foo():\n"
            "    x = 1\n"  # Unused variable
            "    print(y)\n"  # Undefined variable
        )

        js_file = tmp_path / "index.js"
        js_file.write_text("var count = 0;\nconsole.log(count);\n")

        findings = detect_bugs_in_project(tmp_path)
        assert len(findings) > 0
        rule_ids = {f.rule_id for f in findings}

        # Ruff catches unused import and undefined variable
        assert any("F401" in r for r in rule_ids)  # Unused import
        assert any("F821" in r for r in rule_ids)  # Undefined variable
        assert "JS-VAR-USAGE" in rule_ids
        assert "JS-CONSOLE-LOG" in rule_ids

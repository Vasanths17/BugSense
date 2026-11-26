"""
tests/test_quality_analyzer.py
──────────────────────────────
Unit tests verifying Feature 4 (Code Quality Analysis):
- Radon integration: Cyclomatic Complexity, Maintainability Index, Raw metrics
- Overly complex function flagging
- Non-Python quality checks (deep nesting, TODO markers, file lengths)
- FileQualityMetrics structure generation
"""

import tempfile
from pathlib import Path
from services.quality_analyzer import (
    analyze_python_quality,
    analyze_generic_quality,
    analyze_project_quality,
)


def test_python_cyclomatic_complexity_and_metrics():
    # Construct a function with high cyclomatic complexity (> 10)
    complex_code = """
def complex_decision_tree(a, b, c, d):
    # TODO: Refactor this method into polymorphic classes
    result = 0
    if a > 0:
        if b > 0:
            result += 1
        elif b < 0:
            result -= 1
    elif a < 0:
        if c > 0:
            result += 2
        elif c < 0:
            result -= 2
    if d == 1:
        result += 10
    elif d == 2:
        result += 20
    elif d == 3:
        result += 30
    elif d == 4:
        result += 40
    elif d == 5:
        result += 50
    return result
"""
    findings, metrics = analyze_python_quality(complex_code, "decision.py")

    assert metrics.language == "Python"
    assert metrics.loc > 20
    assert metrics.cyclomatic_complexity is not None
    assert metrics.cyclomatic_complexity > 10
    assert metrics.maintainability_index is not None
    assert metrics.todo_count == 1

    rule_ids = {f.rule_id for f in findings}
    assert "QUAL-HIGH-COMPLEXITY" in rule_ids
    assert "QUAL-TODO-COMMENT" in rule_ids
    assert all(f.category == "Code Quality" for f in findings)


def test_generic_code_quality():
    js_code = """
    // TODO: implement caching layer
    function deeplyNested(x) {
        if (x > 0) {
            for (let i = 0; i < x; i++) {
                while (true) {
                    if (i % 2 === 0) {
                        if (x === 100) {
                            return true;
                        }
                    }
                }
            }
        }
    }
    """
    findings, metrics = analyze_generic_quality(js_code, "script.js", ".js")

    assert metrics.language == "JavaScript"
    assert metrics.todo_count == 1
    assert any(f.rule_id == "QUAL-DEEP-NESTING" for f in findings)
    assert any(f.rule_id == "QUAL-TODO-COMMENT" for f in findings)
    assert all(f.category == "Code Quality" for f in findings)


def test_project_quality_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        py_file = tmp_path / "math_ops.py"
        py_file.write_text("def add(a, b):\n    # Simple addition\n    return a + b\n")

        ts_file = tmp_path / "app.ts"
        ts_file.write_text("// FIXME: fix typing\nconst val: number = 42;\n")

        result = analyze_project_quality(tmp_path)
        assert len(result.file_metrics) == 2
        file_paths = {m.file_path for m in result.file_metrics}
        assert "math_ops.py" in file_paths
        assert "app.ts" in file_paths

        assert any(f.rule_id == "QUAL-TODO-COMMENT" for f in result.findings)

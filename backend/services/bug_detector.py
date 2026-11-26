"""
bug_detector.py
─────────────────
Feature 2: Static Bug Detection Engine.

Analyzes Python source files via:
  1. Python built-in AST parser (syntax errors, mutable defaults, bare excepts,
     duplicate dict keys, self-assignments, unreachable code after return/raise).
  2. Ruff static analysis CLI (undefined variables, unused imports, dead code, etc.).

Analyzes JS/TS source files via:
  3. Static pattern & regex matching (console.log leftovers, `==` loose equality,
     `var` usage, empty catch blocks, alert/debugger statements).

Security:
  - Source code is strictly parsed/scanned as plain text / AST structures.
  - Zero execution, importing, or mutation.
  - Normalizes every finding into the unified Pydantic model `RawFinding`.
"""

import ast
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from models.finding import ConfidenceLevel, RawFinding

logger = logging.getLogger(__name__)

# Common skipped directory names
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", ".vite", "build", ".idea", ".vscode"
}


# ── 1. Python AST Custom Visitor ─────────────────────────────────────────────

class PythonBugAstVisitor(ast.NodeVisitor):
    """
    Scans a Python AST without executing any code.
    Detects:
      - Mutable default arguments (def foo(x=[]))
      - Bare except clauses (except:)
      - Duplicate dictionary keys ({'a': 1, 'a': 2})
      - Self assignments (x = x)
      - Unreachable code immediately following return, raise, break, continue
    """

    def __init__(self, file_path: str, lines: List[str]):
        self.file_path = file_path
        self.lines = lines
        self.findings: List[RawFinding] = []

    def _get_snippet(self, lineno: int) -> Optional[str]:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_mutable_defaults(node)
        self._check_unreachable_code(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_mutable_defaults(node)
        self._check_unreachable_code(node.body)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node):
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                type_name = type(default).__name__.lower()
                self.findings.append(RawFinding(
                    rule_id="AST-MUTABLE-DEFAULT",
                    tool="ast",
                    category="Bug",
                    file_path=self.file_path,
                    line_number=default.lineno,
                    column_number=getattr(default, "col_offset", None),
                    raw_message=f"Mutable default argument of type '{type_name}' in function '{node.name}'. Can lead to shared state bugs across calls.",
                    confidence="Potential",
                    code_snippet=self._get_snippet(default.lineno),
                ))

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.findings.append(RawFinding(
                rule_id="AST-BARE-EXCEPT",
                tool="ast",
                category="Bug",
                file_path=self.file_path,
                line_number=node.lineno,
                column_number=getattr(node, "col_offset", None),
                raw_message="Bare 'except:' caught. Catches SystemExit, KeyboardInterrupt, and masks unintended exceptions.",
                confidence="Potential",
                code_snippet=self._get_snippet(node.lineno),
            ))
        elif isinstance(node.type, ast.Name) and node.type.id == "BaseException":
            self.findings.append(RawFinding(
                rule_id="AST-BROAD-EXCEPTION",
                tool="ast",
                category="Bug",
                file_path=self.file_path,
                line_number=node.lineno,
                column_number=getattr(node, "col_offset", None),
                raw_message="Catching 'BaseException' directly catches system termination signals.",
                confidence="Potential",
                code_snippet=self._get_snippet(node.lineno),
            ))
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        seen_keys = set()
        for key in node.keys:
            if key is None:
                continue
            if isinstance(key, ast.Constant):
                val = key.value
                if val in seen_keys:
                    self.findings.append(RawFinding(
                        rule_id="AST-DUPLICATE-DICT-KEY",
                        tool="ast",
                        category="Bug",
                        file_path=self.file_path,
                        line_number=key.lineno,
                        column_number=getattr(key, "col_offset", None),
                        raw_message=f"Duplicate dictionary key '{val}' detected. Earlier value will be overwritten.",
                        confidence="Detected",
                        code_snippet=self._get_snippet(key.lineno),
                    ))
                else:
                    seen_keys.add(val)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Name):
                if target.id == node.value.id:
                    self.findings.append(RawFinding(
                        rule_id="AST-SELF-ASSIGNMENT",
                        tool="ast",
                        category="Bug",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column_number=getattr(node, "col_offset", None),
                        raw_message=f"Self-assignment detected: variable '{target.id}' assigned to itself.",
                        confidence="Detected",
                        code_snippet=self._get_snippet(node.lineno),
                    ))
        self.generic_visit(node)

    def _check_unreachable_code(self, stmts: List[ast.stmt]):
        terminal_encountered = False
        for stmt in stmts:
            if terminal_encountered:
                self.findings.append(RawFinding(
                    rule_id="AST-UNREACHABLE-CODE",
                    tool="ast",
                    category="Bug",
                    file_path=self.file_path,
                    line_number=stmt.lineno,
                    column_number=getattr(stmt, "col_offset", None),
                    raw_message="Unreachable code statement detected after terminal control statement (return, raise, break, continue).",
                    confidence="Detected",
                    code_snippet=self._get_snippet(stmt.lineno),
                ))
                break  # Flag first unreachable statement in block
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminal_encountered = True


def analyze_python_ast(source_text: str, relative_path: str) -> List[RawFinding]:
    """
    Parses Python code into an AST and collects structural bugs.
    Catches SyntaxError gracefully without crashing or executing.
    """
    lines = source_text.splitlines()
    findings: List[RawFinding] = []

    try:
        tree = ast.parse(source_text, filename=relative_path)
    except SyntaxError as err:
        findings.append(RawFinding(
            rule_id="AST-SYNTAX-ERROR",
            tool="ast",
            category="Bug",
            file_path=relative_path,
            line_number=err.lineno or 1,
            column_number=err.offset,
            raw_message=f"SyntaxError: {err.msg}",
            confidence="Detected",
            code_snippet=err.text.strip() if err.text else (lines[err.lineno - 1].strip() if err.lineno and err.lineno <= len(lines) else None),
        ))
        return findings

    visitor = PythonBugAstVisitor(relative_path, lines)
    visitor.visit(tree)
    findings.extend(visitor.findings)
    return findings


# ── 2. Ruff Linter Analysis ──────────────────────────────────────────────────

def _determine_ruff_confidence(rule_code: str) -> ConfidenceLevel:
    """
    Classifies Ruff rules into 'Detected' (clear bugs, syntax, undefined vars)
    versus 'Potential' (heuristics, code style, potential bugs).
    """
    # F821: undefined name, F822: undefined export, F706: return outside func,
    # F632: use == with None, F601: duplicate dict key, E999: syntax error,
    # F401: unused import, F841: unused variable, B006: mutable default
    definite_codes = {
        "E999", "F821", "F822", "F823", "F706", "F704", "F707", "F601",
        "F602", "F632", "F401", "F841", "F811", "F831", "B006", "B008"
    }
    if rule_code in definite_codes:
        return "Detected"
    # General prefixes
    if rule_code.startswith(("F8", "E9")):
        return "Detected"
    return "Potential"


def run_ruff_on_path(target_path: Path, project_root: Path) -> List[RawFinding]:
    """
    Runs `ruff check --output-format=json` on a file or directory.
    Uses the venv's python executable or ruff binary if available.
    """
    findings: List[RawFinding] = []

    # Locate ruff binary
    venv_ruff = project_root.parent / "venv" / "Scripts" / "ruff.exe"
    if not venv_ruff.exists():
        # Fallback to sys.prefix or shutil.which
        venv_ruff = Path(sys.prefix) / "Scripts" / "ruff.exe"
    ruff_cmd = str(venv_ruff) if venv_ruff.exists() else shutil.which("ruff")

    if not ruff_cmd:
        logger.warning("Ruff executable not found. Skipping Ruff analysis step.")
        return findings

    try:
        proc = subprocess.run(
            [
                ruff_cmd,
                "check",
                "--output-format=json",
                "--no-cache",
                "--select=E,F,B,W",  # Errors, Pyflakes, Bugbear, Warnings
                str(target_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.stdout:
            data = json.loads(proc.stdout)
            for item in data:
                file_abs = Path(item.get("filename", ""))
                try:
                    rel_file = file_abs.relative_to(project_root).as_posix()
                except ValueError:
                    rel_file = file_abs.name

                code = item.get("code") or "RUFF-WARN"
                confidence = _determine_ruff_confidence(code)

                location = item.get("location", {})
                line_no = location.get("row", 1)
                col_no = location.get("column", 1)

                findings.append(RawFinding(
                    rule_id=f"RUFF-{code}",
                    tool="ruff",
                    category="Bug",
                    file_path=rel_file,
                    line_number=line_no,
                    column_number=col_no,
                    raw_message=item.get("message", "Lint warning"),
                    confidence=confidence,
                    code_snippet=None,
                ))
    except Exception as exc:
        logger.error(f"Error executing Ruff analysis: {exc}")

    return findings


# ── 3. JS/TS Lightweight Static Regex / Pattern Scanner ───────────────────────

JS_PATTERNS = [
    (
        r"\bconsole\.(log|debug|trace|warn)\s*\(",
        "JS-CONSOLE-LOG",
        "Console logging statement leftover in production code.",
        "Potential"
    ),
    (
        r"(?<![!=<>])==(?!=)",
        "JS-LOOSE-EQUALITY",
        "Loose equality '==' used instead of strict '==='. Can cause unexpected type coercion bugs.",
        "Potential"
    ),
    (
        r"(?<![!=<>])!=(?!=)",
        "JS-LOOSE-INEQUALITY",
        "Loose inequality '!=' used instead of strict '!=='. Can cause unexpected type coercion bugs.",
        "Potential"
    ),
    (
        r"\bvar\s+[a-zA-Z_$][0-9a-zA-Z_$]*",
        "JS-VAR-USAGE",
        "'var' declaration used. Prefer 'let' or 'const' to prevent variable hoisting and scope leak bugs.",
        "Potential"
    ),
    (
        r"\bdebugger\s*;",
        "JS-DEBUGGER-STATEMENT",
        "'debugger' breakpoint statement committed in code.",
        "Detected"
    ),
    (
        r"\bcatch\s*\([^)]*\)\s*\{\s*\}",
        "JS-EMPTY-CATCH",
        "Empty catch block detected. Swallows exceptions silently without handling or logging.",
        "Detected"
    ),
    (
        r"\balert\s*\(",
        "JS-ALERT-STATEMENT",
        "Blocking 'alert()' statement in code.",
        "Potential"
    ),
]


def analyze_js_patterns(source_text: str, relative_path: str) -> List[RawFinding]:
    """
    Lightweight regex & pattern analysis for JavaScript / TypeScript files.
    """
    findings: List[RawFinding] = []
    lines = source_text.splitlines()

    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.strip()

        # Skip comment lines
        if stripped.startswith(("//", "/*", "*")):
            continue

        for pattern, rule_id, message, confidence in JS_PATTERNS:
            match = re.search(pattern, line)
            if match:
                findings.append(RawFinding(
                    rule_id=rule_id,
                    tool="regex-js",
                    category="Bug",
                    file_path=relative_path,
                    line_number=line_num,
                    column_number=match.start() + 1,
                    raw_message=message,
                    confidence=confidence,  # type: ignore
                    code_snippet=stripped,
                ))

    return findings


# ── 4. Unified Project-Level Bug Detection Engine ────────────────────────────

def detect_bugs_in_project(project_dir: Path) -> List[RawFinding]:
    """
    Scans all supported Python, JS, and TS files in a project directory.
    Combines:
      - Python AST checks (syntax, semantics, control flow)
      - Ruff CLI (standardized linter output)
      - JS/TS pattern checks

    Returns a deduplicated list of RawFinding models.
    """
    all_findings: List[RawFinding] = []
    project_root = project_dir.resolve()

    # 1. AST & Pattern Analysis by traversing files
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue

        # Skip ignored directories
        if any(part in SKIP_DIRS for part in path.parts):
            continue

        try:
            rel_path = path.relative_to(project_root).as_posix()
        except ValueError:
            rel_path = path.name

        ext = path.suffix.lower()

        # Python files -> AST Analysis
        if ext == ".py":
            try:
                code = path.read_text(encoding="utf-8", errors="replace")
                findings = analyze_python_ast(code, rel_path)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Failed to run AST analysis on {rel_path}: {e}")

        # JS / TS files -> Pattern Analysis
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            try:
                code = path.read_text(encoding="utf-8", errors="replace")
                findings = analyze_js_patterns(code, rel_path)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Failed to run JS pattern analysis on {rel_path}: {e}")

    # 2. Ruff Analysis on the whole project directory
    ruff_findings = run_ruff_on_path(project_root, project_root)
    all_findings.extend(ruff_findings)

    # 3. Deduplicate findings on (file_path, line_number, rule_id)
    seen = set()
    deduped: List[RawFinding] = []
    for f in all_findings:
        key = (f.file_path, f.line_number, f.rule_id)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    # Sort findings by file path and line number
    deduped.sort(key=lambda x: (x.file_path, x.line_number))
    return deduped

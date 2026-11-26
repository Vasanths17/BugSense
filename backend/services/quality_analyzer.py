"""
quality_analyzer.py
───────────────────
Feature 4: Code Quality & Metrics Analysis.

Calculates static code quality metrics without executing target code:
  1. Python files (via radon):
     - Cyclomatic Complexity (radon.complexity) per function & file average
     - Maintainability Index (radon.metrics.mi_visit) score (0–100) & rank (A–C)
     - Raw metrics (radon.raw): LOC, LLOC, comments, blank lines
  2. Non-Python files (JS, TS, Java, C/C++, HTML, CSS, etc.):
     - File length / LOC, blank lines, comments (via regex / line inspection)
     - TODO / FIXME comments count
     - Long functions and deeply nested block heuristics
  3. Quality Issue Flagging:
     - High Cyclomatic Complexity (> 10 flagged, > 20 critical)
     - Low Maintainability Index (< 20 low/F, < 50 medium/B/C)
     - Excessively long files (> 500 lines)
     - Deeply nested blocks (nesting level > 4)
     - Unresolved TODO/FIXME markers
  4. Returns `QualityAnalysisResult` containing:
     - `findings`: List of `RawFinding` with category="Code Quality"
     - `file_metrics`: Structured list of `FileQualityMetrics` for frontend tables
"""

import logging
import re
from pathlib import Path
from typing import List, Tuple

from models.finding import (
    FileQualityMetrics,
    FunctionComplexity,
    QualityAnalysisResult,
    RawFinding,
)

logger = logging.getLogger(__name__)

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", ".vite", "build", ".idea", ".vscode"
}

SUPPORTED_QUALITY_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".c", ".cpp", ".html", ".css"
}

# ── Radon imports (Python only) ──────────────────────────────────────────────
try:
    from radon.complexity import cc_rank, cc_visit
    from radon.metrics import mi_rank, mi_visit
    from radon.raw import analyze as raw_analyze
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    logger.warning("Radon library not installed. Python advanced metrics will be approximated.")


# ── Python Code Quality Analysis ─────────────────────────────────────────────

def analyze_python_quality(code: str, relative_path: str) -> Tuple[List[RawFinding], FileQualityMetrics]:
    """
    Computes Python metrics with Radon and flags code quality findings.
    """
    findings: List[RawFinding] = []
    function_complexities: List[FunctionComplexity] = []

    lines = code.splitlines()
    loc = len(lines)
    lloc = loc
    comments = 0
    blank = 0
    avg_complexity = 1.0
    mi_score = 100.0
    mi_letter = "A"

    # Count TODO/FIXME comments
    todo_count = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.search(r"#\s*(TODO|FIXME|HACK|XXX)\b", stripped, re.IGNORECASE):
            todo_count += 1
            findings.append(RawFinding(
                rule_id="QUAL-TODO-COMMENT",
                tool="pattern-quality",
                category="Code Quality",
                file_path=relative_path,
                line_number=idx,
                column_number=None,
                raw_message=f"Unresolved reminder comment: {stripped[:80]}",
                confidence="Potential",
                code_snippet=stripped,
            ))

    if RADON_AVAILABLE:
        # 1. Raw Metrics
        try:
            raw = raw_analyze(code)
            loc = raw.loc
            lloc = raw.lloc
            comments = raw.comments
            blank = raw.blank
        except Exception as e:
            logger.debug(f"Radon raw analysis failed on {relative_path}: {e}")

        # 2. Cyclomatic Complexity
        try:
            blocks = cc_visit(code)
            if blocks:
                complexities = [b.complexity for b in blocks]
                avg_complexity = round(sum(complexities) / len(complexities), 2)

                for b in blocks:
                    rank = cc_rank(b.complexity)
                    function_complexities.append(FunctionComplexity(
                        name=b.name,
                        line_number=b.lineno,
                        complexity=b.complexity,
                        rank=rank,
                    ))

                    # Flag overly complex functions (> 10)
                    if b.complexity > 10:
                        conf = "Detected" if b.complexity > 20 else "Potential"
                        severity = "very high" if b.complexity > 20 else "high"
                        snippet = lines[b.lineno - 1].strip() if 1 <= b.lineno <= len(lines) else None
                        findings.append(RawFinding(
                            rule_id="QUAL-HIGH-COMPLEXITY",
                            tool="radon",
                            category="Code Quality",
                            file_path=relative_path,
                            line_number=b.lineno,
                            column_number=b.col_offset if hasattr(b, 'col_offset') else None,
                            raw_message=f"Function '{b.name}' has {severity} cyclomatic complexity ({b.complexity}, Rank {rank}). Consider refactoring into smaller modular functions.",
                            confidence=conf,
                            code_snippet=snippet,
                        ))
        except Exception as e:
            logger.debug(f"Radon CC analysis failed on {relative_path}: {e}")

        # 3. Maintainability Index
        try:
            mi_score = round(mi_visit(code, multi=True), 2)
            mi_letter = mi_rank(mi_score)

            if mi_score < 40:
                findings.append(RawFinding(
                    rule_id="QUAL-LOW-MAINTAINABILITY",
                    tool="radon",
                    category="Code Quality",
                    file_path=relative_path,
                    line_number=1,
                    column_number=None,
                    raw_message=f"Low Maintainability Index ({mi_score}/100, Rank '{mi_letter}'). High risk for technical debt.",
                    confidence="Potential",
                    code_snippet=None,
                ))
        except Exception as e:
            logger.debug(f"Radon MI analysis failed on {relative_path}: {e}")
    else:
        blank = sum(1 for l in lines if not l.strip())
        comments = sum(1 for l in lines if l.strip().startswith("#"))

    # File size check (> 500 lines)
    if loc > 500:
        findings.append(RawFinding(
            rule_id="QUAL-FILE-TOO-LONG",
            tool="pattern-quality",
            category="Code Quality",
            file_path=relative_path,
            line_number=1,
            column_number=None,
            raw_message=f"File exceeds recommended length ({loc} lines > 500 lines). Violates Single Responsibility Principle.",
            confidence="Potential",
            code_snippet=None,
        ))

    metrics = FileQualityMetrics(
        file_path=relative_path,
        language="Python",
        loc=loc,
        lloc=lloc,
        comments=comments,
        blank_lines=blank,
        cyclomatic_complexity=avg_complexity,
        maintainability_index=mi_score,
        maintainability_rank=mi_letter,
        todo_count=todo_count,
        functions=function_complexities,
    )

    return findings, metrics


# ── Generic / Non-Python Quality Analysis ────────────────────────────────────

def analyze_generic_quality(code: str, relative_path: str, ext: str) -> Tuple[List[RawFinding], FileQualityMetrics]:
    """
    Lightweight code quality metrics for non-Python source files.
    """
    findings: List[RawFinding] = []
    lines = code.splitlines()
    loc = len(lines)
    blank = 0
    comments = 0
    todo_count = 0

    lang_map = {
        ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
        ".ts": "TypeScript", ".tsx": "TypeScript (TSX)",
        ".java": "Java", ".c": "C", ".cpp": "C++",
        ".html": "HTML", ".css": "CSS"
    }
    language = lang_map.get(ext, "Other")

    # Detect deeply nested blocks (> 4 indentation levels)
    max_nesting = 0
    deep_nesting_line = 0

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue

        if stripped.startswith(("//", "/*", "*", "<!--")):
            comments += 1

        # Check for TODO/FIXME
        if re.search(r"//\s*(TODO|FIXME|HACK|XXX)\b|<!--\s*(TODO|FIXME)\b", stripped, re.IGNORECASE):
            todo_count += 1
            findings.append(RawFinding(
                rule_id="QUAL-TODO-COMMENT",
                tool="pattern-quality",
                category="Code Quality",
                file_path=relative_path,
                line_number=idx,
                column_number=None,
                raw_message=f"Unresolved reminder comment: {stripped[:80]}",
                confidence="Potential",
                code_snippet=stripped,
            ))

        # Heuristic for nesting via leading indentation
        indent = len(line) - len(line.lstrip())
        level = indent // 4 if "\t" not in line else line.count("\t")
        if level > max_nesting and stripped.startswith(("if", "for", "while", "switch", "try")):
            max_nesting = level
            deep_nesting_line = idx

    if max_nesting >= 5:
        findings.append(RawFinding(
            rule_id="QUAL-DEEP-NESTING",
            tool="pattern-quality",
            category="Code Quality",
            file_path=relative_path,
            line_number=deep_nesting_line or 1,
            column_number=None,
            raw_message=f"Deeply nested control block detected ({max_nesting} levels deep). Increases cognitive complexity.",
            confidence="Potential",
            code_snippet=lines[deep_nesting_line - 1].strip() if deep_nesting_line else None,
        ))

    # File length check (> 500 lines)
    if loc > 500:
        findings.append(RawFinding(
            rule_id="QUAL-FILE-TOO-LONG",
            tool="pattern-quality",
            category="Code Quality",
            file_path=relative_path,
            line_number=1,
            column_number=None,
            raw_message=f"File exceeds recommended length ({loc} lines > 500 lines).",
            confidence="Potential",
            code_snippet=None,
        ))

    # Approximate maintainability index
    mi_approx = max(20.0, min(100.0, 100.0 - (loc / 20.0) - (max_nesting * 5)))
    mi_letter = "A" if mi_approx >= 80 else ("B" if mi_approx >= 50 else "C")

    metrics = FileQualityMetrics(
        file_path=relative_path,
        language=language,
        loc=loc,
        lloc=loc - blank - comments,
        comments=comments,
        blank_lines=blank,
        cyclomatic_complexity=float(max(1, max_nesting)),
        maintainability_index=round(mi_approx, 2),
        maintainability_rank=mi_letter,
        todo_count=todo_count,
        functions=[],
    )

    return findings, metrics


# ── Unified Project-Level Quality Analysis ───────────────────────────────────

def analyze_project_quality(project_dir: Path) -> QualityAnalysisResult:
    """
    Scans project directory and generates:
      - List of RawFinding (category="Code Quality")
      - List of FileQualityMetrics per file
    """
    all_findings: List[RawFinding] = []
    file_metrics: List[FileQualityMetrics] = []
    project_root = project_dir.resolve()

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in SKIP_DIRS for part in path.parts):
            continue

        ext = path.suffix.lower()
        if ext in SUPPORTED_QUALITY_EXTS:
            try:
                rel_path = path.relative_to(project_root).as_posix()
            except ValueError:
                rel_path = path.name

            try:
                code = path.read_text(encoding="utf-8", errors="replace")
                if ext == ".py":
                    findings, metrics = analyze_python_quality(code, rel_path)
                else:
                    findings, metrics = analyze_generic_quality(code, rel_path, ext)

                all_findings.extend(findings)
                file_metrics.append(metrics)
            except Exception as e:
                logger.error(f"Error analyzing code quality for {rel_path}: {e}")

    # Deduplicate findings
    seen = set()
    deduped_findings: List[RawFinding] = []
    for f in all_findings:
        key = (f.file_path, f.line_number, f.rule_id)
        if key not in seen:
            seen.add(key)
            deduped_findings.append(f)

    deduped_findings.sort(key=lambda x: (x.file_path, x.line_number))
    file_metrics.sort(key=lambda m: m.file_path)

    return QualityAnalysisResult(
        findings=deduped_findings,
        file_metrics=file_metrics
    )

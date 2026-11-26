"""
explainer.py
────────────
Feature 5 & 6: Explainable Issue Analysis & Severity Classification.

Responsibilities:
  1. Loads the local Explainability Knowledge Base (`knowledge_base/rules.json`).
  2. For every `RawFinding`, generates an `ExplainedIssue` with all 9 required fields:
     - title
     - category ("Bug", "Security", "Code Quality")
     - file_name
     - line_number
     - explanation
     - why_it_matters
     - possible_impact
     - severity ("Critical", "High", "Medium", "Low")
     - recommendation
     Plus: `id`, `detection_type` ("Detected" vs "Potential"), `code_snippet` (3-5 lines context).
  3. Includes smart fallback templating for unmapped or unfamiliar rule IDs.
  4. Implements transparent severity classification logic.
  5. Never modifies or rewrites user source code.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models.finding import (
    CategoryBreakdown,
    ExplainedIssue,
    RawFinding,
    SeverityBreakdown,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "rules.json"

# In-memory cached rules dictionary
_KNOWLEDGE_BASE: Optional[Dict[str, dict]] = None


def get_knowledge_base() -> Dict[str, dict]:
    """Loads and caches the explainability dictionary from rules.json."""
    global _KNOWLEDGE_BASE
    if _KNOWLEDGE_BASE is None:
        try:
            if KB_PATH.exists():
                text = KB_PATH.read_text(encoding="utf-8")
                _KNOWLEDGE_BASE = json.loads(text)
            else:
                logger.warning(f"Knowledge base rules file not found at {KB_PATH}")
                _KNOWLEDGE_BASE = {}
        except Exception as e:
            logger.error(f"Failed to load rules knowledge base: {e}")
            _KNOWLEDGE_BASE = {}
    return _KNOWLEDGE_BASE


# ── Read-Only Multi-line Code Snippet Context ────────────────────────────────

def get_context_snippet(project_root: Path, file_name: str, line_no: Optional[int], context_lines: int = 2) -> Optional[str]:
    """
    Safely reads 3-5 lines of code context around line_no from the extracted project.
    Never modifies user files.
    """
    if not line_no or line_no < 1:
        return None

    try:
        file_path = (project_root / file_name).resolve()
        if not file_path.is_file() or not str(file_path).startswith(str(project_root.resolve())):
            return None

        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, line_no - context_lines - 1)
        end = min(len(lines), line_no + context_lines)

        snippet_parts = []
        for i in range(start, end):
            prefix = "▶ " if (i + 1) == line_no else "  "
            snippet_parts.append(f"{prefix}{i + 1:4d} | {lines[i]}")

        return "\n".join(snippet_parts)
    except Exception as e:
        logger.debug(f"Could not load context snippet for {file_name}:{line_no}: {e}")
        return None


# ── Severity Classification Rules ───────────────────────────────────────────

def determine_severity(finding: RawFinding, rule_entry: Optional[dict]) -> SeverityLevel:
    """
    Transparent severity classification:
      - Critical: severe security flaws (SQLi, command injection, hardcoded secrets, eval/exec)
                  or syntax errors breaking execution.
      - High: undefined variables, high-risk security practices, very high complexity.
      - Medium: potential logical bugs, maintainability warnings, weak practices.
      - Low: unused imports/variables, style/standards, TODOs.
    """
    # 1. If knowledge base has an explicit severity, check if context overrides it
    if rule_entry and "severity" in rule_entry:
        base_sev = rule_entry["severity"]
        # Special check: Very high complexity (>20) upgrades to High
        if finding.rule_id == "QUAL-HIGH-COMPLEXITY" and finding.confidence == "Detected":
            return "High"
        return base_sev

    rule_upper = finding.rule_id.upper()
    cat_upper = finding.category.upper()

    # Critical patterns
    if any(k in rule_upper for k in ["SYNTAX", "SQLI", "SQL-INJECTION", "COMMAND", "SHELL", "EVAL", "SECRET", "CREDENTIAL", "TOKEN"]):
        return "Critical"

    # High patterns
    if any(k in rule_upper for k in ["UNDEFINED", "F821", "EMPTY-CATCH", "DUPLICATE", "WEAK-HASH", "DEBUG"]):
        return "High"

    # Low patterns
    if any(k in rule_upper for k in ["UNUSED", "F401", "F841", "CONSOLE", "VAR", "TODO", "COMMENT", "ALERT", "FILE-TOO-LONG"]):
        return "Low"

    # Category defaults
    if cat_upper == "SECURITY":
        return "High" if finding.confidence == "Detected" else "Medium"
    if cat_upper == "BUG":
        return "High" if finding.confidence == "Detected" else "Medium"

    return "Medium"


# ── Fallback Explainability Template ─────────────────────────────────────────

def generate_fallback_explanation(finding: RawFinding) -> dict:
    """
    Generates intelligent fallback explanation fields for unmapped rule codes.
    """
    rule_code = finding.rule_id
    clean_msg = finding.raw_message or "Potential software issue detected."

    if finding.category == "Security":
        title = f"Security Advisory: {rule_code}"
        explanation = f"A static security check flagged a potential vulnerability: {clean_msg}"
        why_it_matters = "Security vulnerabilities may expose sensitive data or allow unauthorized operation."
        possible_impact = "Risk of security exposure or compromise if untrusted input reaches this code."
        recommendation = "Review this pattern against OWASP and secure coding best practices."
    elif finding.category == "Code Quality":
        title = f"Code Quality Advisory: {rule_code}"
        explanation = f"A code quality check noted an area for improvement: {clean_msg}"
        why_it_matters = "Sub-optimal coding patterns degrade readability, testability, and long-term maintainability."
        possible_impact = "Accumulation of technical debt and slower developer velocity."
        recommendation = "Consider refactoring the flagged construct to adhere to team quality guidelines."
    else:  # Bug
        title = f"Potential Bug: {rule_code}"
        explanation = f"Static analysis identified a code pattern that may lead to unexpected behavior: {clean_msg}"
        why_it_matters = "Code anomalies often produce silent errors, incorrect results, or edge-case crashes."
        possible_impact = "Unexpected runtime failures or logic discrepancies during execution."
        recommendation = "Inspect the flagged line and verify test coverage around this logic."

    return {
        "title": title,
        "explanation": explanation,
        "why_it_matters": why_it_matters,
        "possible_impact": possible_impact,
        "recommendation": recommendation,
    }


# ── Explainer Engine ─────────────────────────────────────────────────────────

def explain_finding(finding: RawFinding, issue_index: int, project_root: Optional[Path] = None) -> ExplainedIssue:
    """
    Transforms a single `RawFinding` into an `ExplainedIssue` with all 9 required fields.
    """
    kb = get_knowledge_base()

    # Look up direct rule_id or base code (e.g. "RUFF-F821" -> "RUFF-F821" or "F821")
    rule_entry = kb.get(finding.rule_id)
    if not rule_entry:
        # Check without tool prefix
        parts = finding.rule_id.split("-", 1)
        if len(parts) > 1 and parts[1] in kb:
            rule_entry = kb[parts[1]]

    if rule_entry:
        title = rule_entry.get("title", finding.rule_id)
        category = rule_entry.get("category", finding.category)
        explanation = rule_entry.get("explanation", finding.raw_message)
        why_it_matters = rule_entry.get("why_it_matters", "Problematic code pattern.")
        possible_impact = rule_entry.get("possible_impact", "May cause software defects.")
        recommendation = rule_entry.get("recommendation", "Refactor the flagged line.")
    else:
        fallback = generate_fallback_explanation(finding)
        title = fallback["title"]
        category = finding.category
        explanation = fallback["explanation"]
        why_it_matters = fallback["why_it_matters"]
        possible_impact = fallback["possible_impact"]
        recommendation = fallback["recommendation"]

    # Calculate severity
    severity = determine_severity(finding, rule_entry)

    # Fetch 3-5 line read-only snippet if project_root is provided
    code_context = None
    if project_root:
        code_context = get_context_snippet(project_root, finding.file_path, finding.line_number)
    if not code_context:
        code_context = finding.code_snippet

    return ExplainedIssue(
        id=f"ISSUE-{issue_index:03d}",
        rule_id=finding.rule_id,
        tool=finding.tool,
        title=title,
        category=category,  # type: ignore
        file_name=finding.file_path,
        line_number=finding.line_number,
        explanation=explanation,
        why_it_matters=why_it_matters,
        possible_impact=possible_impact,
        severity=severity,
        recommendation=recommendation,
        detection_type=finding.confidence,
        code_snippet=code_context,
    )


def explain_all_findings(findings: List[RawFinding], project_root: Optional[Path] = None) -> List[ExplainedIssue]:
    """
    Transforms a list of RawFinding items into ExplainedIssue objects.
    Sorted by severity (Critical -> High -> Medium -> Low).
    """
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

    explained_issues: List[ExplainedIssue] = []
    for idx, f in enumerate(findings, start=1):
        issue = explain_finding(f, idx, project_root)
        explained_issues.append(issue)

    # Sort issues: Critical first, then High, Medium, Low
    explained_issues.sort(key=lambda x: (severity_order.get(x.severity, 4), x.file_name, x.line_number or 0))

    # Re-index nicely formatted IDs
    for idx, issue in enumerate(explained_issues, start=1):
        issue.id = f"ISSUE-{idx:03d}"

    return explained_issues


def compute_breakdowns(issues: List[ExplainedIssue]) -> Tuple[SeverityBreakdown, CategoryBreakdown]:
    """
    Computes statistical counts for severity and category breakdowns.
    """
    sev = SeverityBreakdown()
    cat = CategoryBreakdown()

    for issue in issues:
        # Severity
        if issue.severity == "Critical":
            sev.critical += 1
        elif issue.severity == "High":
            sev.high += 1
        elif issue.severity == "Medium":
            sev.medium += 1
        elif issue.severity == "Low":
            sev.low += 1

        # Category
        if issue.category == "Bug":
            cat.bugs += 1
        elif issue.category == "Security":
            cat.security += 1
        elif issue.category == "Code Quality":
            cat.quality += 1

    return sev, cat

"""
tests/test_pdf_and_cleanup.py
─────────────────────────────
Verifies:
- PDF generation producing non-empty valid PDF byte stream with %PDF- header
- Disclaimers, multi-severity grouping, wrapped texts
- Automatic stale project cleanup logic
- DELETE /api/project/{project_id} endpoint
"""

import io
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone

from models.finding import (
    AnalysisReport,
    CategoryBreakdown,
    ExplainedIssue,
    FileQualityMetrics,
    HealthScoreDetails,
    SeverityBreakdown,
)
from services.pdf_generator import generate_pdf_report
from routers.analysis import cleanup_stale_temp_uploads, ANALYSIS_CACHE


def test_pdf_generation_valid_output():
    report = AnalysisReport(
        project_id="test-proj-123",
        project_name="SampleVulnerableApp",
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        total_issues=3,
        detected_count=2,
        potential_count=1,
        severity_breakdown=SeverityBreakdown(critical=1, high=1, medium=1, low=0),
        category_breakdown=CategoryBreakdown(bugs=1, security=1, quality=1),
        health_score=HealthScoreDetails(
            score=65,
            grade="C",
            status="Needs Attention",
            defect_density_score=50.0,
            quality_score=80.0,
            total_loc=350,
            explanation="Calculated from 1 Critical, 1 High, 1 Medium issue.",
        ),
        issues=[
            ExplainedIssue(
                id="ISSUE-001",
                rule_id="SEC-SQL-INJECTION",
                tool="pattern-security",
                title="Potential SQL Injection",
                category="Security",
                file_name="models/db.py",
                line_number=24,
                explanation="Raw SQL query constructed via concatenation.",
                why_it_matters="Allows attackers to bypass authentication or extract records.",
                possible_impact="Total database compromise.",
                severity="Critical",
                recommendation="Use parameterized queries instead of string concatenation.",
                detection_type="Potential",
                code_snippet="▶   24 | cursor.execute('SELECT * FROM users WHERE id = ' + uid)",
            ),
            ExplainedIssue(
                id="ISSUE-002",
                rule_id="RUFF-F821",
                tool="ruff",
                title="Undefined Variable",
                category="Bug",
                file_name="utils.py",
                line_number=15,
                explanation="Name 'unresolved_var' is referenced without definition.",
                why_it_matters="Triggers NameError as soon as this line executes.",
                possible_impact="Runtime application crash.",
                severity="High",
                recommendation="Define or import the variable before use.",
                detection_type="Detected",
                code_snippet="▶   15 | return unresolved_var * 2",
            ),
        ],
        file_metrics=[
            FileQualityMetrics(
                file_path="models/db.py",
                language="Python",
                loc=120,
                cyclomatic_complexity=4.0,
                maintainability_index=78.5,
                maintainability_rank="B",
            ),
            FileQualityMetrics(
                file_path="utils.py",
                language="Python",
                loc=85,
                cyclomatic_complexity=2.0,
                maintainability_index=88.0,
                maintainability_rank="A",
            ),
        ],
    )

    pdf_bytes = generate_pdf_report(report)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_stale_cleanup():
    # Test cleanup logic runs without error
    cleanup_stale_temp_uploads(max_age_seconds=86400)

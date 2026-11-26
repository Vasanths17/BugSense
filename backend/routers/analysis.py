"""
routers/analysis.py
───────────────────
POST /api/analyze/{project_id} – runs full multi-engine analysis pipeline:
  1. Static Bug Detection (AST, Ruff, JS/TS patterns)
  2. Security Vulnerability Scanning (Bandit, Secret/Injection patterns)
  3. Code Quality Analysis (Radon metrics, Complexity, Maintainability)
  4. Local Explainability Engine (Knowledge base translation + 9 required fields)
  5. Health Score Calculation (0-100 score, letter grade, breakdown)
  6. Caches and persists report in memory/disk for project_id

GET  /api/analyze/{project_id} and GET /api/analysis/{project_id} – retrieves cached report
GET  /api/report/{project_id}/pdf – generates and streams downloadable PDF report
DELETE /api/project/{project_id} – removes extracted project directory and clears caches
"""

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from models.finding import AnalysisReport
from services.bug_detector import detect_bugs_in_project
from services.explainer import compute_breakdowns, explain_all_findings
from services.health_score import calculate_health_score
from services.pdf_generator import generate_pdf_report
from services.quality_analyzer import analyze_project_quality
from services.security_scanner import scan_security_in_project
from services.upload_service import TEMP_UPLOADS_ROOT

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for generated analysis reports
ANALYSIS_CACHE: Dict[str, AnalysisReport] = {}


def cleanup_stale_temp_uploads(max_age_seconds: int = 3600):
    """
    Cleans up temp directories older than max_age_seconds (default 1 hour).
    """
    now = time.time()
    if not TEMP_UPLOADS_ROOT.exists():
        return

    for item in TEMP_UPLOADS_ROOT.iterdir():
        if item.is_dir() and item.name != ".gitkeep":
            try:
                mtime = item.stat().st_mtime
                if (now - mtime) > max_age_seconds:
                    logger.info(f"Removing stale temporary directory: {item.name}")
                    shutil.rmtree(item, ignore_errors=True)
                    ANALYSIS_CACHE.pop(item.name, None)
            except Exception as e:
                logger.debug(f"Error checking/cleaning directory {item}: {e}")


@router.post("/api/analyze/{project_id}", response_model=AnalysisReport)
async def run_project_analysis(project_id: str):
    """
    Executes all local analyzers against the extracted project:
    - Zero execution of user code
    - Offline explainability generation via local rules.json
    - Computes metrics and severity rankings
    - Computes normalized Health Score (0-100)
    """
    # Run automatic periodic cleanup of stale uploads
    cleanup_stale_temp_uploads()

    project_dir = (TEMP_UPLOADS_ROOT / project_id).resolve()

    if not project_dir.exists() or not project_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found. Please upload the project ZIP first."
        )

    logger.info(f"Starting complete static analysis for project {project_id}...")

    # 1. Run Static Bug Detector (Feature 2)
    try:
        bug_findings = detect_bugs_in_project(project_dir)
    except Exception as e:
        logger.error(f"Bug detection failed: {e}")
        bug_findings = []

    # 2. Run Security Scanner (Feature 3)
    try:
        sec_findings = scan_security_in_project(project_dir)
    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        sec_findings = []

    # 3. Run Quality Analyzer (Feature 4)
    try:
        quality_result = analyze_project_quality(project_dir)
        qual_findings = quality_result.findings
        file_metrics = quality_result.file_metrics
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        qual_findings = []
        file_metrics = []

    # 4. Combine all raw findings and deduplicate
    all_raw_findings = bug_findings + sec_findings + qual_findings
    seen = set()
    deduped_raw = []
    for f in all_raw_findings:
        key = (f.file_path, f.line_number, f.rule_id)
        if key not in seen:
            seen.add(key)
            deduped_raw.append(f)

    # 5. Transform via Explainability Engine (Feature 5 & 6)
    explained_issues = explain_all_findings(deduped_raw, project_root=project_dir)

    # 6. Compute Statistics & Breakdowns
    sev_breakdown, cat_breakdown = compute_breakdowns(explained_issues)

    detected_count = sum(1 for i in explained_issues if i.detection_type == "Detected")
    potential_count = sum(1 for i in explained_issues if i.detection_type == "Potential")

    # 7. Calculate Project Health Score (Feature 7)
    health_score_details = calculate_health_score(sev_breakdown, file_metrics)

    project_name = project_dir.name

    report = AnalysisReport(
        project_id=project_id,
        project_name=project_name,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        total_issues=len(explained_issues),
        detected_count=detected_count,
        potential_count=potential_count,
        severity_breakdown=sev_breakdown,
        category_breakdown=cat_breakdown,
        health_score=health_score_details,
        issues=explained_issues,
        file_metrics=file_metrics,
    )

    # Cache report in memory
    ANALYSIS_CACHE[project_id] = report

    # Also persist report as report.json in the project folder
    try:
        report_file = project_dir / "analysis_report.json"
        report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not persist analysis_report.json to disk: {e}")

    logger.info(f"Analysis complete for {project_id}: {len(explained_issues)} issues found. Health Score: {health_score_details.score}/100 ({health_score_details.grade})")
    return report


@router.get("/api/analyze/{project_id}", response_model=AnalysisReport)
@router.get("/api/analysis/{project_id}", response_model=AnalysisReport)
async def get_project_analysis(project_id: str):
    """
    Retrieves the generated analysis report for a given project.
    Accessible at both /api/analyze/{project_id} and /api/analysis/{project_id}.
    """
    if project_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[project_id]

    project_dir = (TEMP_UPLOADS_ROOT / project_id).resolve()
    report_file = project_dir / "analysis_report.json"

    if report_file.exists():
        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
            report = AnalysisReport(**data)
            ANALYSIS_CACHE[project_id] = report
            return report
        except Exception as e:
            logger.error(f"Failed loading cached report from disk: {e}")

    raise HTTPException(
        status_code=404,
        detail=f"Analysis report for project '{project_id}' not found. Run analysis first."
    )


@router.get("/api/report/{project_id}/pdf")
async def download_pdf_report(project_id: str):
    """
    Generates and streams a downloadable, professional PDF report for project_id.
    """
    # 1. Retrieve the analysis report
    report = None
    if project_id in ANALYSIS_CACHE:
        report = ANALYSIS_CACHE[project_id]
    else:
        project_dir = (TEMP_UPLOADS_ROOT / project_id).resolve()
        report_file = project_dir / "analysis_report.json"
        if report_file.exists():
            try:
                data = json.loads(report_file.read_text(encoding="utf-8"))
                report = AnalysisReport(**data)
                ANALYSIS_CACHE[project_id] = report
            except Exception as e:
                logger.error(f"Failed loading report: {e}")

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis report for project '{project_id}' not found. Please run analysis first."
        )

    # 2. Generate PDF bytes
    try:
        pdf_bytes = generate_pdf_report(report)
    except Exception as e:
        logger.exception("PDF generation error")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {e}")

    filename = f"BugSense_Report_{report.project_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/api/project/{project_id}")
async def delete_project(project_id: str):
    """
    Removes the temporary extracted project directory and invalidates cached reports.
    """
    ANALYSIS_CACHE.pop(project_id, None)

    project_dir = (TEMP_UPLOADS_ROOT / project_id).resolve()
    if project_dir.exists() and project_dir.is_dir():
        try:
            shutil.rmtree(project_dir, ignore_errors=True)
            logger.info(f"Successfully deleted project directory: {project_id}")
            return {"status": "ok", "message": f"Project '{project_id}' deleted successfully."}
        except Exception as e:
            logger.error(f"Error removing project directory {project_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Could not delete project directory: {e}")

    return {"status": "ok", "message": f"Project '{project_id}' was not present on disk."}

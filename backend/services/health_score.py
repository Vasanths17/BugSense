"""
health_score.py
───────────────
Calculates a transparent Project Health Score (0–100) based on:
  1. Defect density penalty weighted by severity:
     - Critical: weight 20
     - High: weight 8
     - Medium: weight 3
     - Low: weight 1
     Normalized per 1,000 Lines of Code (KLOC) or per file count so large codebases
     are not unfairly penalized.
  2. Maintainability Index / Quality factor:
     - Average maintainability index across scanned files (scaled 0-100).
  3. Combined score:
     - Health Score = max(0, min(100, round(0.65 * QualityScore + 0.35 * DefectHealthScore)))
     - Letter grade: A (85-100), B (70-84), C (55-69), D (40-54), F (<40).
     - Status label: "Healthy", "Needs Attention", "At Risk", "Critical State".
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from models.finding import FileQualityMetrics, SeverityBreakdown


class HealthScoreDetails(BaseModel):
    score: int = Field(..., description="Project Health Score between 0 and 100")
    grade: str = Field(..., description="Letter grade: A, B, C, D, or F")
    status: str = Field(..., description="Health status label")
    defect_density_score: float = Field(..., description="Score based on weighted issues per 1,000 LOC (0-100)")
    quality_score: float = Field(..., description="Average maintainability/quality score (0-100)")
    total_loc: int = Field(..., description="Total lines of code scanned")
    explanation: str = Field(..., description="Brief breakdown of how score was determined")


def calculate_health_score(
    severity: SeverityBreakdown,
    file_metrics: List[FileQualityMetrics],
) -> HealthScoreDetails:
    # 1. Compute total LOC and average maintainability
    total_loc = sum(m.loc for m in file_metrics)
    if total_loc == 0:
        total_loc = max(1, len(file_metrics) * 50)  # fallback approximation if empty files

    kloc = max(0.2, total_loc / 1000.0)  # at least 0.2 KLOC (200 lines) base

    # 2. Defect weighted penalty
    # Weights: Critical=20, High=8, Medium=3, Low=1
    weighted_penalty = (
        (severity.critical * 20.0) +
        (severity.high * 8.0) +
        (severity.medium * 3.0) +
        (severity.low * 1.0)
    )

    penalty_per_kloc = weighted_penalty / kloc

    # Defect health score: 100 base, deducted by penalty_per_kloc
    defect_health = max(0.0, min(100.0, 100.0 - (penalty_per_kloc * 2.5)))

    # 3. Quality score from Maintainability Index
    mi_scores = [m.maintainability_index for m in file_metrics if m.maintainability_index is not None]
    if mi_scores:
        avg_mi = sum(mi_scores) / len(mi_scores)
    else:
        avg_mi = 85.0  # default good quality if no files or generic

    quality_score = max(0.0, min(100.0, avg_mi))

    # 4. Final Combined Health Score
    # 60% defect density & severity, 40% code maintainability
    combined = (0.60 * defect_health) + (0.40 * quality_score)
    final_score = int(round(max(0.0, min(100.0, combined))))

    # 5. Grade & Status mapping
    if final_score >= 85:
        grade = "A"
        status = "Healthy"
    elif final_score >= 70:
        grade = "B"
        status = "Good"
    elif final_score >= 55:
        grade = "C"
        status = "Needs Attention"
    elif final_score >= 40:
        grade = "D"
        status = "At Risk"
    else:
        grade = "F"
        status = "Critical"

    explanation = (
        f"Calculated from {severity.critical} Critical, {severity.high} High, {severity.medium} Medium, "
        f"and {severity.low} Low severity issues normalized across {total_loc:,} lines of code "
        f"combined with an average Maintainability Index of {quality_score:.1f}/100."
    )

    return HealthScoreDetails(
        score=final_score,
        grade=grade,
        status=status,
        defect_density_score=round(defect_health, 1),
        quality_score=round(quality_score, 1),
        total_loc=total_loc,
        explanation=explanation,
    )

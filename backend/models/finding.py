from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

ConfidenceLevel = Literal["Detected", "Potential"]
SeverityLevel = Literal["Critical", "High", "Medium", "Low"]
IssueCategory = Literal["Bug", "Security", "Code Quality"]


class RawFinding(BaseModel):
    rule_id: str = Field(..., description="Unique rule/linter code, e.g. 'F401', 'AST-SYNTAX', 'QUAL-COMPLEXITY'")
    tool: str = Field(..., description="Tool or analyzer that caught the issue (e.g. 'ruff', 'ast', 'bandit', 'radon', 'pattern-quality')")
    category: str = Field(default="Bug", description="Category: 'Bug', 'Security', or 'Code Quality'")
    file_path: str = Field(..., description="Relative file path within the project")
    line_number: int = Field(..., description="Line number of the issue (1-indexed)")
    column_number: Optional[int] = Field(None, description="Optional column/character offset")
    raw_message: str = Field(..., description="Original raw error or warning message")
    confidence: ConfidenceLevel = Field(
        ...,
        description="'Detected' for definite issues vs 'Potential' for heuristics/code smells"
    )
    code_snippet: Optional[str] = Field(None, description="Optional single line or snippet where the issue occurred")


class FunctionComplexity(BaseModel):
    name: str = Field(..., description="Name of the function or method")
    line_number: int = Field(..., description="Line number definition")
    complexity: int = Field(..., description="Cyclomatic complexity score")
    rank: str = Field(..., description="Complexity rank (A through F)")


class FileQualityMetrics(BaseModel):
    file_path: str = Field(..., description="Relative file path")
    language: str = Field(..., description="Detected programming language")
    loc: int = Field(..., description="Total lines of code")
    lloc: Optional[int] = Field(None, description="Logical lines of code")
    comments: Optional[int] = Field(0, description="Comment lines")
    blank_lines: Optional[int] = Field(0, description="Blank lines")
    cyclomatic_complexity: Optional[float] = Field(None, description="Average cyclomatic complexity")
    maintainability_index: Optional[float] = Field(None, description="Maintainability index (0-100)")
    maintainability_rank: Optional[str] = Field(None, description="Maintainability rank letter: A, B, C, or F")
    todo_count: int = Field(0, description="Count of TODO/FIXME markers")
    functions: List[FunctionComplexity] = Field(default_factory=list, description="Per-function complexity breakdown")


class QualityAnalysisResult(BaseModel):
    findings: List[RawFinding] = Field(default_factory=list, description="List of quality issues flagged as RawFinding")
    file_metrics: List[FileQualityMetrics] = Field(default_factory=list, description="Per-file code metrics summary")


class ExplainedIssue(BaseModel):
    id: str = Field(..., description="Unique generated issue ID (e.g. 'ISSUE-001')")
    rule_id: str = Field(..., description="Original rule or check code")
    tool: str = Field(..., description="Detection tool that raised the finding")
    title: str = Field(..., description="Clear human-readable title of the issue")
    category: IssueCategory = Field(..., description="Category: 'Bug', 'Security', or 'Code Quality'")
    file_name: str = Field(..., description="Relative path of file in project")
    line_number: Optional[int] = Field(None, description="Line number where issue is situated")
    explanation: str = Field(..., description="Simple, beginner-friendly explanation of what was found")
    why_it_matters: str = Field(..., description="Why the pattern or issue is problematic")
    possible_impact: str = Field(..., description="Concrete consequences if left unresolved")
    severity: SeverityLevel = Field(..., description="One of: 'Critical', 'High', 'Medium', 'Low'")
    recommendation: str = Field(..., description="Actionable instructions on how to fix the issue")
    detection_type: ConfidenceLevel = Field(..., description="'Detected' for verified vs 'Potential' for heuristics")
    code_snippet: Optional[str] = Field(None, description="Read-only context snippet (3-5 lines around line_number)")


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class CategoryBreakdown(BaseModel):
    bugs: int = 0
    security: int = 0
    quality: int = 0


class AnalysisReport(BaseModel):
    project_id: str
    project_name: str
    analyzed_at: str
    total_issues: int
    detected_count: int
    potential_count: int
    severity_breakdown: SeverityBreakdown
    category_breakdown: CategoryBreakdown
    issues: List[ExplainedIssue]
    file_metrics: List[FileQualityMetrics] = Field(default_factory=list)


class DetectionSummary(BaseModel):
    total_findings: int
    detected_count: int
    potential_count: int
    findings_by_tool: Dict[str, int]
    findings: List[RawFinding]
    file_metrics: Optional[List[FileQualityMetrics]] = None

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

ConfidenceLevel = Literal["Detected", "Potential"]


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


class DetectionSummary(BaseModel):
    total_findings: int
    detected_count: int
    potential_count: int
    findings_by_tool: Dict[str, int]
    findings: List[RawFinding]
    file_metrics: Optional[List[FileQualityMetrics]] = None

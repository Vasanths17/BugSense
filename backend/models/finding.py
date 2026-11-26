from pydantic import BaseModel, Field
from typing import List, Optional, Literal

ConfidenceLevel = Literal["Detected", "Potential"]


class RawFinding(BaseModel):
    rule_id: str = Field(..., description="Unique rule/linter code, e.g. 'F401', 'AST-SYNTAX', 'JS-VAR'")
    tool: str = Field(..., description="Tool or analyzer that caught the issue (e.g. 'ruff', 'ast', 'regex-js')")
    category: str = Field(default="Bug", description="Category of the finding (always 'Bug' for Feature 2)")
    file_path: str = Field(..., description="Relative file path within the project")
    line_number: int = Field(..., description="Line number of the issue (1-indexed)")
    column_number: Optional[int] = Field(None, description="Optional column/character offset")
    raw_message: str = Field(..., description="Original raw error or warning message")
    confidence: ConfidenceLevel = Field(
        ...,
        description="'Detected' for definite bugs/errors (syntax error, undefined variable, unused import) vs 'Potential' for heuristics/code smells (bare except, mutable default, loose equality)"
    )
    code_snippet: Optional[str] = Field(None, description="Optional single line or snippet where the issue occurred")


class DetectionSummary(BaseModel):
    total_findings: int
    detected_count: int
    potential_count: int
    findings_by_tool: dict[str, int]
    findings: List[RawFinding]

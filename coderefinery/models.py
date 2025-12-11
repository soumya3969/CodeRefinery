"""
Data models for CodeRefinery analysis results.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class StyleIssue:
    line: int
    code: str
    message: str
    suggestion: str
    severity: Severity = Severity.MEDIUM


@dataclass
class ComplexityMetric:
    name: str
    ccn: int
    lineno: int
    type: str = "function"


@dataclass
class BugReport:
    line: int
    message: str
    severity: Severity
    category: str = "general"


@dataclass
class FileAnalysis:
    path: str
    language: str
    style_issues: List[StyleIssue] = field(default_factory=list)
    complexity: Dict[str, Any] = field(default_factory=dict)
    bugs: List[BugReport] = field(default_factory=list)
    before_snippet: str = ""
    after_snippet: str = ""
    patch: Optional[str] = None
    
    def __post_init__(self):
        if not self.complexity:
            self.complexity = {
                "function_metrics": [],
                "avg_ccn": 0.0
            }


@dataclass
class OverallMetrics:
    total_issues: int
    high_severity: int
    files_analyzed: int
    complexity_violations: int = 0


@dataclass
class AnalysisResult:
    summary: str
    files: List[FileAnalysis] = field(default_factory=list)
    overall_metrics: OverallMetrics = field(default_factory=lambda: OverallMetrics(0, 0, 0))
    export: Dict[str, Any] = field(default_factory=dict)
    tool_status: str = "all tools available"
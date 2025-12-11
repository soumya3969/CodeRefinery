"""
CodeRefinery - AI Code Reviewer
An automated code-quality analyst and refactoring assistant.
"""

__version__ = "1.0.0"
__author__ = "CodeRefinery Team"

from .analyzer import CodeAnalyzer
from .models import AnalysisResult, FileAnalysis, StyleIssue, ComplexityMetric, BugReport

__all__ = [
    "CodeAnalyzer",
    "AnalysisResult", 
    "FileAnalysis",
    "StyleIssue",
    "ComplexityMetric", 
    "BugReport"
]
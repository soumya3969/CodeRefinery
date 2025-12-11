"""
Core code analysis engine for CodeRefinery.
"""
import ast
import re
import subprocess
import tempfile
from typing import List, Dict, Tuple, Optional, Set, Any
from pathlib import Path
import json

from .models import (
    AnalysisResult, FileAnalysis, StyleIssue, ComplexityMetric, 
    BugReport, OverallMetrics, Severity
)


class CodeAnalyzer:
    """Main code analysis engine."""
    
    def __init__(self, max_complexity_threshold: int = 10):
        self.max_complexity_threshold = max_complexity_threshold
        self.tools_available = self._check_tool_availability()
    
    def _check_tool_availability(self) -> Dict[str, bool]:
        """Check which code quality tools are available."""
        tools = {}
        for tool in ['flake8', 'black', 'radon']:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
                tools[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                tools[tool] = False
        return tools
    
    def analyze_files(self, files: List[Dict[str, str]], options: Dict = None) -> AnalysisResult:
        """
        Analyze multiple files and return comprehensive analysis results.
        
        Args:
            files: List of dicts with 'path', 'language', 'content' keys
            options: Analysis options (apply_black, max_complexity_threshold, export_formats)
        """
        if options is None:
            options = {}
        
        # Update threshold if provided
        if 'max_complexity_threshold' in options:
            self.max_complexity_threshold = options['max_complexity_threshold']
        
        analyzed_files = []
        total_issues = 0
        high_severity_count = 0
        complexity_violations = 0
        
        for file_data in files:
            if file_data.get('language') != 'python':
                continue
                
            file_analysis = self._analyze_single_file(
                file_data['path'], 
                file_data['content'],
                options.get('apply_black', False)
            )
            
            analyzed_files.append(file_analysis)
            total_issues += len(file_analysis.style_issues) + len(file_analysis.bugs)
            high_severity_count += sum(1 for issue in file_analysis.style_issues 
                                     if issue.severity == Severity.HIGH)
            high_severity_count += sum(1 for bug in file_analysis.bugs 
                                     if bug.severity == Severity.HIGH)
            
            # Count complexity violations
            for metric in file_analysis.complexity.get('function_metrics', []):
                if metric.get('ccn', 0) > self.max_complexity_threshold:
                    complexity_violations += 1
        
        overall_metrics = OverallMetrics(
            total_issues=total_issues,
            high_severity=high_severity_count,
            files_analyzed=len(analyzed_files),
            complexity_violations=complexity_violations
        )
        
        summary = self._generate_summary(overall_metrics, analyzed_files)
        
        result = AnalysisResult(
            summary=summary,
            files=analyzed_files,
            overall_metrics=overall_metrics,
            tool_status=self._get_tool_status()
        )
        
        # Generate export formats if requested
        if 'export_formats' in options:
            result.export = self._generate_exports(result, options['export_formats'])
        
        return result
    
    def _analyze_single_file(self, path: str, content: str, apply_black: bool = False) -> FileAnalysis:
        """Analyze a single Python file."""
        file_analysis = FileAnalysis(path=path, language="python")
        
        # Step 1: Style analysis
        file_analysis.style_issues = self._analyze_style(content)
        
        # Step 2: Formatting analysis
        formatted_content, formatting_issues = self._analyze_formatting(content, apply_black)
        file_analysis.style_issues.extend(formatting_issues)
        
        # Step 3: Complexity measurement
        file_analysis.complexity = self._analyze_complexity(content)
        
        # Step 4: Bug detection
        file_analysis.bugs = self._detect_bugs(content)
        
        # Step 5: Generate before/after snippets
        file_analysis.before_snippet = self._extract_snippet(content)
        if formatted_content != content:
            file_analysis.after_snippet = self._extract_snippet(formatted_content)
            file_analysis.patch = self._generate_patch(content, formatted_content, path)
        else:
            file_analysis.after_snippet = file_analysis.before_snippet
        
        return file_analysis
    
    def _analyze_style(self, content: str) -> List[StyleIssue]:
        """Analyze code style issues."""
        issues = []
        lines = content.split('\n')
        
        # Use flake8 if available, otherwise heuristic analysis
        if self.tools_available.get('flake8', False):
            issues.extend(self._run_flake8(content))
        else:
            issues.extend(self._heuristic_style_analysis(lines))
        
        return issues
    
    def _run_flake8(self, content: str) -> List[StyleIssue]:
        """Run flake8 analysis."""
        issues = []
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                f.flush()
                
                result = subprocess.run(
                    ['flake8', '--format=%(row)d:%(col)d:%(code)s:%(text)s', f.name],
                    capture_output=True, text=True
                )
                
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            row, col, code, message = parts
                            issues.append(StyleIssue(
                                line=int(row),
                                code=code,
                                message=message.strip(),
                                suggestion=self._get_style_suggestion(code),
                                severity=self._get_style_severity(code)
                            ))
        except Exception as e:
            # Fallback to heuristic analysis
            return self._heuristic_style_analysis(content.split('\n'))
        
        return issues
    
    def _heuristic_style_analysis(self, lines: List[str]) -> List[StyleIssue]:
        """Perform heuristic style analysis when flake8 is not available."""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 79:
                issues.append(StyleIssue(
                    line=i,
                    code="E501",
                    message=f"line too long ({len(line)} > 79 characters)",
                    suggestion="break line into multiple lines"
                ))
            
            # Check for multiple spaces after comma
            if re.search(r',\s{2,}', line):
                issues.append(StyleIssue(
                    line=i,
                    code="E241",
                    message="multiple spaces after ','",
                    suggestion="use single space after comma"
                ))
            
            # Check for missing spaces around operators
            if re.search(r'\w[=+\-*/]\w', line) and 'def ' not in line:
                issues.append(StyleIssue(
                    line=i,
                    code="E225",
                    message="missing whitespace around operator",
                    suggestion="add spaces around operators"
                ))
            
            # Check for trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(StyleIssue(
                    line=i,
                    code="W291",
                    message="trailing whitespace",
                    suggestion="remove trailing whitespace"
                ))
        
        return issues
    
    def _analyze_formatting(self, content: str, apply_black: bool) -> Tuple[str, List[StyleIssue]]:
        """Analyze code formatting with black."""
        formatting_issues = []
        formatted_content = content
        
        if self.tools_available.get('black', False):
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(content)
                    f.flush()
                    
                    # Check what black would change
                    result = subprocess.run(
                        ['black', '--diff', f.name],
                        capture_output=True, text=True
                    )
                    
                    if result.stdout and result.stdout.strip():
                        formatting_issues.append(StyleIssue(
                            line=1,
                            code="BLACK",
                            message="code formatting can be improved",
                            suggestion="run black formatter",
                            severity=Severity.LOW
                        ))
                        
                        if apply_black:
                            # Apply black formatting
                            subprocess.run(['black', f.name], check=True)
                            with open(f.name, 'r') as formatted_f:
                                formatted_content = formatted_f.read()
                                
            except Exception:
                pass
        else:
            # Heuristic formatting analysis
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip() and (line.startswith(' ') and not line.startswith('    ')):
                    if not any(line.startswith(' ' * j) for j in [2, 6, 8]):
                        formatting_issues.append(StyleIssue(
                            line=i,
                            code="E111",
                            message="indentation is not a multiple of four",
                            suggestion="use 4-space indentation"
                        ))
        
        return formatted_content, formatting_issues
    
    def _analyze_complexity(self, content: str) -> Dict:
        """Analyze code complexity."""
        complexity_data = {
            "function_metrics": [],
            "avg_ccn": 0.0
        }
        
        if self.tools_available.get('radon', False):
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(content)
                    f.flush()
                    
                    result = subprocess.run(
                        ['radon', 'cc', '--json', f.name],
                        capture_output=True, text=True
                    )
                    
                    if result.stdout:
                        radon_data = json.loads(result.stdout)
                        for file_data in radon_data.values():
                            for func_data in file_data:
                                complexity_data["function_metrics"].append({
                                    "name": func_data["name"],
                                    "ccn": func_data["complexity"],
                                    "lineno": func_data["lineno"]
                                })
                        
                        if complexity_data["function_metrics"]:
                            avg_ccn = sum(m["ccn"] for m in complexity_data["function_metrics"]) / len(complexity_data["function_metrics"])
                            complexity_data["avg_ccn"] = round(avg_ccn, 2)
                            
            except Exception:
                complexity_data = self._heuristic_complexity_analysis(content)
        else:
            complexity_data = self._heuristic_complexity_analysis(content)
        
        return complexity_data
    
    def _heuristic_complexity_analysis(self, content: str) -> Dict:
        """Perform heuristic complexity analysis when radon is not available."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {"function_metrics": [], "avg_ccn": 0.0}
        
        function_metrics = []
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self, parent):
                self.parent = parent
            
            def visit_FunctionDef(self, node):
                ccn = self.parent._calculate_ccn(node)
                function_metrics.append({
                    "name": node.name,
                    "ccn": ccn,
                    "lineno": node.lineno
                })
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
        
        visitor = ComplexityVisitor(self)
        visitor.visit(tree)
        
        avg_ccn = 0.0
        if function_metrics:
            avg_ccn = sum(m["ccn"] for m in function_metrics) / len(function_metrics)
            avg_ccn = round(avg_ccn, 2)
        
        return {
            "function_metrics": function_metrics,
            "avg_ccn": avg_ccn
        }
    
    def _calculate_ccn(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.ExceptHandler,)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                for generator in child.generators:
                    complexity += 1
                    complexity += len(generator.ifs)
        
        return complexity
    
    def _detect_bugs(self, content: str) -> List[BugReport]:
        """Detect potential bugs and unsafe patterns."""
        bugs = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            bugs.append(BugReport(
                line=e.lineno or 1,
                message=f"Syntax error: {e.msg}",
                severity=Severity.HIGH,
                category="syntax"
            ))
            return bugs
        
        # Check for common bug patterns
        bugs.extend(self._check_mutable_defaults(tree))
        bugs.extend(self._check_bare_except(tree))
        bugs.extend(self._check_unused_variables(tree, content))
        bugs.extend(self._check_security_issues(tree, content))
        
        return bugs
    
    def _check_mutable_defaults(self, tree: ast.AST) -> List[BugReport]:
        """Check for mutable default arguments."""
        bugs = []
        
        class MutableDefaultVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        bugs.append(BugReport(
                            line=node.lineno,
                            message="Dangerous default value {} (mutable default argument)".format(
                                "[]" if isinstance(arg, ast.List) else "{}" if isinstance(arg, ast.Dict) else "set()"
                            ),
                            severity=Severity.HIGH,
                            category="mutable_default"
                        ))
                self.generic_visit(node)
        
        visitor = MutableDefaultVisitor()
        visitor.visit(tree)
        return bugs
    
    def _check_bare_except(self, tree: ast.AST) -> List[BugReport]:
        """Check for bare except clauses."""
        bugs = []
        
        class BareExceptVisitor(ast.NodeVisitor):
            def visit_ExceptHandler(self, node):
                if node.type is None:
                    bugs.append(BugReport(
                        line=node.lineno,
                        message="Bare except clause - catches all exceptions including KeyboardInterrupt",
                        severity=Severity.MEDIUM,
                        category="exception_handling"
                    ))
                self.generic_visit(node)
        
        visitor = BareExceptVisitor()
        visitor.visit(tree)
        return bugs
    
    def _check_unused_variables(self, tree: ast.AST, content: str) -> List[BugReport]:
        """Check for unused variables (simplified)."""
        bugs = []
        lines = content.split('\n')
        
        # Simple regex-based check for obvious unused variables
        for i, line in enumerate(lines, 1):
            if '=' in line and not line.strip().startswith('#'):
                # Look for simple assignments
                match = re.match(r'\s*(\w+)\s*=', line)
                if match:
                    var_name = match.group(1)
                    if var_name not in ['_', '__'] and var_name.islower():
                        # Check if variable is used later (simple check)
                        remaining_content = '\n'.join(lines[i:])
                        if var_name not in remaining_content:
                            bugs.append(BugReport(
                                line=i,
                                message=f"Variable '{var_name}' assigned but never used",
                                severity=Severity.LOW,
                                category="unused_variable"
                            ))
        
        return bugs
    
    def _check_security_issues(self, tree: ast.AST, content: str) -> List[BugReport]:
        """Check for basic security issues."""
        bugs = []
        
        # Check for eval/exec usage
        if 'eval(' in content:
            line_num = next((i+1 for i, line in enumerate(content.split('\n')) if 'eval(' in line), 1)
            bugs.append(BugReport(
                line=line_num,
                message="Use of eval() is dangerous and should be avoided",
                severity=Severity.HIGH,
                category="security"
            ))
        
        if 'exec(' in content:
            line_num = next((i+1 for i, line in enumerate(content.split('\n')) if 'exec(' in line), 1)
            bugs.append(BugReport(
                line=line_num,
                message="Use of exec() is dangerous and should be avoided",
                severity=Severity.HIGH,
                category="security"
            ))
        
        return bugs
    
    def _extract_snippet(self, content: str, max_lines: int = 20) -> str:
        """Extract a representative snippet from the content."""
        lines = content.split('\n')
        if len(lines) <= max_lines:
            return content
        
        # Try to get a meaningful snippet
        for i, line in enumerate(lines):
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                end_idx = min(i + max_lines, len(lines))
                return '\n'.join(lines[i:end_idx])
        
        # Fallback to first N lines
        return '\n'.join(lines[:max_lines])
    
    def _generate_patch(self, original: str, modified: str, path: str) -> str:
        """Generate unified diff patch."""
        try:
            import difflib
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}"
            )
            return ''.join(diff)
        except Exception:
            return None
    
    def _generate_summary(self, metrics: OverallMetrics, files: List[FileAnalysis]) -> str:
        """Generate executive summary."""
        summary_parts = [
            f"Analyzed {metrics.files_analyzed} Python files",
            f"Found {metrics.total_issues} total issues"
        ]
        
        if metrics.high_severity > 0:
            summary_parts.append(f"{metrics.high_severity} high-severity issues require immediate attention")
        
        if metrics.complexity_violations > 0:
            summary_parts.append(f"{metrics.complexity_violations} functions exceed complexity threshold")
        
        if metrics.total_issues == 0:
            summary_parts.append("Code quality looks good!")
        
        return ". ".join(summary_parts) + "."
    
    def _get_tool_status(self) -> str:
        """Get status of available tools."""
        missing_tools = [tool for tool, available in self.tools_available.items() if not available]
        if missing_tools:
            return f"Tools not available: {', '.join(missing_tools)} - using heuristic analysis"
        return "all tools available"
    
    def _get_style_suggestion(self, code: str) -> str:
        """Get suggestion for style issue code."""
        suggestions = {
            "E501": "break line into multiple lines or increase line length limit",
            "E225": "add spaces around operators",
            "E231": "add space after comma",
            "E241": "use single space after comma",
            "W291": "remove trailing whitespace",
            "E111": "use 4-space indentation",
            "E301": "add blank line before function/class definition"
        }
        return suggestions.get(code, "refer to PEP8 style guide")
    
    def _get_style_severity(self, code: str) -> Severity:
        """Get severity level for style issue code."""
        high_severity = {"E901", "E999"}  # Syntax errors
        low_severity = {"W291", "W292", "W293"}  # Whitespace issues
        
        if code in high_severity:
            return Severity.HIGH
        elif code in low_severity:
            return Severity.LOW
        else:
            return Severity.MEDIUM
    
    def _generate_exports(self, result: AnalysisResult, formats: List[str]) -> Dict[str, Any]:
        """Generate export formats."""
        exports = {}
        
        if "markdown" in formats:
            exports["markdown"] = self._generate_markdown_report(result)
        
        if "json" in formats:
            exports["json"] = self._serialize_result(result)
        
        return exports
    
    def _generate_markdown_report(self, result: AnalysisResult) -> str:
        """Generate markdown report."""
        md_lines = [
            "# CodeRefinery Analysis Report\n",
            f"## Summary\n{result.summary}\n",
            f"## Overall Metrics",
            f"- Files analyzed: {result.overall_metrics.files_analyzed}",
            f"- Total issues: {result.overall_metrics.total_issues}",
            f"- High severity issues: {result.overall_metrics.high_severity}",
            f"- Complexity violations: {result.overall_metrics.complexity_violations}\n"
        ]
        
        for file_analysis in result.files:
            md_lines.extend([
                f"## File: {file_analysis.path}",
                f"### Style Issues ({len(file_analysis.style_issues)})"
            ])
            
            for issue in file_analysis.style_issues:
                md_lines.append(f"- Line {issue.line}: {issue.message} ({issue.code})")
            
            if file_analysis.bugs:
                md_lines.append(f"\n### Potential Bugs ({len(file_analysis.bugs)})")
                for bug in file_analysis.bugs:
                    md_lines.append(f"- Line {bug.line}: {bug.message} [{bug.severity.value}]")
            
            complexity_metrics = file_analysis.complexity.get('function_metrics', [])
            if complexity_metrics:
                md_lines.append(f"\n### Complexity Metrics")
                for metric in complexity_metrics:
                    md_lines.append(f"- {metric['name']} (line {metric['lineno']}): CCN = {metric['ccn']}")
                md_lines.append(f"- Average CCN: {file_analysis.complexity.get('avg_ccn', 0)}")
            
            md_lines.append("")
        
        if result.tool_status != "all tools available":
            md_lines.append(f"\n---\n*Note: {result.tool_status}*")
        
        return "\n".join(md_lines)
    
    def _serialize_result(self, result: AnalysisResult) -> Dict:
        """Convert result to JSON-serializable format."""
        return {
            "summary": result.summary,
            "files": [
                {
                    "path": f.path,
                    "language": f.language,
                    "style_issues": [
                        {
                            "line": issue.line,
                            "code": issue.code,
                            "message": issue.message,
                            "suggestion": issue.suggestion
                        }
                        for issue in f.style_issues
                    ],
                    "complexity": f.complexity,
                    "bugs": [
                        {
                            "line": bug.line,
                            "message": bug.message,
                            "severity": bug.severity.value
                        }
                        for bug in f.bugs
                    ],
                    "before_snippet": f.before_snippet,
                    "after_snippet": f.after_snippet,
                    "patch": f.patch
                }
                for f in result.files
            ],
            "overall_metrics": {
                "total_issues": result.overall_metrics.total_issues,
                "high_severity": result.overall_metrics.high_severity,
                "files_analyzed": result.overall_metrics.files_analyzed
            },
            "export": result.export
        }
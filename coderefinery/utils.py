"""
Utility functions for CodeRefinery.
"""
import re
import ast
from typing import List, Dict, Tuple, Optional


def extract_functions(content: str) -> List[Dict[str, any]]:
    """Extract function definitions from Python code."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    
    functions = []
    
    class FunctionVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            functions.append({
                'name': node.name,
                'lineno': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'docstring': ast.get_docstring(node),
                'is_async': False
            })
            self.generic_visit(node)
        
        def visit_AsyncFunctionDef(self, node):
            functions.append({
                'name': node.name,
                'lineno': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'docstring': ast.get_docstring(node),
                'is_async': True
            })
            self.generic_visit(node)
    
    visitor = FunctionVisitor()
    visitor.visit(tree)
    return functions


def extract_classes(content: str) -> List[Dict[str, any]]:
    """Extract class definitions from Python code."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    
    classes = []
    
    class ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'lineno': item.lineno,
                        'is_async': False
                    })
                elif isinstance(item, ast.AsyncFunctionDef):
                    methods.append({
                        'name': item.name,
                        'lineno': item.lineno,
                        'is_async': True
                    })
            
            classes.append({
                'name': node.name,
                'lineno': node.lineno,
                'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else 'Unknown' for base in node.bases],
                'methods': methods,
                'docstring': ast.get_docstring(node)
            })
            self.generic_visit(node)
    
    visitor = ClassVisitor()
    visitor.visit(tree)
    return classes


def extract_imports(content: str) -> Dict[str, List[str]]:
    """Extract import statements from Python code."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {'imports': [], 'from_imports': []}
    
    imports = []
    from_imports = []
    
    class ImportVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                imports.append({
                    'module': alias.name,
                    'alias': alias.asname,
                    'lineno': node.lineno
                })
        
        def visit_ImportFrom(self, node):
            module = node.module or ''
            for alias in node.names:
                from_imports.append({
                    'module': module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'lineno': node.lineno,
                    'level': node.level
                })
    
    visitor = ImportVisitor()
    visitor.visit(tree)
    
    return {
        'imports': imports,
        'from_imports': from_imports
    }


def get_code_metrics(content: str) -> Dict[str, any]:
    """Get basic code metrics."""
    lines = content.split('\n')
    
    metrics = {
        'total_lines': len(lines),
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0,
        'string_literals': 0
    }
    
    in_multiline_string = False
    multiline_delimiter = None
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            metrics['blank_lines'] += 1
        elif stripped.startswith('#'):
            metrics['comment_lines'] += 1
        else:
            # Check for multiline strings
            if not in_multiline_string:
                if '"""' in line:
                    multiline_delimiter = '"""'
                    in_multiline_string = True
                    if line.count('"""') >= 2:
                        in_multiline_string = False
                elif "'''" in line:
                    multiline_delimiter = "'''"
                    in_multiline_string = True
                    if line.count("'''") >= 2:
                        in_multiline_string = False
                else:
                    metrics['code_lines'] += 1
            else:
                if multiline_delimiter in line:
                    in_multiline_string = False
                    multiline_delimiter = None
                metrics['string_literals'] += 1
    
    if metrics['total_lines'] > 0:
        metrics['code_percentage'] = round(metrics['code_lines'] / metrics['total_lines'] * 100, 1)
        metrics['comment_percentage'] = round(metrics['comment_lines'] / metrics['total_lines'] * 100, 1)
    else:
        metrics['code_percentage'] = 0
        metrics['comment_percentage'] = 0
    
    return metrics


def validate_python_syntax(content: str) -> Tuple[bool, Optional[str]]:
    """Validate Python syntax."""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def suggest_refactoring(content: str, complexity_threshold: int = 10) -> List[Dict[str, any]]:
    """Suggest refactoring opportunities."""
    suggestions = []
    
    # Extract functions for analysis
    functions = extract_functions(content)
    
    for func in functions:
        # Suggest refactoring for long parameter lists
        if len(func['args']) > 5:
            suggestions.append({
                'type': 'parameter_list',
                'function': func['name'],
                'line': func['lineno'],
                'message': f"Function '{func['name']}' has {len(func['args'])} parameters. Consider using a configuration object or reducing parameters.",
                'severity': 'medium'
            })
        
        # Suggest adding docstrings
        if not func['docstring']:
            suggestions.append({
                'type': 'documentation',
                'function': func['name'],
                'line': func['lineno'],
                'message': f"Function '{func['name']}' lacks a docstring. Consider adding documentation.",
                'severity': 'low'
            })
    
    # Extract classes for analysis
    classes = extract_classes(content)
    
    for cls in classes:
        # Suggest adding docstrings to classes
        if not cls['docstring']:
            suggestions.append({
                'type': 'documentation',
                'class': cls['name'],
                'line': cls['lineno'],
                'message': f"Class '{cls['name']}' lacks a docstring. Consider adding documentation.",
                'severity': 'low'
            })
        
        # Check for classes with too many methods
        if len(cls['methods']) > 20:
            suggestions.append({
                'type': 'class_size',
                'class': cls['name'],
                'line': cls['lineno'],
                'message': f"Class '{cls['name']}' has {len(cls['methods'])} methods. Consider splitting into smaller classes.",
                'severity': 'medium'
            })
    
    # Check for long files
    lines = content.split('\n')
    if len(lines) > 500:
        suggestions.append({
            'type': 'file_size',
            'line': 1,
            'message': f"File has {len(lines)} lines. Consider splitting into multiple modules.",
            'severity': 'medium'
        })
    
    return suggestions


def generate_fix_suggestions(issue_type: str, context: Dict) -> str:
    """Generate specific fix suggestions for different issue types."""
    fixes = {
        'mutable_default': """
Replace mutable default argument with None and initialize inside function:

Before:
def func(items=[]):
    items.append(1)
    return items

After:
def func(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
""",
        'bare_except': """
Use specific exception types instead of bare except:

Before:
try:
    risky_operation()
except:
    handle_error()

After:
try:
    risky_operation()
except ValueError as e:
    handle_error(e)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
""",
        'long_line': """
Break long lines using parentheses or backslashes:

Before:
result = some_function(arg1, arg2, arg3, arg4, arg5, arg6)

After:
result = some_function(
    arg1, arg2, arg3,
    arg4, arg5, arg6
)
""",
        'missing_spaces': """
Add spaces around operators for better readability:

Before:
x=y+z*2

After:
x = y + z * 2
""",
    }
    
    return fixes.get(issue_type, "Refer to PEP8 style guide for best practices.")


def calculate_maintainability_index(content: str) -> float:
    """Calculate a simple maintainability index."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return 0.0
    
    # Basic metrics
    lines = content.split('\n')
    total_lines = len([line for line in lines if line.strip()])
    
    if total_lines == 0:
        return 100.0
    
    # Count various constructs
    functions = len(extract_functions(content))
    classes = len(extract_classes(content))
    
    # Simple scoring (higher is better)
    score = 100.0
    
    # Penalize large files
    if total_lines > 500:
        score -= (total_lines - 500) / 50
    
    # Reward modular code
    if functions > 0:
        score += min(functions * 2, 20)
    if classes > 0:
        score += min(classes * 5, 25)
    
    # Check for comments
    comment_lines = len([line for line in lines if line.strip().startswith('#')])
    comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
    if comment_ratio > 0.1:
        score += 10
    
    return max(0, min(100, score))


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
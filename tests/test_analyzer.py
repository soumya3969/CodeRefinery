"""
Test module for CodeRefinery analyzer.
"""
import pytest
from coderefinery.analyzer import CodeAnalyzer
from coderefinery.models import Severity


class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CodeAnalyzer(max_complexity_threshold=10)
    
    def test_simple_code_analysis(self):
        """Test analysis of simple Python code."""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        assert result.overall_metrics.files_analyzed == 1
        assert isinstance(result.summary, str)
        assert len(result.files) == 1
    
    def test_mutable_default_detection(self):
        """Test detection of mutable default arguments."""
        code = """
def add_items(items, new_items=[]):
    items.extend(new_items)
    return items
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        # Should detect mutable default argument
        bugs = result.files[0].bugs
        assert any(bug.category == "mutable_default" for bug in bugs)
        assert any(bug.severity == Severity.HIGH for bug in bugs)
    
    def test_complexity_analysis(self):
        """Test complexity analysis."""
        code = """
def complex_function(x):
    if x > 10:
        if x > 20:
            if x > 30:
                if x > 40:
                    if x > 50:
                        return "very high"
                    else:
                        return "high"
                else:
                    return "medium-high"
            else:
                return "medium"
        else:
            return "low-medium"
    else:
        return "low"
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        complexity = result.files[0].complexity
        assert len(complexity['function_metrics']) > 0
        
        # Function should have high complexity
        func_metric = complexity['function_metrics'][0]
        assert func_metric['name'] == 'complex_function'
        assert func_metric['ccn'] > 5  # Should be complex
    
    def test_style_issues(self):
        """Test style issue detection."""
        code = """
def  bad_style( x,y ):
  return x+y
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        # Should detect style issues
        assert len(result.files[0].style_issues) > 0
    
    def test_bare_except_detection(self):
        """Test detection of bare except clauses."""
        code = """
def risky_function():
    try:
        dangerous_operation()
    except:
        pass
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        # Should detect bare except
        bugs = result.files[0].bugs
        assert any("bare except" in bug.message.lower() for bug in bugs)
    
    def test_security_issues(self):
        """Test detection of security issues."""
        code = """
def unsafe_function(user_input):
    result = eval(user_input)
    return result
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        # Should detect eval usage
        bugs = result.files[0].bugs
        assert any("eval" in bug.message.lower() for bug in bugs)
        assert any(bug.severity == Severity.HIGH for bug in bugs)
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        code = """
def broken_function(
    print("Missing closing parenthesis")
"""
        files = [{"path": "test.py", "language": "python", "content": code}]
        result = self.analyzer.analyze_files(files)
        
        # Should detect syntax error
        bugs = result.files[0].bugs
        assert any("syntax error" in bug.message.lower() for bug in bugs)
    
    def test_empty_files_handling(self):
        """Test handling of empty files."""
        files = []
        result = self.analyzer.analyze_files(files)
        
        assert result.overall_metrics.files_analyzed == 0
        assert result.overall_metrics.total_issues == 0
    
    def test_multiple_files(self):
        """Test analysis of multiple files."""
        file1 = {
            "path": "module1.py",
            "language": "python", 
            "content": "def func1(): pass"
        }
        file2 = {
            "path": "module2.py",
            "language": "python",
            "content": "def func2(): return 42"
        }
        
        result = self.analyzer.analyze_files([file1, file2])
        
        assert result.overall_metrics.files_analyzed == 2
        assert len(result.files) == 2
    
    def test_options_handling(self):
        """Test handling of analysis options."""
        code = "def test(): pass"
        files = [{"path": "test.py", "language": "python", "content": code}]
        
        options = {
            "max_complexity_threshold": 5,
            "apply_black": False,
            "export_formats": ["markdown", "json"]
        }
        
        result = self.analyzer.analyze_files(files, options)
        
        assert "markdown" in result.export
        assert "json" in result.export
        assert self.analyzer.max_complexity_threshold == 5


@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
def calculate_grade(scores):
    '''Calculate letter grade from numeric scores.'''
    if not scores:
        return 'F'
    
    average = sum(scores) / len(scores)
    
    if average >= 90:
        return 'A'
    elif average >= 80:
        return 'B'
    elif average >= 70:
        return 'C'
    elif average >= 60:
        return 'D'
    else:
        return 'F'


class Student:
    '''Represents a student with grades.'''
    
    def __init__(self, name, scores=[]):  # Mutable default!
        self.name = name
        self.scores = scores
    
    def add_score(self, score):
        self.scores.append(score)
    
    def get_grade(self):
        return calculate_grade(self.scores)
"""


def test_comprehensive_analysis(sample_code):
    """Test comprehensive analysis with sample code."""
    analyzer = CodeAnalyzer()
    files = [{"path": "student.py", "language": "python", "content": sample_code}]
    result = analyzer.analyze_files(files)
    
    # Should find the mutable default argument bug
    bugs = result.files[0].bugs
    assert any("mutable" in bug.message.lower() for bug in bugs)
    
    # Should analyze complexity
    complexity = result.files[0].complexity
    assert len(complexity['function_metrics']) >= 2  # At least 2 functions
    
    # Should have overall metrics
    assert result.overall_metrics.files_analyzed == 1
    assert result.overall_metrics.total_issues > 0
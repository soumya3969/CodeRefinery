"""
Example scripts demonstrating CodeRefinery usage.
"""
from coderefinery.analyzer import CodeAnalyzer


def example_analysis():
    """Run example code analysis."""
    
    # Sample problematic code
    sample_code = """
def add_items(items, new_items=[]):  # Mutable default!
    for item in new_items:
        items.append(item)
    return items

def complex_function(x, y, z, a, b, c, d):
    if x > 10:
        if y > 20:
            if z > 30:
                if a > 40:
                    if b > 50:
                        if c > 60:
                            if d > 70:
                                return "very complex"
                            else:
                                return "complex"
                        else:
                            return "medium"
                    else:
                        return "simple"
                else:
                    return "basic"
            else:
                return "trivial"
        else:
            return "minimal"
    else:
        return "none"

def unsafe_function(user_input):
    return eval(user_input)  # Security risk!

class Student:
    def __init__(self, name, grades=[]):  # Another mutable default!
        self.name = name
        self.grades = grades
    
    def add_grade(self, grade):
        self.grades.append(grade)
"""
    
    # Create analyzer
    analyzer = CodeAnalyzer(max_complexity_threshold=8)
    
    # Analyze the code
    files = [{
        "path": "problematic_code.py",
        "language": "python",
        "content": sample_code
    }]
    
    options = {
        "apply_black": False,
        "max_complexity_threshold": 8,
        "export_formats": ["markdown", "json"]
    }
    
    result = analyzer.analyze_files(files, options)
    
    # Print results
    print("=" * 60)
    print("CodeRefinery Analysis Results")
    print("=" * 60)
    print(f"Summary: {result.summary}")
    print()
    
    print("Overall Metrics:")
    print(f"- Files analyzed: {result.overall_metrics.files_analyzed}")
    print(f"- Total issues: {result.overall_metrics.total_issues}")
    print(f"- High severity: {result.overall_metrics.high_severity}")
    print(f"- Complexity violations: {result.overall_metrics.complexity_violations}")
    print()
    
    # Show file analysis
    for file_analysis in result.files:
        print(f"File: {file_analysis.path}")
        print("-" * 40)
        
        if file_analysis.style_issues:
            print("Style Issues:")
            for issue in file_analysis.style_issues:
                print(f"  Line {issue.line}: [{issue.code}] {issue.message}")
        
        if file_analysis.bugs:
            print("Potential Bugs:")
            for bug in file_analysis.bugs:
                print(f"  Line {bug.line}: [{bug.severity.value.upper()}] {bug.message}")
        
        complexity_metrics = file_analysis.complexity.get('function_metrics', [])
        if complexity_metrics:
            print("Complexity Metrics:")
            for metric in complexity_metrics:
                warning = " ⚠️" if metric['ccn'] > options['max_complexity_threshold'] else ""
                print(f"  {metric['name']} (line {metric['lineno']}): CCN = {metric['ccn']}{warning}")
        
        print()
    
    return result


if __name__ == "__main__":
    example_analysis()
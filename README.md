# 🔍 CodeRefinery

**AI-Powered Code Quality Analyzer and Refactoring Assistant**

CodeRefinery is a comprehensive code analysis tool that helps you identify style issues, complexity problems, potential bugs, and provides automated refactoring suggestions for Python code. Built with modern AI techniques and following established best practices like PEP8, flake8, black, and radon.

## ✨ Features

- **Style Analysis**: PEP8/flake8-compatible style checking with detailed suggestions
- **Code Formatting**: Black-style formatting analysis and auto-fixing
- **Complexity Measurement**: Cyclomatic complexity analysis with configurable thresholds
- **Bug Detection**: Identifies potential runtime issues, security vulnerabilities, and anti-patterns
- **Refactoring Suggestions**: Actionable recommendations with before/after examples
- **Multiple Interfaces**: CLI tool, Streamlit web app, and Python API
- **Export Formats**: Markdown and JSON reports for integration and documentation

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/coderefinery/coderefinery.git
cd coderefinery
pip install -e .

# Install with optional dependencies
pip install -e ".[dev,tools]"
```

### Command Line Usage

```bash
# Analyze specific files
coderefinery analyze app.py utils.py

# Analyze with options
coderefinery analyze --max-complexity 15 --apply-black --export markdown,json app.py

# Use JSON input
coderefinery analyze --input config.json

# Show help
coderefinery --help
```

### Web Interface

```bash
# Launch Streamlit web app
streamlit run coderefinery/web_app.py

# Or access via your browser at http://localhost:8501
```

### Python API

```python
from coderefinery.analyzer import CodeAnalyzer

# Create analyzer
analyzer = CodeAnalyzer(max_complexity_threshold=10)

# Analyze files
files = [{
    "path": "example.py",
    "language": "python", 
    "content": "def hello(): print('world')"
}]

result = analyzer.analyze_files(files, {
    "apply_black": False,
    "export_formats": ["markdown", "json"]
})

print(result.summary)
```

## 📊 Analysis Types

### 1. Style Analysis (PEP8/flake8 Compatible)
- **Line length violations** (E501): Lines exceeding 79 characters
- **Spacing issues**: Missing whitespace around operators (E225), after commas (E231)
- **Indentation problems** (E111): Non-standard indentation
- **Trailing whitespace** (W291): Unnecessary trailing spaces
- **Missing blank lines** (E301, E302): Required spacing around functions/classes

### 2. Bug Detection & Security
- **Mutable default arguments**: Dangerous `def func(arg=[]):` patterns (HIGH severity)
- **Bare except clauses**: `except:` without specific exception types (MEDIUM severity)
- **Security issues**: Usage of `eval()` and `exec()` functions (HIGH severity)
- **Unused variables**: Variables assigned but never used (LOW severity)
- **Syntax errors**: Code that won't parse correctly (HIGH severity)

### 3. Complexity Metrics
- **Cyclomatic complexity** per function with line numbers
- **Average complexity** per file
- **Configurable thresholds** (default: 10)
- **Radon-compatible** CCN (Cyclomatic Complexity Number) reporting

### 4. Refactoring Suggestions
- **Parameter list optimization**: Functions with too many parameters
- **Documentation improvements**: Missing docstrings
- **Code structure recommendations**: Large classes/files
- **Security enhancements**: Safer alternatives to dangerous patterns

## 🛠️ Configuration

### JSON Input Format

```json
{
  "files": [
    {
      "path": "app.py",
      "language": "python",
      "content": "def example():\n    return True"
    }
  ],
  "options": {
    "apply_black": false,
    "max_complexity_threshold": 10,
    "export_formats": ["markdown", "json"]
  }
}
```

### CLI Options

- `--max-complexity N`: Set complexity threshold (default: 10)
- `--apply-black`: Apply black formatting automatically
- `--export FORMAT`: Export formats (markdown, json)
- `--output FILE`: Save results to file
- `--format FORMAT`: Output format (human, json)
- `--input FILE`: Use JSON configuration file

## 📈 Output Examples

### Human-Readable Report

```
============================================================
CodeRefinery Analysis Report
============================================================

SUMMARY
--------------------
Analyzed 1 Python files. Found 8 total issues. 2 high-severity 
issues require immediate attention.

FILE 1: problematic_code.py
--------------------------------------------
Style Issues:
  Line   5: [E501] line too long (95 > 79 characters)
           Suggestion: break line into multiple lines

Potential Bugs:
  Line   1: [HIGH] Dangerous default value [] (mutable default argument)
  Line  15: [HIGH] Use of eval() is dangerous and should be avoided

Complexity Metrics:
  complex_function     (line  15): CCN = 12 ⚠️
  simple_function      (line   5): CCN = 3
  Average CCN: 7.5
```

### JSON Output (Schema Compliant)

```json
{
  "summary": "Analyzed 1 Python files. Found 8 total issues.",
  "files": [
    {
      "path": "example.py",
      "language": "python",
      "style_issues": [
        {
          "line": 5,
          "code": "E501", 
          "message": "line too long (95 > 79 characters)",
          "suggestion": "break line into multiple lines"
        }
      ],
      "complexity": {
        "function_metrics": [
          {"name": "complex_function", "ccn": 12, "lineno": 15}
        ],
        "avg_ccn": 7.5
      },
      "bugs": [
        {
          "line": 1,
          "message": "Dangerous default value [] (mutable default argument)", 
          "severity": "high"
        }
      ],
      "before_snippet": "def bad_function(items=[]):",
      "after_snippet": "def bad_function(items=None):\n    if items is None:\n        items = []",
      "patch": "unified-diff-format"
    }
  ],
  "overall_metrics": {
    "total_issues": 8,
    "high_severity": 2,
    "files_analyzed": 1
  },
  "export": {
    "markdown": "...",
    "json": {...}
  }
}
```

## 🧪 Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=coderefinery --cov-report=html

# Run specific test file
pytest tests/test_analyzer.py
```

### Code Quality Checks

```bash
# Format code
black coderefinery tests examples

# Check style
flake8 coderefinery tests examples

# Type checking (if mypy installed)
mypy coderefinery

# Run all quality checks
make check
```

### Using the Makefile

```bash
# See all available commands
make help

# Install in development mode
make install-dev

# Run tests with coverage
make test-cov

# Run example analysis
make run-example

# Launch web interface
make run-web
```

## 📁 Project Structure

```
coderefinery/
├── coderefinery/           # Main package
│   ├── __init__.py        # Package initialization
│   ├── analyzer.py        # Core analysis engine
│   ├── models.py          # Data models and schemas
│   ├── cli.py             # Command-line interface
│   ├── web_app.py         # Streamlit web interface
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
│   ├── test_analyzer.py   # Analyzer tests
│   └── test_utils.py      # Utility tests
├── examples/              # Example scripts
│   └── example_analysis.py
├── config/                # Configuration files
│   └── example_input.json
├── pyproject.toml         # Project configuration
├── Makefile              # Development commands
├── LICENSE               # MIT License
└── README.md             # This file
```

## 🔧 Advanced Usage

### Custom Analysis Pipeline

```python
from coderefinery.analyzer import CodeAnalyzer
from coderefinery.models import Severity

# Custom analyzer with specific settings
analyzer = CodeAnalyzer(max_complexity_threshold=8)

# Analyze with custom options
result = analyzer.analyze_files(files, {
    "apply_black": True,
    "max_complexity_threshold": 5,
    "export_formats": ["markdown", "json"]
})

# Filter high-severity issues
high_severity_bugs = [
    bug for file_analysis in result.files 
    for bug in file_analysis.bugs 
    if bug.severity == Severity.HIGH
]
```

### Batch Processing

```bash
# Analyze all Python files in a directory
find . -name "*.py" | xargs coderefinery analyze

# Generate reports for multiple projects
for project in project1 project2 project3; do
    coderefinery analyze "$project"/*.py --output "${project}_report.json"
done
```

## 🎯 Tool Integration

CodeRefinery intelligently integrates with popular Python tools:

- **flake8**: For comprehensive style checking (falls back to heuristic analysis)
- **black**: For code formatting analysis and auto-fixing
- **radon**: For accurate complexity measurements
- **ast**: For Python code parsing and analysis

When these tools are not available, CodeRefinery uses built-in heuristic analysis to provide similar functionality.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Ensure code quality: `make check`
6. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/coderefinery/coderefinery.git
cd coderefinery

# Install in development mode with all dependencies
make install-dev

# Run tests to verify setup
make test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Uses [flake8](https://flake8.pycqa.org/), [black](https://black.readthedocs.io/), and [radon](https://radon.readthedocs.io/) for code analysis
- Follows [PEP8](https://pep8.org/) style guidelines
- Inspired by modern code quality tools and AI-assisted development practices

## 🆘 Support & Documentation

- **CLI Help**: `coderefinery --help` or `coderefinery analyze --help`
- **Python API**: See docstrings in `coderefinery.analyzer.CodeAnalyzer`
- **Web Interface**: Interactive help available in the Streamlit app
- **Examples**: Check the `examples/` directory for usage patterns

---

**CodeRefinery** - Making Python code better, one analysis at a time! 🐍✨

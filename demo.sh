#!/bin/bash
# CodeRefinery Demo Script

echo "🔍 CodeRefinery Demo - AI-Powered Code Quality Analyzer"
echo "========================================================"
echo

# Set up PATH
export PATH="/usr/local/python/3.12.1/bin:$PATH"

# Demo 1: Basic CLI analysis
echo "Demo 1: Basic File Analysis"
echo "----------------------------"
echo "Analyzing test_sample.py..."
echo
coderefinery analyze test_sample.py --max-complexity 5
echo

# Demo 2: JSON input analysis
echo "Demo 2: JSON Input Analysis"
echo "----------------------------"
echo "Using configuration from config/example_input.json..."
echo
coderefinery analyze --input config/example_input.json --export markdown,json --output demo_results.json
echo

# Demo 3: Show JSON results
echo "Demo 3: JSON Export Results (first 30 lines)"
echo "---------------------------------------------"
head -30 demo_results.json
echo "... (truncated)"
echo

# Demo 4: Example with better code
echo "Demo 4: Analysis of Well-Written Code"
echo "------------------------------------"

cat > good_example.py << 'EOF'
"""
A well-written Python module demonstrating good practices.
"""

def calculate_average(numbers: list) -> float:
    """Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numeric values
        
    Returns:
        The average as a float
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    return sum(numbers) / len(numbers)


class NumberProcessor:
    """A class for processing numeric data."""
    
    def __init__(self, default_value: float = 0.0) -> None:
        """Initialize with a default value."""
        self.default_value = default_value
        self.processed_count = 0
    
    def process_safe(self, value: str) -> float:
        """Safely convert string to float with error handling."""
        try:
            result = float(value)
            self.processed_count += 1
            return result
        except ValueError as e:
            print(f"Warning: Could not convert '{value}' to float: {e}")
            return self.default_value
EOF

echo "Analyzing well-written code (good_example.py):"
coderefinery analyze good_example.py
echo

# Demo 5: Version check
echo "Demo 5: Version Information"
echo "----------------------------"
coderefinery version
echo

echo "Demo Complete!"
echo "=============="
echo "Features demonstrated:"
echo "✓ Basic file analysis with style, complexity, and bug detection"
echo "✓ JSON configuration input"
echo "✓ Export capabilities (markdown and JSON)"
echo "✓ Comparison between problematic and well-written code"
echo "✓ Command-line interface with various options"
echo
echo "For web interface, run: streamlit run coderefinery/web_app.py"
echo "For help, run: coderefinery analyze --help"
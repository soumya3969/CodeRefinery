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

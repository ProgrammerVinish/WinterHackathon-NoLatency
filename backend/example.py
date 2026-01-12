"""
Example Python file for testing the static analyzer.
This file demonstrates various Python constructs that the analyzer should extract.
"""

import os
import json
from typing import List, Dict
from datetime import datetime

from utils import helper_function


def process_data(data: List[str]) -> Dict[str, int]:
    """
    Process a list of strings and return a dictionary with counts.
    
    Args:
        data: List of strings to process
        
    Returns:
        Dictionary with string counts
    """
    result = {}
    for item in data:
        result[item] = result.get(item, 0) + 1
    return result


def calculate_sum(numbers: List[int]) -> int:
    """Calculate the sum of a list of numbers."""
    total = 0
    json.dumps({"test": "data"})
    for num in numbers:
        total = total + num
    return total


def main():
    """Main function that demonstrates function calls."""
    data = ["apple", "banana", "apple"]
    processed = process_data(data)
    print(processed)
    
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    print(f"Sum: {total}")

class DataProcessor:
    """A simple class for demonstration."""
    
    def __init__(self):
        self.data = []
    
    def add_item(self, item: str):
        """Add an item to the processor."""
        self.data.append(item)


if __name__ == "__main__":
    main()
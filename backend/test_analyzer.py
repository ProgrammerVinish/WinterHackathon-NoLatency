"""
Simple test script to demonstrate the analyzer functionality.
"""

from analyzer import PythonStaticAnalyzer


def test_example_file():
    """Test the analyzer on the example.py file."""
    analyzer = PythonStaticAnalyzer()
    
    print("=" * 60)
    print("Testing Static Analyzer on example.py")
    print("=" * 60)
    print()
    
    result = analyzer.analyze_file("example.py")
    json_output = analyzer.analyze_file_to_json("example.py")
    
"""
Test file to demonstrate risk scoring functionality.
"""

from analyzer import PythonStaticAnalyzer


def test_api_call_detection():
    """Test HIGH risk detection for functions with API calls."""
    # Create a test file with API calls
    test_code = """
import requests
import urllib.request

def fetch_data(url):
    response = requests.get(url)
    return response.json()

def download_file(url):
    urllib.request.urlretrieve(url, "file.txt")
"""
    
    with open("test_api.py", "w") as f:
        f.write(test_code)
    
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("test_api.py")
    
    print("=" * 60)
    print("Test: API Call Detection (HIGH risk)")
    print("=" * 60)
    for func in result['functions']:
        if func['name'] in ['fetch_data', 'download_file']:
            print(f"\nFunction: {func['name']}")
            print(f"  Risk Level: {func['risk_score']['risk_level']}")
            print(f"  Risk Reason: {func['risk_score']['risk_reason']}")
            print(f"  API Calls: {func.get('api_calls', [])}")
    
    import os
    if os.path.exists("test_api.py"):
        os.remove("test_api.py")

def test_helper_function():
    """Test LOW risk detection for utility/helper functions."""
    test_code = """
def format_string(text):
    return text.strip().lower()

def parse_data(data):
    return data.split(',')

def validate_input(value):
    return value is not None
"""
    
    with open("test_helper.py", "w") as f:
        f.write(test_code)
    
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("test_helper.py")
    
    print("\n" + "=" * 60)
    print("Test: Helper Function Detection (LOW risk)")
    print("=" * 60)
    for func in result['functions']:
        print(f"\nFunction: {func['name']}")
        print(f"  Risk Level: {func['risk_score']['risk_level']}")
        print(f"  Risk Reason: {func['risk_score']['risk_reason']}")


def test_core_logic():
    """Test MEDIUM risk for core logic functions."""
    test_code = """
def process_order(order_id, items):
    total = 0
    for item in items:
        total += item['price']
    return total

def calculate_tax(amount, rate):
    return amount * rate
"""
    
    with open("test_core.py", "w") as f:
        f.write(test_code)
    
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("test_core.py")
    
    print("\n" + "=" * 60)
    print("Test: Core Logic Function (MEDIUM risk)")
    print("=" * 60)
    for func in result['functions']:
        print(f"\nFunction: {func['name']}")
        print(f"  Risk Level: {func['risk_score']['risk_level']}")
        print(f"  Risk Reason: {func['risk_score']['risk_reason']}")


def test_multi_file_usage():
    """Test HIGH risk for functions used in multiple files."""
    # Create two files with the same function name
    file1_code = """
def shared_function():
    return "shared"
"""
    
    file2_code = """
def shared_function():
    return "also shared"
"""
    
    with open("file1.py", "w") as f:
        f.write(file1_code)
    with open("file2.py", "w") as f:
        f.write(file2_code)
    
    # Build usage map
    analyzer = PythonStaticAnalyzer()
    usage_map = analyzer.build_function_usage_map(["file1.py", "file2.py"])
    
    # Analyze with usage map
    analyzer_with_map = PythonStaticAnalyzer(function_usage_map=usage_map)
    result = analyzer_with_map.analyze_file("file1.py")
    
    print("\n" + "=" * 60)
    print("Test: Multi-file Usage (HIGH risk)")
    print("=" * 60)
    print(f"Usage Map: {usage_map}")
    for func in result['functions']:
        if func['name'] == 'shared_function':
            print(f"\nFunction: {func['name']}")
            print(f"  Risk Level: {func['risk_score']['risk_level']}")
            print(f"  Risk Reason: {func['risk_score']['risk_reason']}")
    
    import os
    for f in ["file1.py", "file2.py"]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    test_api_call_detection()
    test_helper_function()
    test_core_logic()
    test_multi_file_usage()
    print("\n" + "=" * 60)
    print("All risk scoring tests completed!")
    print("=" * 60)
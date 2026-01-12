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


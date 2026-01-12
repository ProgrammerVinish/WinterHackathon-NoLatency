"""
Test script for Gemini API integration.
Demonstrates how to use the explainer with analyzed code metadata.
"""

from analyzer import PythonStaticAnalyzer
from gemini_explainer import GeminiExplainer
import os


def test_gemini_explanation():
    """Test Gemini explanation for a single function."""
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("=" * 60)
        print("GEMINI_API_KEY environment variable not set.")
        print("Set it to test Gemini integration:")
        print("  export GEMINI_API_KEY='your-api-key'")
        print("=" * 60)
        return
    
    print("=" * 60)
    print("Testing Gemini API Integration")
    print("=" * 60)
    
    # Analyze a file
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("example.py")
    
    if not result.get("functions"):
        print("No functions found in example.py")
        return
    
    # Get first function for testing
    first_function = result["functions"][0]
    
    print(f"\nAnalyzing function: {first_function['name']}")
    print(f"Risk Level: {first_function['risk_score']['risk_level']}")
    print(f"Risk Reason: {first_function['risk_score']['risk_reason']}")
    
    # Prepare file context
    file_context = {
        "imports": result.get("imports", []),
        "file_dependencies": result.get("file_dependencies", [])
    }
    
    try:
        # Get explanation from Gemini
        explainer = GeminiExplainer(api_key=api_key)
        print("\n" + "=" * 60)
        print("Requesting explanation from Gemini...")
        print("=" * 60)
        
        explanation = explainer.explain_function(first_function, file_context)
        
        print("\n" + "=" * 60)
        print("Gemini Explanation:")
        print("=" * 60)
        print(explanation)
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. GEMINI_API_KEY is set correctly")
        print("2. google-generativeai package is installed: pip install google-generativeai")
        print("3. You have internet connectivity")




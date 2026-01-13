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


def test_explain_all_functions():
    """Test explaining all functions in a file."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Skipping test.")
        return
    
    print("\n" + "=" * 60)
    print("Testing: Explain All Functions in File")
    print("=" * 60)
    
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("example.py")
    
    try:
        explainer = GeminiExplainer(api_key=api_key)
        explanations = explainer.explain_file(result)
        
        for func_name, explanation in explanations.items():
            print(f"\n{'=' * 60}")
            print(f"Function: {func_name}")
            print(f"{'=' * 60}")
            print(explanation)
            print()
            
    except Exception as e:
        print(f"Error: {e}")


def test_metadata_only():
    """Verify that only metadata is sent, never raw code."""
    print("\n" + "=" * 60)
    print("Verifying: Only Metadata Sent (No Raw Code)")
    print("=" * 60)
    
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file("example.py")
    
    # Check that result contains only metadata
    assert "file_path" in result
    assert "imports" in result
    assert "functions" in result
    
    # Verify functions contain only metadata, not source code
    for func in result["functions"]:
        assert "name" in func
        assert "parameters" in func
        assert "risk_score" in func
        # Ensure NO source code fields
        assert "source_code" not in func
        assert "body" not in func
        assert "code" not in func
    
    print("[OK] Verified: Analysis result contains only structured metadata")
    print("[OK] No raw source code in the output")
    print("[OK] Safe to send to Gemini API")


if __name__ == "__main__":
    # First verify metadata-only structure
    test_metadata_only()
    
    # Then test Gemini integration (requires API key)
    test_gemini_explanation()
    
    # Uncomment to test all functions
    # test_explain_all_functions()

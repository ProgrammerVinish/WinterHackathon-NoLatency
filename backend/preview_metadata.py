"""
Utility script to preview the structured metadata that would be sent to Gemini.
Useful for verifying that NO raw source code is included.
"""

from analyzer import PythonStaticAnalyzer
from gemini_explainer import GeminiExplainer
import json


def preview_metadata_for_function(file_path: str, function_name: str = None):
    """
    Preview the metadata that would be sent to Gemini for a function.
    
    Args:
        file_path: Path to Python file
        function_name: Name of function to preview (uses first function if None)
    """
    print("=" * 60)
    print("Preview: Metadata Sent to Gemini")
    print("=" * 60)
    print(f"\nFile: {file_path}\n")
    
    # Analyze file
    analyzer = PythonStaticAnalyzer()
    result = analyzer.analyze_file(file_path)
    
    if not result.get("functions"):
        print("No functions found in file.")
        return
    
    # Select function
    if function_name:
        func = next((f for f in result["functions"] if f["name"] == function_name), None)
        if not func:
            print(f"Function '{function_name}' not found.")
            return
    else:
        func = result["functions"][0]
        function_name = func["name"]
    
    print(f"Function: {function_name}")
    print("\n" + "-" * 60)
    print("Metadata that would be sent to Gemini:")
    print("-" * 60)
    
    # Prepare metadata (same as what GeminiExplainer does)
    file_context = {
        "imports": result.get("imports", []),
        "file_dependencies": result.get("file_dependencies", [])
    }
    
    # Prepare metadata manually (same logic as GeminiExplainer._prepare_function_metadata)
    clean_metadata = {
        "function_name": func.get("name"),
        "parameters": func.get("parameters", []),
        "parameter_count": func.get("parameter_count", 0),
        "line_number": func.get("line_number"),
        "function_calls": func.get("function_calls", []),
        "api_calls": func.get("api_calls", []),
        "is_async": func.get("is_async", False),
        "decorators": func.get("decorators", []),
        "risk_score": func.get("risk_score", {})
    }
    
    # Add file context if provided
    if file_context:
        clean_metadata["file_context"] = {
            "imports": file_context.get("imports", []),
            "file_dependencies": file_context.get("file_dependencies", [])
        }
    
    # Pretty print JSON
    metadata_json = json.dumps(clean_metadata, indent=2)
    print(metadata_json)
    
    print("\n" + "-" * 60)
    print("Verification:")
    print("-" * 60)
    
    # Verify no raw code
    metadata_str = str(clean_metadata).lower()
    forbidden_keywords = ["source", "code", "body", "raw", "text", "content"]
    found_keywords = [kw for kw in forbidden_keywords if kw in metadata_str]
    
    if found_keywords:
        print(f"[WARNING] Found keywords that might indicate raw code: {found_keywords}")
    else:
        print("[OK] No raw code keywords found in metadata")
    
    # Check structure
    required_fields = ["function_name", "parameters", "risk_score"]
    missing_fields = [f for f in required_fields if f not in clean_metadata]
    
    if missing_fields:
        print(f"[WARNING] Missing required fields: {missing_fields}")
    else:
        print("[OK] All required metadata fields present")
    
    print("\n[OK] This metadata is safe to send to Gemini (no raw source code)")


if __name__ == "__main__":
    import sys
    
    file_path = sys.argv[1] if len(sys.argv) > 1 else "example.py"
    function_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        preview_metadata_for_function(file_path, function_name)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error: {e}")

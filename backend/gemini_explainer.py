"""
Gemini API Integration for ExplainIt
Sends structured metadata to Gemini for code explanation.
NEVER sends raw source code - only structured JSON metadata.
"""

import json
import os
from typing import Dict, List, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiExplainer:
    """
    Integrates with Google Gemini API to explain Python functions
    based on structured metadata only (never raw source code).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini explainer.
        
        Args:
            api_key: Google Gemini API key. If None, reads from GEMINI_API_KEY env var.
        
        Raises:
            ImportError: If google-generativeai package is not installed
            ValueError: If API key is not provided
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package is required. "
                "Install with: pip install google-generativeai"
            )
        
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Provide it as parameter or set GEMINI_API_KEY environment variable."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def explain_function(self, function_metadata: Dict[str, Any], 
                        file_context: Dict[str, Any] = None) -> str:
        """
        Get explanation for a single function from Gemini.
        
        Args:
            function_metadata: Dictionary with function metadata (name, parameters, calls, risk_score, etc.)
            file_context: Optional file-level context (imports, dependencies)
            
        Returns:
            Plain text explanation from Gemini
        """
        # Prepare structured metadata (ONLY metadata, never raw code)
        metadata_json = self._prepare_function_metadata(function_metadata, file_context)
        
        # Create prompt that asks for explanation only (no code generation)
        prompt = self._create_explanation_prompt(metadata_json)
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error getting explanation from Gemini: {str(e)}"
    
    def explain_file(self, analysis_result: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Get explanations for all functions in an analyzed file.
        
        Args:
            analysis_result: Full analysis result from PythonStaticAnalyzer
            
        Returns:
            Dictionary mapping function names to their explanations
        """
        explanations = {}
        file_context = {
            "imports": analysis_result.get("imports", []),
            "file_dependencies": analysis_result.get("file_dependencies", [])
        }
        
        for func_metadata in analysis_result.get("functions", []):
            func_name = func_metadata.get("name", "unknown")
            explanation = self.explain_function(func_metadata, file_context)
            explanations[func_name] = explanation
        
        return explanations
    
    def _prepare_function_metadata(self, function_metadata: Dict[str, Any],
                                   file_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare clean metadata dictionary for Gemini.
        Ensures NO raw source code is included.
        
        Args:
            function_metadata: Function metadata from analyzer
            file_context: Optional file-level context
            
        Returns:
            Clean metadata dictionary ready for JSON serialization
        """
        # Extract only the metadata we want to send
        clean_metadata = {
            "function_name": function_metadata.get("name"),
            "parameters": function_metadata.get("parameters", []),
            "parameter_count": function_metadata.get("parameter_count", 0),
            "line_number": function_metadata.get("line_number"),
            "function_calls": function_metadata.get("function_calls", []),
            "api_calls": function_metadata.get("api_calls", []),
            "is_async": function_metadata.get("is_async", False),
            "decorators": function_metadata.get("decorators", []),
            "risk_score": function_metadata.get("risk_score", {})
        }
        
        # Add file context if provided
        if file_context:
            clean_metadata["file_context"] = {
                "imports": file_context.get("imports", []),
                "file_dependencies": file_context.get("file_dependencies", [])
            }
        
        return clean_metadata
    
    def _create_explanation_prompt(self, metadata_json: Dict[str, Any]) -> str:
        """
        Create prompt for Gemini that asks for explanation only.
        Explicitly prohibits code generation or refactoring suggestions.
        
        Args:
            metadata_json: Structured metadata dictionary
            
        Returns:
            Formatted prompt string
        """
        # Convert metadata to JSON string for the prompt
        metadata_str = json.dumps(metadata_json, indent=2)
        
        prompt = f"""You are analyzing a Python function based on its structured metadata. 
You will receive ONLY metadata (function name, parameters, calls, risk score) - NO raw source code.

Function Metadata:
{metadata_str}

Please provide a clear, concise explanation in plain text that addresses:

1. **Why this function exists**: What is its purpose and role in the codebase?
   - Based on the function name, parameters, and what it calls
   - Consider the imports and dependencies as context

2. **What might break if changed**: What are the potential impacts of modifying this function?
   - Consider the risk level and why it was assigned
   - Think about what other code might depend on this function
   - Consider the function calls it makes and parameters it accepts

3. **Why the risk level is assigned**: Explain the risk assessment reasoning
   - Risk level: {metadata_json.get('risk_score', {}).get('risk_level', 'UNKNOWN')}
   - Risk reason: {metadata_json.get('risk_score', {}).get('risk_reason', 'Not provided')}
   - Explain what factors contribute to this risk level

IMPORTANT CONSTRAINTS:
- Provide explanation ONLY - do NOT generate code
- Do NOT suggest refactoring or code changes
- Do NOT provide code examples
- Focus on understanding and explanation
- Write in clear, natural language

Your explanation:"""
        
        return prompt


def explain_with_gemini(function_metadata: Dict[str, Any],
                       api_key: Optional[str] = None,
                       file_context: Dict[str, Any] = None) -> str:
    """
    Convenience function to get explanation for a function.
    
    Args:
        function_metadata: Function metadata dictionary
        api_key: Optional Gemini API key (uses env var if not provided)
        file_context: Optional file-level context
        
    Returns:
        Plain text explanation
    """
    explainer = GeminiExplainer(api_key=api_key)
    return explainer.explain_function(function_metadata, file_context)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python gemini_explainer.py <api_key>")
        print("Or set GEMINI_API_KEY environment variable")
        sys.exit(1)
    
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Example function metadata
    example_metadata = {
        "name": "process_data",
        "parameters": [{"name": "data", "annotation": "List[str]"}],
        "parameter_count": 1,
        "line_number": 14,
        "function_calls": ["get"],
        "api_calls": [],
        "is_async": False,
        "decorators": [],
        "risk_score": {
            "risk_level": "MEDIUM",
            "risk_reason": "Core logic function, used once, no external API calls"
        }
    }
    
    try:
        explainer = GeminiExplainer(api_key=api_key)
        explanation = explainer.explain_function(example_metadata)
        print("\n" + "=" * 60)
        print("Gemini Explanation:")
        print("=" * 60)
        print(explanation)
    except Exception as e:
        print(f"Error: {e}")

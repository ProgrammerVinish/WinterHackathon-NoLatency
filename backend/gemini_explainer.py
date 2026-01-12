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
    

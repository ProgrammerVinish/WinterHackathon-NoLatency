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
    

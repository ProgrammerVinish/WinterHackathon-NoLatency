"""
Utility script to preview the structured metadata that would be sent to Gemini.
Useful for verifying that NO raw source code is included.
"""

from analyzer import PythonStaticAnalyzer
from gemini_explainer import GeminiExplainer
import json




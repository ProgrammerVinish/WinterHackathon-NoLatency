"""
Static Analysis Module for ExplainIt
Analyzes Python code files and extracts structured metadata using AST parsing.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Any


class PythonStaticAnalyzer:
    """
    Analyzes Python source code files using AST parsing.
    Extracts imports, functions, parameters, calls, and dependencies.
    """
    
    def __init__(self):
        self.imports: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.file_dependencies: Set[str] = set()
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point: analyzes a Python file and returns structured metadata.
        
        Args:
            file_path: Path to the .py file to analyze
            
        Returns:
            Dictionary containing all extracted metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.suffix == '.py':
            raise ValueError(f"File must be a Python file (.py): {file_path}")
        
        # Reset state for fresh analysis
        self.imports = []
        self.functions = []
        self.file_dependencies = set()
        
        # Read and parse the file
        try:
            source_code = path.read_text(encoding='utf-8')
            tree = ast.parse(source_code, filename=str(path))
        except SyntaxError as e:
            return {
                "error": f"Syntax error in file: {str(e)}",
                "file_path": str(path),
                "imports": [],
                "functions": [],
                "file_dependencies": []
            }
        
        # Extract metadata by walking the AST
        visitor = CodeAnalyzerVisitor(self.imports, self.functions, self.file_dependencies, path.parent)
        visitor.visit(tree)
        
        # Build result structure
        result = {
            "file_path": str(path),
            "imports": self.imports,
            "functions": self.functions,
            "file_dependencies": sorted(list(self.file_dependencies))
        }
        
        return result
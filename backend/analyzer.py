"""
Static Analysis Module for ExplainIt
Analyzes Python code files and extracts structured metadata using AST parsing.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Any


class PythonStaticAnalyzer:
    def __init__(self):
        self.imports = []
        self.functions = []
        self.file_dependencies = set()

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix != ".py":
            raise ValueError("File must be a Python file")

        self.imports = []
        self.functions = []
        self.file_dependencies = set()

        try:
            source_code = path.read_text(encoding="utf-8")
            tree = ast.parse(source_code, filename=str(path))
        except SyntaxError as e:
            return {
                "error": str(e),
                "file_path": str(path),
                "imports": [],
                "functions": [],
                "file_dependencies": []
            }

        return {
            "file_path": str(path),
            "imports": self.imports,
            "functions": self.functions,
            "file_dependencies": []
        }
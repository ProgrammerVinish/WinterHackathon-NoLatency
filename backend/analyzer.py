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
    
    def __init__(self, function_usage_map: Dict[str, int] = None):
        """
        Initialize analyzer.
        
        Args:
            function_usage_map: Optional dictionary mapping function names to usage counts
                              across files. Used for risk scoring multi-file usage.
        """
        self.imports: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.file_dependencies: Set[str] = set()
        self.function_usage_map = function_usage_map or {}
    
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
        
        # Apply risk scoring to functions
        risk_scorer = RiskScorer(self.function_usage_map)
        for func_info in self.functions:
            # Get API calls from function info (stored as list, convert to set)
            api_calls_set = set(func_info.get('api_calls', []))
            risk_score = risk_scorer.score_function(func_info, self.imports, api_calls_set)
            func_info['risk_score'] = risk_score
        
        # Build result structure
        result = {
            "file_path": str(path),
            "imports": self.imports,
            "functions": self.functions,
            "file_dependencies": sorted(list(self.file_dependencies))
        }
        
        return result
    
    def analyze_file_to_json(self, file_path: str, indent: int = 2) -> str:
        """
        Analyzes a file and returns the result as a JSON string.
        
        Args:
            file_path: Path to the .py file to analyze
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the analysis
        """
        result = self.analyze_file(file_path)
        return json.dumps(result, indent=indent)
    
    def build_function_usage_map(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Analyzes multiple files and builds a map of function usage counts.
        Used for risk scoring to detect functions used in multiple files.
        
        Args:
            file_paths: List of Python file paths to analyze
            
        Returns:
            Dictionary mapping function names to usage counts across files
        """
        function_usage: Dict[str, int] = {}
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if not path.exists() or not path.suffix == '.py':
                    continue
                
                source_code = path.read_text(encoding='utf-8')
                tree = ast.parse(source_code, filename=str(path))
                
                # Extract function definitions from this file
                visitor = CodeAnalyzerVisitor([], [], set(), path.parent)
                visitor.visit(tree)
                
                # Count function definitions (not calls, but definitions)
                for func_info in visitor.functions:
                    func_name = func_info['name']
                    function_usage[func_name] = function_usage.get(func_name, 0) + 1
                    
            except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
                # Skip files with errors
                continue
        
        return function_usage
    
    def analyze_file_with_context(self, file_path: str, 
                                  project_files: List[str] = None) -> Dict[str, Any]:
        """
        Analyzes a file with context from other project files for accurate risk scoring.
        
        Args:
            file_path: Path to the .py file to analyze
            project_files: Optional list of all Python files in the project
                          for building function usage map
            
        Returns:
            Dictionary containing all extracted metadata with risk scores
        """
        # Build function usage map if project files provided
        if project_files:
            usage_map = self.build_function_usage_map(project_files)
            # Re-initialize with usage map
            self.function_usage_map = usage_map
        
        return self.analyze_file(file_path)


class CodeAnalyzerVisitor(ast.NodeVisitor):
    """
    AST Visitor that extracts metadata from Python code.
    Visits nodes in the AST tree and collects information.
    """
    
    def __init__(self, imports: List[Dict], functions: List[Dict], 
                 dependencies: Set[str], file_dir: Path):
        self.imports = imports
        self.functions = functions
        self.file_dependencies = dependencies
        self.file_dir = file_dir
        self.current_function = None
    
    def visit_Import(self, node: ast.Import):
        """Extracts standard import statements (e.g., 'import os')."""
        for alias in node.names:
            import_info = {
                "type": "import",
                "module": alias.name,
                "alias": alias.asname if alias.asname else None
            }
            self.imports.append(import_info)
            # Check if this might be a local file dependency
            self._check_local_dependency(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extracts from-import statements (e.g., 'from os import path')."""
        module_name = node.module if node.module else ""
        imports_list = []
        
        for alias in node.names:
            import_item = {
                "name": alias.name,
                "alias": alias.asname if alias.asname else None
            }
            imports_list.append(import_item)
        
        import_info = {
            "type": "from_import",
            "module": module_name,
            "imports": imports_list
        }
        self.imports.append(import_info)
        # Check if this might be a local file dependency
        if module_name:
            self._check_local_dependency(module_name)
        
        self.generic_visit(node)
    
    def _check_local_dependency(self, module_name: str):
        """
        Determines if an import is a local file dependency.
        Simple heuristic: if a .py file with that name exists in the directory,
        it's considered a local dependency.
        """
        # Skip standard library and common packages (simple heuristic)
        if '.' in module_name or module_name.startswith('_'):
            # Could be a local module with dots, check if file exists
            module_path = self.file_dir / f"{module_name.replace('.', '/')}.py"
            if module_path.exists():
                self.file_dependencies.add(str(module_path))
        else:
            # Check if it's a local file in the same directory
            local_file = self.file_dir / f"{module_name}.py"
            if local_file.exists():
                self.file_dependencies.add(str(local_file))
            # Also check parent directory (common pattern)
            parent_file = self.file_dir.parent / f"{module_name}.py"
            if parent_file.exists():
                self.file_dependencies.add(str(parent_file))
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extracts function definitions including name, parameters, and calls."""
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None
            }
            params.append(param_info)
        
        # Extract function calls within this function (including API calls)
        call_collector = FunctionCallCollector()
        call_collector.visit(node)
        
        function_info = {
            "name": node.name,
            "parameters": params,
            "parameter_count": len(params),
            "line_number": node.lineno,
            "function_calls": call_collector.calls,
            "api_calls": list(call_collector.api_calls),  # Store API calls for risk scoring
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [ast.unparse(dec) for dec in node.decorator_list] if node.decorator_list else []
        }
        
        self.functions.append(function_info)
        self.generic_visit(node)

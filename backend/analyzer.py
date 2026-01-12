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
        
        # Extract function calls within this function
        call_collector = FunctionCallCollector()
        call_collector.visit(node)
        
        function_info = {
            "name": node.name,
            "parameters": params,
            "parameter_count": len(params),
            "line_number": node.lineno,
            "function_calls": call_collector.calls,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [ast.unparse(dec) for dec in node.decorator_list] if node.decorator_list else []
        }
        
        self.functions.append(function_info)
        self.generic_visit(node)
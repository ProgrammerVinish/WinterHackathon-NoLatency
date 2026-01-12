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
class RiskScorer:
    """
    Rule-based risk scoring system for functions.
    Assigns risk levels based on deterministic rules.
    """
    
    # Known external API libraries/modules
    API_MODULES = {
        'requests', 'http', 'urllib', 'urllib2', 'httplib', 'aiohttp',
        'httpx', 'urllib3', 'http.client', 'http.server', 'urllib.request',
        'urllib.parse', 'urllib.error'
    }
    
    # Common API-related function names
    API_FUNCTION_NAMES = {
        'get', 'post', 'put', 'delete', 'patch', 'request', 'urlopen',
        'urlretrieve', 'urlencode', 'send', 'fetch'
    }
    
    # Helper/utility function name patterns
    HELPER_PATTERNS = [
        'helper', 'util', 'utils', 'format', 'parse', 'convert', 'transform',
        'validate', 'sanitize', 'normalize', 'escape', 'unescape', 'encode',
        'decode', 'serialize', 'deserialize', 'to_', 'from_', 'is_', 'has_',
        'get_', 'set_', 'make_', 'create_', 'build_'
    ]
    
    def __init__(self, function_usage_map: Dict[str, int] = None):
        """
        Initialize risk scorer.
        
        Args:
            function_usage_map: Dictionary mapping function names to usage counts
                              across files. If None, assumes single-file analysis.
        """
        self.function_usage_map = function_usage_map or {}
    
    def score_function(self, function_info: Dict[str, Any], 
                      imports: List[Dict[str, Any]],
                      api_calls: Set[str] = None) -> Dict[str, str]:
        """
        Score a function's risk level based on deterministic rules.
        
        Args:
            function_info: Dictionary with function metadata (name, calls, etc.)
            imports: List of import statements from the file
            api_calls: Set of API-related calls found in the function
            
        Returns:
            Dictionary with 'risk_level' and 'risk_reason'
        """
        function_name = function_info.get('name', '')
        function_calls = function_info.get('function_calls', [])
        api_calls = api_calls or set()
        
        # Check for external API calls (HIGH risk)
        if self._has_external_api_calls(imports, api_calls, function_calls):
            return {
                "risk_level": "HIGH",
                "risk_reason": "Function makes external API calls"
            }
        
        # Check if function is used in multiple files (HIGH risk)
        usage_count = self.function_usage_map.get(function_name, 1)
        if usage_count > 1:
            return {
                "risk_level": "HIGH",
                "risk_reason": f"Function used in {usage_count} files"
            }
        
        # Check if function is a utility/helper function (LOW risk)
        if self._is_helper_function(function_name):
            return {
                "risk_level": "LOW",
                "risk_reason": "Utility/helper function"
            }
        
        # Default: MEDIUM risk (core logic, used once, no external calls)
        return {
            "risk_level": "MEDIUM",
            "risk_reason": "Core logic function, used once, no external API calls"
        }
    
    def _has_external_api_calls(self, imports: List[Dict[str, Any]], 
                               api_calls: Set[str],
                               function_calls: List[str]) -> bool:
        """
        Determines if the function makes external API calls.
        
        Checks if the function actually uses API calls by:
        1. Checking if API modules are called directly (e.g., requests.get)
        2. Checking if imported API modules are used in function calls
        """
        # Build set of imported API module names and aliases
        imported_api_modules = set()
        for imp in imports:
            if imp['type'] == 'import':
                module_name = imp['module']
                alias = imp.get('alias')
                # Check if this is an API module
                if self._is_api_module(module_name):
                    imported_api_modules.add(alias if alias else module_name)
            elif imp['type'] == 'from_import':
                module_name = imp['module']
                if self._is_api_module(module_name):
                    # For from-import, check if any imported items are used
                    for item in imp.get('imports', []):
                        imported_name = item.get('alias') or item.get('name')
                        if imported_name in self.API_FUNCTION_NAMES:
                            return True
                    # Also track the module itself
                    imported_api_modules.add(module_name)
        
        # Check API calls that use API modules (e.g., requests.get, urllib.request.urlopen)
        for api_call in api_calls:
            # Extract module part from API call (e.g., "requests" from "requests.get")
            if '.' in api_call:
                module_part = api_call.split('.')[0]
                # Check if this module is an API module
                if module_part in self.API_MODULES or module_part in imported_api_modules:
                    return True
                # Check for partial matches (e.g., 'urllib.request' matches 'urllib')
                for api_module in self.API_MODULES:
                    if module_part.startswith(api_module.split('.')[0]) or api_module.startswith(module_part):
                        return True
        
        # Check if function calls use imported API modules
        for call in function_calls:
            # Check if any imported API module name appears in calls
            # This handles cases like: requests.get() where 'requests' is imported
            for api_module in imported_api_modules:
                if call.startswith(api_module) or api_module in call:
                    return True
        
        return False
    
    def _is_api_module(self, module_name: str) -> bool:
        """Check if a module name is an API-related module."""
        # Direct match
        if module_name in self.API_MODULES:
            return True
        # Check if module starts with any API module name
        for api_module in self.API_MODULES:
            base_module = api_module.split('.')[0]
            if module_name == base_module or module_name.startswith(base_module + '.'):
                return True
        return False
    
    def _is_helper_function(self, function_name: str) -> bool:
        """
        Determines if a function is a utility/helper function based on naming patterns.
        """
        function_name_lower = function_name.lower()
        return any(pattern in function_name_lower for pattern in self.HELPER_PATTERNS)


class FunctionCallCollector(ast.NodeVisitor):
    """
    Helper visitor to collect function calls within a function body.
    Extracts the names of functions being called and tracks API-related calls.
    """
    
    def __init__(self):
        self.calls: List[str] = []
        self.api_calls: Set[str] = set()  # Track API-related function calls
    
    def visit_Call(self, node: ast.Call):
        """Extracts function call names and detects API calls."""
        if isinstance(node.func, ast.Name):
            # Direct function call: function_name()
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method call: obj.method_name()
            # We store just the method name for simplicity
            self.calls.append(node.func.attr)
            # Check if this is an API call (e.g., requests.get, urllib.request.urlopen)
            if isinstance(node.func.value, ast.Name):
                # Track the module name for API detection
                self.api_calls.add(f"{node.func.value.id}.{node.func.attr}")
            elif isinstance(node.func.value, ast.Attribute):
                # Handle nested attributes (e.g., urllib.request.urlopen)
                attr_name = self._get_attribute_name(node.func.value)
                if attr_name:
                    self.api_calls.add(f"{attr_name}.{node.func.attr}")
        elif isinstance(node.func, ast.Call):
            # Chained call: func()()
            pass  # Skip complex chained calls for MVP
        
        self.generic_visit(node)
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Helper to extract full attribute name from nested attributes."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            parent = self._get_attribute_name(node.value)
            return f"{parent}.{node.attr}" if parent else None
        return None


def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a Python file.
    
    Args:
        file_path: Path to the .py file
        
    Returns:
        Dictionary with analysis results
    """
    analyzer = PythonStaticAnalyzer()
    return analyzer.analyze_file(file_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        analyzer = PythonStaticAnalyzer()
        result = analyzer.analyze_file(file_path)
        print(analyzer.analyze_file_to_json(file_path))
    else:
        print("Usage: python analyzer.py <path_to_python_file>")

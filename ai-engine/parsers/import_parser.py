"""
Import Parser with Tree-sitter and Regex Fallbacks
Extracts import statements from source files using tree-sitter with regex fallback.
"""
import logging
import re
from typing import List, Set, Optional, TYPE_CHECKING
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Type checking imports
if TYPE_CHECKING:
    from tree_sitter import Language, Parser

# Global flag to track if tree-sitter is available
TREE_SITTER_AVAILABLE = False
TREE_SITTER_PARSERS = {}
Parser = None  # Initialize to None, will be set if tree-sitter is available

# Try to import tree-sitter - fail gracefully if not available
try:
    from tree_sitter import Language, Parser  # type: ignore
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_go
    
    # Initialize parsers for different languages
    TREE_SITTER_PARSERS = {
        'python': Language(tree_sitter_python.language(), 'python'),
        'javascript': Language(tree_sitter_javascript.language(), 'javascript'),
        'typescript': Language(tree_sitter_typescript.language_typescript(), 'typescript'),
        'tsx': Language(tree_sitter_typescript.language_tsx(), 'tsx'),
        'go': Language(tree_sitter_go.language(), 'go'),
    }
    TREE_SITTER_AVAILABLE = True
    logger.info("Tree-sitter successfully initialized")
    
except Exception as e:
    logger.warning(f"Tree-sitter initialization failed, falling back to regex: {e}")
    TREE_SITTER_AVAILABLE = False


def parse_imports_from_file(filepath: str, language: Optional[str] = None) -> List[str]:
    """
    Extracts import statements from a source file.
    
    Attempts to use tree-sitter for accurate parsing, but falls back to
    regex patterns if tree-sitter is unavailable or fails.
    
    Args:
        filepath: Path to the source file to parse
        language: Programming language (python, javascript, typescript, go, etc.)
                 If None, will be inferred from file extension
        
    Returns:
        List of import statements/module names found in the file
    """
    try:
        # Read file content
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Infer language from extension if not provided
        if language is None:
            language = _infer_language_from_path(filepath)
        
        # Try tree-sitter first if available
        if TREE_SITTER_AVAILABLE and language in TREE_SITTER_PARSERS:
            try:
                imports = _parse_imports_with_treesitter(content, language)
                if imports:
                    logger.debug(f"Tree-sitter parsed {len(imports)} imports from {filepath}")
                    return imports
            except Exception as e:
                logger.debug(f"Tree-sitter parsing failed for {filepath}: {e}")
        
        # Fall back to regex parsing
        imports = _parse_imports_with_regex(content, language)
        logger.debug(f"Regex parsed {len(imports)} imports from {filepath}")
        return imports
        
    except Exception as e:
        logger.error(f"Error parsing imports from {filepath}: {e}")
        return []


def _infer_language_from_path(filepath: str) -> str:
    """
    Infers programming language from file extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Language identifier (python, javascript, typescript, go, etc.)
    """
    ext = Path(filepath).suffix.lower()
    
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.go': 'go',
        '.rb': 'ruby',
        '.java': 'java',
        '.cs': 'csharp',
        '.php': 'php',
    }
    
    return extension_map.get(ext, 'unknown')


def _parse_imports_with_treesitter(content: str, language: str) -> List[str]:
    """
    Parses imports using tree-sitter for accurate AST-based extraction.
    
    Args:
        content: Source code content
        language: Programming language identifier
        
    Returns:
        List of imported module names
    """
    imports: Set[str] = set()
    
    try:
        # Get the appropriate parser
        lang = TREE_SITTER_PARSERS.get(language)
        if not lang:
            return []
        
        # Parser should be available since TREE_SITTER_AVAILABLE is True
        if Parser is None:
            raise RuntimeError("Parser is not available despite TREE_SITTER_AVAILABLE being True")
        
        parser = Parser()
        parser.set_language(lang)
        
        # Parse the content
        tree = parser.parse(bytes(content, 'utf8'))
        root_node = tree.root_node
        
        # Extract imports based on language
        if language == 'python':
            imports.update(_extract_python_imports_treesitter(root_node))
        elif language in ['javascript', 'typescript', 'tsx']:
            imports.update(_extract_js_imports_treesitter(root_node))
        elif language == 'go':
            imports.update(_extract_go_imports_treesitter(root_node))
        
    except Exception as e:
        logger.debug(f"Tree-sitter parsing error: {e}")
        raise
    
    return sorted(list(imports))


def _extract_python_imports_treesitter(node) -> Set[str]:
    """Extracts Python imports from tree-sitter AST."""
    imports: Set[str] = set()
    
    def traverse(n):
        if n.type == 'import_statement':
            # import module
            for child in n.children:
                if child.type == 'dotted_name':
                    imports.add(child.text.decode('utf8'))
        elif n.type == 'import_from_statement':
            # from module import ...
            for child in n.children:
                if child.type == 'dotted_name':
                    imports.add(child.text.decode('utf8'))
        
        for child in n.children:
            traverse(child)
    
    traverse(node)
    return imports


def _extract_js_imports_treesitter(node) -> Set[str]:
    """Extracts JavaScript/TypeScript imports from tree-sitter AST."""
    imports: Set[str] = set()
    
    def traverse(n):
        if n.type == 'import_statement':
            # import ... from 'module'
            for child in n.children:
                if child.type == 'string':
                    # Remove quotes from string
                    module = child.text.decode('utf8').strip('\'"')
                    imports.add(module)
        elif n.type == 'call_expression':
            # require('module')
            func = n.child_by_field_name('function')
            if func and func.text.decode('utf8') == 'require':
                args = n.child_by_field_name('arguments')
                if args:
                    for child in args.children:
                        if child.type == 'string':
                            module = child.text.decode('utf8').strip('\'"')
                            imports.add(module)
        
        for child in n.children:
            traverse(child)
    
    traverse(node)
    return imports


def _extract_go_imports_treesitter(node) -> Set[str]:
    """Extracts Go imports from tree-sitter AST."""
    imports: Set[str] = set()
    
    def traverse(n):
        if n.type == 'import_declaration':
            for child in n.children:
                if child.type == 'import_spec':
                    for spec_child in child.children:
                        if spec_child.type == 'interpreted_string_literal':
                            module = spec_child.text.decode('utf8').strip('"')
                            imports.add(module)
        
        for child in n.children:
            traverse(child)
    
    traverse(node)
    return imports


def _parse_imports_with_regex(content: str, language: str) -> List[str]:
    """
    Parses imports using regex patterns as a fallback.
    
    This is a fast, reliable fallback when tree-sitter is unavailable
    or fails. While less accurate than AST parsing, it handles most
    common import patterns effectively.
    
    Args:
        content: Source code content
        language: Programming language identifier
        
    Returns:
        List of imported module names
    """
    imports: Set[str] = set()
    
    try:
        if language == 'python':
            # Match: import module, from module import ...
            import_pattern = r'^\s*(?:from\s+([a-zA-Z0-9_.]+)\s+)?import\s+([a-zA-Z0-9_., ]+)'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                if match.group(1):  # from X import
                    imports.add(match.group(1))
                if match.group(2):  # import X
                    # Handle multiple imports: import a, b, c
                    for module in match.group(2).split(','):
                        module = module.strip().split()[0]  # Get first part before 'as'
                        if module:
                            imports.add(module)
        
        elif language in ['javascript', 'typescript', 'tsx']:
            # Match: import ... from 'module', require('module')
            import_pattern = r'(?:import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]|require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\))'
            for match in re.finditer(import_pattern, content):
                module = match.group(1) or match.group(2)
                if module:
                    imports.add(module)
        
        elif language == 'go':
            # Match: import "module" or import ( "module1" "module2" )
            # Single import
            single_pattern = r'^\s*import\s+"([^"]+)"'
            for match in re.finditer(single_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
            
            # Multi-line import block
            block_pattern = r'import\s*\(\s*((?:[^)]*\n)*)\s*\)'
            for block_match in re.finditer(block_pattern, content, re.MULTILINE):
                block_content = block_match.group(1)
                module_pattern = r'"([^"]+)"'
                for module_match in re.finditer(module_pattern, block_content):
                    imports.add(module_match.group(1))
        
        elif language == 'java':
            # Match: import package.Class;
            import_pattern = r'^\s*import\s+([a-zA-Z0-9_.]+);'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
        
        elif language == 'ruby':
            # Match: require 'module', require_relative 'module'
            import_pattern = r'^\s*require(?:_relative)?\s+[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
        
        elif language == 'php':
            # Match: use Namespace\Class, require 'file.php'
            use_pattern = r'^\s*use\s+([a-zA-Z0-9_\\]+)'
            require_pattern = r'^\s*require(?:_once)?\s+[\'"]([^\'"]+)[\'"]'
            
            for match in re.finditer(use_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
            for match in re.finditer(require_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
        
        elif language == 'csharp':
            # Match: using Namespace;
            import_pattern = r'^\s*using\s+([a-zA-Z0-9_.]+);'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                imports.add(match.group(1))
    
    except Exception as e:
        logger.error(f"Regex parsing error for {language}: {e}")
    
    return sorted(list(imports))


def get_parser_status() -> dict:
    """
    Returns the current status of the import parser.
    
    Returns:
        Dictionary with parser availability and supported languages
    """
    return {
        "tree_sitter_available": TREE_SITTER_AVAILABLE,
        "tree_sitter_languages": list(TREE_SITTER_PARSERS.keys()) if TREE_SITTER_AVAILABLE else [],
        "regex_fallback_enabled": True,
        "supported_languages": ["python", "javascript", "typescript", "go", "java", "ruby", "php", "csharp"],
    }

# Made with Bob

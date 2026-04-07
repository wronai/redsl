"""Direct refactoring implementations for simple, deterministic changes."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class DirectRefactorEngine:
    """Applies simple refactorings directly via AST manipulation."""
    
    def __init__(self) -> None:
        self.applied_changes = []
    
    def remove_unused_imports(self, file_path: Path, unused_imports: list[str]) -> bool:
        """Remove unused imports from a Python file."""
        if not unused_imports:
            return False
        
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            
            # Find and remove unused imports
            transformer = UnusedImportRemover(unused_imports)
            new_tree = transformer.visit(tree)
            
            # Write back the modified source
            new_source = ast.unparse(new_tree)
            file_path.write_text(new_source, encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "remove_unused_imports",
                "details": f"Removed: {', '.join(unused_imports)}"
            })
            return True
            
        except Exception as e:
            print(f"Failed to remove unused imports from {file_path}: {e}")
            return False
    
    def fix_module_execution_block(self, file_path: Path) -> bool:
        """Wrap module-level code in if __name__ == '__main__' guard."""
        try:
            source = file_path.read_text(encoding="utf-8")
            lines = source.splitlines(keepends=True)
            
            # Find module execution blocks
            execution_lines = []
            in_main_guard = False
            has_main_guard = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Check for existing main guard
                if re.match(r'if\s+__name__\s*==\s*["\']__main__["\']', stripped):
                    in_main_guard = True
                    has_main_guard = True
                    continue
                
                # Skip comments, docstrings, imports, and definitions
                if (not stripped or 
                    stripped.startswith('#') or 
                    stripped.startswith('"""') or 
                    stripped.startswith("'''") or
                    stripped.startswith(('import ', 'from ')) or
                    stripped.startswith(('def ', 'class ', '@'))):
                    continue
                
                # If we're not in a main guard and this is executable code
                if not in_main_guard and (
                    stripped.startswith(('print(', 'assert ', 'raise ')) or
                    '(' in stripped or '=' in stripped
                ):
                    execution_lines.append(i)
                
                # Exit main guard
                if in_main_guard and stripped and not line[0].isspace():
                    in_main_guard = False
            
            if not execution_lines or has_main_guard:
                return False
            
            # Insert main guard before the first execution line
            first_line = execution_lines[0]
            indent = '    '
            
            # Insert the guard
            lines.insert(first_line, f'\nif __name__ == "__main__":\n')
            
            # Indent the execution lines
            for line_num in execution_lines:
                lines[line_num + 1] = indent + lines[line_num + 1]
            
            # Write back
            file_path.write_text(''.join(lines), encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "fix_module_execution_block",
                "details": f"Wrapped {len(execution_lines)} lines in main guard"
            })
            return True
            
        except Exception as e:
            print(f"Failed to fix module execution block in {file_path}: {e}")
            return False
    
    def extract_constants(self, file_path: Path, magic_numbers: list[tuple[int, int | float]]) -> bool:
        """Extract magic numbers into named constants."""
        if len(magic_numbers) < 3:  # Only worth it for multiple numbers
            return False
        
        try:
            source = file_path.read_text(encoding="utf-8")
            lines = source.splitlines(keepends=True)
            
            # Group numbers by value to create constants
            value_to_names = {}
            for line_num, value in magic_numbers:
                if value not in value_to_names:
                    # Generate a constant name
                    const_name = self._generate_constant_name(value, lines[line_num - 1])
                    value_to_names[value] = const_name
            
            # Add constants at the top of the file (after imports and docstring)
            insert_line = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    insert_line = i + 1
                elif line.strip() and not line.startswith(' ') and not line.startswith('#'):
                    if insert_line == 0:
                        insert_line = i
                    break
            
            # Insert constants
            constants_text = '\n' + '\n'.join(f"{name} = {value}" for value, name in sorted(value_to_names.items())) + '\n\n'
            lines.insert(insert_line, constants_text)
            
            # Replace magic numbers with constants
            for line_num, value in magic_numbers:
                const_name = value_to_names[value]
                lines[line_num - 1] = re.sub(r'\b' + re.escape(str(value)) + r'\b', const_name, lines[line_num - 1])
            
            # Write back
            file_path.write_text(''.join(lines), encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "extract_constants",
                "details": f"Extracted {len(value_to_names)} constants"
            })
            return True
            
        except Exception as e:
            print(f"Failed to extract constants from {file_path}: {e}")
            return False
    
    def _generate_constant_name(self, value: int | float, context: str) -> str:
        """Generate a meaningful constant name based on value and context."""
        # Try to infer from context
        context_lower = context.lower()
        
        if 'timeout' in context_lower or 'sleep' in context_lower:
            return f"TIMEOUT_{int(value)}"
        elif 'port' in context_lower:
            return f"PORT_{int(value)}"
        elif 'max' in context_lower:
            return f"MAX_{int(value)}"
        elif 'min' in context_lower:
            return f"MIN_{int(value)}"
        elif 'retry' in context_lower or 'attempt' in context_lower:
            return f"MAX_RETRIES"
        elif 'buffer' in context_lower:
            return f"BUFFER_SIZE"
        else:
            # Generic name
            return f"CONSTANT_{int(value)}"
    
    def add_return_types(self, file_path: Path, functions_missing_return: list[tuple[str, int]]) -> bool:
        """Add return type annotations to functions."""
        if not functions_missing_return:
            return False
        
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            
            # Add return types to functions
            transformer = ReturnTypeAdder(functions_missing_return)
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)
            
            # Write back the modified source
            new_source = ast.unparse(new_tree)
            file_path.write_text(new_source, encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "add_return_types",
                "details": f"Added return types to {len(functions_missing_return)} functions"
            })
            return True
            
        except Exception as e:
            print(f"Failed to add return types to {file_path}: {e}")
            return False
    
    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes."""
        return self.applied_changes


class ReturnTypeAdder(ast.NodeTransformer):
    """AST transformer to add return type annotations."""
    
    def __init__(self, functions_missing_return: list[tuple[str, int]]) -> None:
        self.functions_to_fix = {name for name, _ in functions_missing_return}
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add return type annotation to function."""
        self.generic_visit(node)
        
        if node.name in self.functions_to_fix and node.returns is None:
            # Simple heuristic: add '-> None' for functions without explicit return
            # This is a conservative approach - better than guessing wrong types
            node.returns = ast.Constant(value=None)
        
        return node
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Add return type annotation to async function."""
        self.generic_visit(node)
        
        if node.name in self.functions_to_fix and node.returns is None:
            node.returns = ast.Constant(value=None)
        
        return node


class UnusedImportRemover(ast.NodeTransformer):
    """AST transformer to remove unused imports."""
    
    def __init__(self, unused_imports: list[str]) -> None:
        self.unused_imports = set(unused_imports)
    
    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        """Remove unused imports from import statements."""
        new_aliases = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name not in self.unused_imports:
                new_aliases.append(alias)
        
        if new_aliases:
            node.names = new_aliases
            return node
        return None
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        """Remove unused imports from from...import statements."""
        if node.names[0].name == "*":
            return node  # Can't handle star imports
        
        new_aliases = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name not in self.unused_imports:
                new_aliases.append(alias)
        
        if new_aliases:
            node.names = new_aliases
            return node
        return None

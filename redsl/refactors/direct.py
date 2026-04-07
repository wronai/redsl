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
            tree = ast.parse(source)
            
            # Find module-level statements that need to be guarded
            module_level_lines = []
            
            for node in tree.body:
                # Check for function calls at module level
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    module_level_lines.append(node.lineno - 1)
                # Check for assignments that look like executable code
                elif isinstance(node, ast.Assign):
                    # Skip if it's an all-caps constant
                    is_constant = all(
                        isinstance(t, ast.Name) and t.id.isupper() 
                        for t in node.targets
                    )
                    if not is_constant:
                        module_level_lines.append(node.lineno - 1)
            
            if not module_level_lines:
                return False
            
            # Read lines and insert guard
            lines = source.splitlines(keepends=True)
            first_line = min(module_level_lines)
            
            # Insert the guard before the first execution line
            indent = '    '
            lines.insert(first_line, f'\nif __name__ == "__main__":\n')
            
            # Indent the execution lines
            for line_num in sorted(module_level_lines, reverse=True):
                adjusted_line = line_num + 1  # Account for inserted guard
                if adjusted_line < len(lines):
                    if not lines[adjusted_line].startswith(indent):
                        lines[adjusted_line] = indent + lines[adjusted_line]
            
            # Write back
            file_path.write_text(''.join(lines), encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "fix_module_execution_block",
                "details": f"Wrapped {len(module_level_lines)} lines in main guard"
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
                    # Check if line number is valid
                    if 0 <= line_num - 1 < len(lines):
                        # Generate a constant name
                        const_name = self._generate_constant_name(value, lines[line_num - 1])
                    else:
                        # Fallback to generic name if line is out of range
                        const_name = f"CONSTANT_{int(value) if isinstance(value, int) else 'FLOAT'}"
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
            
            # Track line offset after inserting constants
            line_offset = len(constants_text.splitlines())
            
            # Replace magic numbers with constants (adjust for line offset)
            for line_num, value in magic_numbers:
                const_name = value_to_names[value]
                adjusted_line_num = line_num - 1
                if adjusted_line_num >= insert_line:
                    adjusted_line_num += line_offset
                
                # Check if line number is still valid after adjustments
                if 0 <= adjusted_line_num < len(lines):
                    lines[adjusted_line_num] = re.sub(r'\b' + re.escape(str(value)) + r'\b', const_name, lines[adjusted_line_num])
            
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
            # Analyze function body to infer return type
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type
        
        return node
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Add return type annotation to async function."""
        self.generic_visit(node)
        
        if node.name in self.functions_to_fix and node.returns is None:
            # Analyze function body to infer return type
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type
        
        return node
    
    def _infer_return_type(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.expr | None:
        """Infer return type from function body."""
        # Look for return statements
        return_statements = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value is not None:
                    return_statements.append(child.value)
        
        # No explicit returns -> None
        if not return_statements:
            return ast.Name(id='None', ctx=ast.Load())
        
        # Check if all returns are the same type
        types = set()
        for ret in return_statements:
            if isinstance(ret, ast.Constant):
                if isinstance(ret.value, bool):
                    types.add('bool')
                elif isinstance(ret.value, int):
                    types.add('int')
                elif isinstance(ret.value, float):
                    types.add('float')
                elif isinstance(ret.value, str):
                    types.add('str')
                elif ret.value is None:
                    types.add('None')
            elif isinstance(ret, ast.Name):
                types.add(ret.id)
            elif isinstance(ret, ast.List):
                types.add('list')
            elif isinstance(ret, ast.Dict):
                types.add('dict')
            elif isinstance(ret, ast.Tuple):
                types.add('tuple')
            else:
                # Too complex to infer safely
                return None
        
        # If mixed types, don't infer
        if len(types) > 1:
            return None
        
        # Return the inferred type
        if types:
            type_name = types.pop()
            if type_name == 'None':
                return ast.Name(id='None', ctx=ast.Load())
            else:
                return ast.Name(id=type_name, ctx=ast.Load())
        
        return None


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

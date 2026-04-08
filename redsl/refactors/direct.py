"""Direct refactoring implementations for simple, deterministic changes."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from redsl.refactors.ast_transformers import ReturnTypeAdder, UnusedImportRemover


class DirectRefactorEngine:
    """Applies simple refactorings directly via AST manipulation."""
    
    def __init__(self) -> None:
        self.applied_changes = []
    
    def remove_unused_imports(self, file_path: Path, unused_imports: list[str]) -> bool:
        """Remove unused imports from a Python file.
        
        Uses line-based editing to preserve original formatting.
        """
        if not unused_imports:
            return False
        
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            unused_set = set(unused_imports)

            lines_to_remove, line_replacements = self._collect_unused_import_edits(
                tree, lines, unused_set
            )
            
            if not lines_to_remove and not line_replacements:
                return False
            
            new_source = self._apply_line_edits(lines, lines_to_remove, line_replacements)
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

    def _collect_unused_import_edits(
        self,
        tree: ast.Module,
        lines: list[str],
        unused_set: set[str],
    ) -> tuple[set[int], dict[int, str]]:
        """Collect line removals and replacements for unused import cleanup."""
        lines_to_remove: set[int] = set()  # 0-indexed
        line_replacements: dict[int, str] = {}  # 0-indexed -> new content

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                self._collect_import_edits(node, lines, unused_set, lines_to_remove, line_replacements)
            elif isinstance(node, ast.ImportFrom):
                self._collect_import_from_edits(node, lines, unused_set, lines_to_remove, line_replacements)

        return lines_to_remove, line_replacements

    def _collect_import_edits(
        self,
        node: ast.Import,
        lines: list[str],
        unused_set: set[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> None:
        kept = [alias for alias in node.names if self._alias_name(alias) not in unused_set]
        if len(kept) == len(node.names):
            return

        if not kept:
            self._remove_statement_lines(node, lines_to_remove)
            return

        names_str = ", ".join(self._format_alias(alias) for alias in kept)
        indent = self._get_indent(lines[node.lineno - 1])
        line_replacements[node.lineno - 1] = f"{indent}import {names_str}\n"
        self._remove_replaced_statement_lines(node, lines_to_remove)

    def _collect_import_from_edits(
        self,
        node: ast.ImportFrom,
        lines: list[str],
        unused_set: set[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> None:
        if node.names[0].name == "*":
            return

        kept = [alias for alias in node.names if self._alias_name(alias) not in unused_set]
        if len(kept) == len(node.names):
            return

        if not kept:
            self._remove_statement_lines(node, lines_to_remove)
            return

        indent = self._get_indent(lines[node.lineno - 1])
        module = node.module or ""
        dots = "." * (node.level or 0)
        end_lineno = getattr(node, "end_lineno", node.lineno)

        if end_lineno > node.lineno:
            names_lines = [
                f"{indent}    {self._format_alias(alias)},"
                for alias in kept
            ]
            replacement = (
                f"{indent}from {dots}{module} import (\n"
                + "\n".join(names_lines)
                + f"\n{indent})\n"
            )
            line_replacements[node.lineno - 1] = replacement
            self._remove_replaced_statement_lines(node, lines_to_remove)
        else:
            names_str = ", ".join(self._format_alias(alias) for alias in kept)
            line_replacements[node.lineno - 1] = (
                f"{indent}from {dots}{module} import {names_str}\n"
            )

    @staticmethod
    def _alias_name(alias: ast.alias) -> str:
        return alias.asname or alias.name

    @staticmethod
    def _format_alias(alias: ast.alias) -> str:
        return f"{alias.name} as {alias.asname}" if alias.asname else alias.name

    @staticmethod
    def _remove_statement_lines(node: ast.AST, lines_to_remove: set[int]) -> None:
        end_lineno = getattr(node, "end_lineno", node.lineno)
        for ln in range(node.lineno - 1, end_lineno):
            lines_to_remove.add(ln)

    @staticmethod
    def _remove_replaced_statement_lines(node: ast.AST, lines_to_remove: set[int]) -> None:
        end_lineno = getattr(node, "end_lineno", node.lineno)
        for ln in range(node.lineno, end_lineno):
            lines_to_remove.add(ln)

    def _apply_line_edits(
        self,
        lines: list[str],
        lines_to_remove: set[int],
        line_replacements: dict[int, str],
    ) -> str:
        new_lines = []
        for i, line in enumerate(lines):
            if i in lines_to_remove:
                continue
            if i in line_replacements:
                new_lines.append(line_replacements[i])
            else:
                new_lines.append(line)

        return self._clean_blank_lines("".join(new_lines))
    
    @staticmethod
    def _is_main_guard_node(node: ast.If) -> bool:
        """Return True if *node* is `if __name__ == '__main__':`."""
        test = node.test
        return (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        )

    @staticmethod
    def _get_indent(line: str) -> str:
        """Return the leading whitespace of a line."""
        return line[: len(line) - len(line.lstrip())]
    
    @staticmethod
    def _clean_blank_lines(source: str) -> str:
        """Remove runs of 3+ consecutive blank lines, keeping max 2."""
        result: list[str] = []
        blank_count = 0
        for line in source.splitlines(keepends=True):
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        return "".join(result)
    
    def fix_module_execution_block(self, file_path: Path) -> bool:
        """Wrap module-level code in if __name__ == '__main__' guard."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            
            # Find module-level statements that need to be guarded
            module_level_lines = []
            
            # Collect existing __main__ guard start lines so we skip them
            guarded_lines: set[int] = set()
            for node in tree.body:
                if isinstance(node, ast.If) and self._is_main_guard_node(node):
                    for child in ast.walk(node):
                        if hasattr(child, 'lineno'):
                            guarded_lines.add(child.lineno - 1)

            for node in tree.body:
                # Only guard bare function/method calls at module level.
                # Assignments (app = Typer(), TaskPattern = Task, etc.) are
                # intentional module-level state and must NOT be moved.
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    if (node.lineno - 1) not in guarded_lines:
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
            
            # Add constants after the last import statement.
            # Use AST end_lineno to correctly skip multi-line import blocks.
            tree_for_pos = ast.parse(source)
            insert_line = 0
            for node in tree_for_pos.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_line = node.end_lineno  # 1-indexed end of this import
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    pass  # docstring — keep scanning
                else:
                    break  # first non-import real statement
            
            # Insert constants
            constants_text = '\n' + '\n'.join(f"{name} = {value}" for value, name in sorted(value_to_names.items())) + '\n\n'
            lines.insert(insert_line, constants_text)
            
            # One element inserted into the lines list → all subsequent indices shift by 1
            line_offset = 1
            
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
        """Add return type annotations to functions.
        
        Uses line-based editing to preserve original formatting.
        """
        if not functions_missing_return:
            return False
        
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            lines = source.splitlines(keepends=True)
            
            # Build lookup: (func_name, lineno) pairs to fix
            to_fix = {(name, lineno) for name, lineno in functions_missing_return}
            
            # Infer return types via AST, then apply via line editing
            inferrer = ReturnTypeAdder(functions_missing_return)
            replacements: dict[int, str] = {}  # 0-indexed line -> new content
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (node.name, node.lineno) not in to_fix:
                        continue
                    if node.returns is not None:
                        continue
                    
                    ret_type = inferrer._infer_return_type(node)
                    if ret_type is None:
                        continue
                    type_str = ast.unparse(ret_type)
                    
                    # Find the "def ... :" line and insert -> Type before the colon
                    # The colon ending the signature could be on lineno or a later line
                    for ln in range(node.lineno - 1, min(node.end_lineno, len(lines))):
                        line = lines[ln]
                        # Find the colon that ends the def signature (not inside strings/parens)
                        colon_idx = self._find_def_colon(line, ln == node.lineno - 1)
                        if colon_idx is not None:
                            before = line[:colon_idx].rstrip()
                            after = line[colon_idx:]  # includes ':'
                            replacements[ln] = f"{before} -> {type_str}{after}"
                            break
            
            if not replacements:
                return False
            
            new_lines = []
            for i, line in enumerate(lines):
                if i in replacements:
                    new_lines.append(replacements[i])
                else:
                    new_lines.append(line)
            
            file_path.write_text("".join(new_lines), encoding="utf-8")
            
            self.applied_changes.append({
                "file": str(file_path),
                "action": "add_return_types",
                "details": f"Added return types to {len(functions_missing_return)} functions"
            })
            return True
            
        except Exception as e:
            print(f"Failed to add return types to {file_path}: {e}")
            return False
    
    @staticmethod
    def _find_def_colon(line: str, is_first_line: bool) -> int | None:
        """Find the index of the colon ending a def signature on this line.
        
        Skips colons inside strings and parentheses.
        Returns None if no signature-ending colon is found.
        """
        depth = 0
        in_string = None
        i = 0
        while i < len(line):
            ch = line[i]
            # Handle string delimiters
            if ch in ('"', "'"):
                triple = line[i:i+3]
                if triple in ('"""', "'''"):
                    if in_string == triple:
                        in_string = None
                        i += 3
                        continue
                    elif in_string is None:
                        in_string = triple
                        i += 3
                        continue
                if in_string is None:
                    in_string = ch
                elif in_string == ch:
                    in_string = None
                i += 1
                continue
            if in_string:
                i += 1
                continue
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ':' and depth == 0:
                # This is the signature-ending colon
                return i
            i += 1
        return None
    
    def get_applied_changes(self) -> list[dict[str, Any]]:
        """Get list of all applied changes."""
        return self.applied_changes


__all__ = ["DirectRefactorEngine", "ReturnTypeAdder", "UnusedImportRemover"]

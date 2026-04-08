"""AST-based transformer classes for deterministic code transformations."""

from __future__ import annotations

import ast


class ReturnTypeAdder(ast.NodeTransformer):
    """AST transformer to add return type annotations."""

    def __init__(self, functions_missing_return: list[tuple[str, int]]) -> None:
        self.functions_to_fix = {name for name, _ in functions_missing_return}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add return type annotation to function."""
        self.generic_visit(node)

        if node.name in self.functions_to_fix and node.returns is None:
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Add return type annotation to async function."""
        self.generic_visit(node)

        if node.name in self.functions_to_fix and node.returns is None:
            return_type = self._infer_return_type(node)
            if return_type:
                node.returns = return_type

        return node

    def _infer_return_type(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.expr | None:
        """Infer return type from function body."""
        return_statements = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                if child.value is not None:
                    return_statements.append(child.value)

        if not return_statements:
            return ast.Name(id='None', ctx=ast.Load())

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
                return None

        if len(types) > 1:
            return None

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
            return node

        new_aliases = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name not in self.unused_imports:
                new_aliases.append(alias)

        if new_aliases:
            node.names = new_aliases
            return node
        return None


__all__ = ["ReturnTypeAdder", "UnusedImportRemover"]

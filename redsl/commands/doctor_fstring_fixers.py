"""F-string fixers for project doctor."""

import ast
import re
from pathlib import Path

def _fix_broken_fstring(path: Path) -> bool:
    """Fix common broken f-string patterns (single brace, multiline issues)."""
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return False

    lines = src.splitlines(keepends=True)
    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for single '}' in f-string context
        if "f'" in line or 'f"' in line:
            if '}' in line and '{' not in line:
                # Likely a single closing brace — escape it
                new_line = line.replace('}', '}}')
                new_lines.append(new_line)
                changed = True
                i += 1
                continue

        # Check for multiline f-string start
        if (stripped.startswith("f'") or stripped.startswith('f"')) and not stripped.endswith(stripped[1]):
            quote = stripped[1]
            start_indent = len(line) - len(line.lstrip())
            body_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip().endswith(quote):
                    break
                body_lines.append(next_line)
                j += 1

            if j < len(lines) and body_lines:
                # Check body for unbalanced braces
                fixed_body = _fix_multiline_fstring_braces("".join(body_lines))
                if fixed_body != "".join(body_lines):
                    new_lines.append(line)
                    new_lines.append(fixed_body)
                    new_lines.append(lines[j])
                    changed = True
                    i = j + 1
                    continue

        new_lines.append(line)
        i += 1

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
        try:
            ast.parse("".join(new_lines))
            return True
        except SyntaxError:
            return False
    return False

def _fix_multiline_fstring_braces(src: str) -> str:
    """Fix unbalanced braces in multiline f-string body."""
    lines = src.splitlines(keepends=True)
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and '}' in stripped and '{' not in stripped and not stripped.startswith('#'):
            new_line = line.replace('}', '}}')
            new_lines.append(new_line)
        elif stripped and '{' in stripped and '}' not in stripped and not stripped.startswith('#'):
            new_line = line.replace('{', '{{')
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return "".join(new_lines)

def _escape_fstring_body_braces(body: str) -> str:
    """Escape unbalanced braces in f-string body content."""
    result: list[str] = []
    i = 0
    while i < len(body):
        if body[i] == '{':
            if i + 1 < len(body) and body[i + 1] == '{':
                result.append('{{')
                i += 2
            else:
                result.append('{{')
                i += 1
        elif body[i] == '}':
            if i + 1 < len(body) and body[i + 1] == '}':
                result.append('}}')
                i += 2
            else:
                result.append('}}')
                i += 1
        else:
            result.append(body[i])
            i += 1
    return "".join(result)

def _is_fstring_expr(inner: str) -> bool:
    """Check if content inside f-string braces is a valid expression."""
    return any(c.isalnum() or c in '._' for c in inner)

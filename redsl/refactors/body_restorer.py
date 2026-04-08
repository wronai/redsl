"""Repair stolen class/function bodies caused by FIX_MODULE_EXECUTION_BLOCK bug.

Pattern being fixed (both variants):

  A) SyntaxError — body completely stolen:
       class Foo:
       if __name__ == "__main__":
           MEMBER = value

  B) MIDFILE — docstring-only class, members in guard:
       class Foo:
           \"\"\"docs.\"\"\"

       if __name__ == "__main__":
           MEMBER = value

  Fix: un-indent the guard body by 4 spaces and inject it after the preceding
  class/function/try definition, then remove the guard.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_GUARD_RE = re.compile(r'^if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:\s*$')
_DEF_RE = re.compile(r'^(class|def|async\s+def|try)\s*')


def _find_preceding_def(lines: list[str], guard_idx: int) -> int | None:
    """Return 0-based index of the last class/def/try that precedes guard_idx."""
    for k in range(guard_idx - 1, -1, -1):
        stripped = lines[k].rstrip()
        if stripped and _DEF_RE.match(stripped) and stripped.endswith(':'):
            return k
    return None


def _body_after_def(lines: list[str], def_idx: int, guard_idx: int) -> list[str]:
    """Return non-blank lines between def and guard."""
    return [l for l in lines[def_idx + 1 : guard_idx] if l.strip()]


def _collect_guard_body(lines: list[str], guard_idx: int) -> tuple[list[str], int]:
    """Collect indented body lines of the if-guard; return (body_lines, next_idx)."""
    body: list[str] = []
    j = guard_idx + 1
    while j < len(lines):
        bl = lines[j]
        if bl.strip() == "" or bl.startswith("    ") or bl.startswith("\t"):
            body.append(bl)
            j += 1
        else:
            break
    # Strip trailing blank lines
    while body and not body[-1].strip():
        body.pop()
    return body, j


def _unindent_4(line: str) -> str:
    """Remove exactly 4 leading spaces (or 1 tab)."""
    if line.startswith("    "):
        return line[4:]
    if line.startswith("\t"):
        return line[1:]
    return line


def _is_docstring_only(body_lines: list[str]) -> bool:
    """Return True if the body contains at most a docstring and nothing else."""
    code = [l.strip() for l in body_lines if l.strip()]
    if not code:
        return True

    first = code[0]
    # Single-line docstring: starts AND ends with triple-quote on one line
    for q in ('"""', "'''"):
        if first.startswith(q):
            # Find where the triple-quote closes
            close = first.find(q, len(q))
            if close != -1:
                # Closed on the same line — no more code should follow
                return len(code) == 1
            # Open triple-quote without close on first line → multi-line docstring
            # Scan remaining lines for the closing quote
            for i, cl in enumerate(code[1:], 1):
                if q in cl:
                    # Closing quote found — everything after this must be absent
                    return i == len(code) - 1
            # Never closed — not a valid docstring
            return False

    return False


def repair_file(path: Path) -> bool:
    """Attempt to restore stolen class/function bodies in *path*.

    Returns True if any fixes were applied.
    """
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    lines = src.splitlines(keepends=True)
    new_lines: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]

        if _GUARD_RE.match(line.rstrip()) and not line.startswith(" "):
            guard_idx_in_orig = i
            guard_body, next_i = _collect_guard_body(lines, i)

            if not guard_body:
                new_lines.append(line)
                i += 1
                continue

            # Find preceding def in the ORIGINAL lines
            def_idx = _find_preceding_def(lines, guard_idx_in_orig)

            if def_idx is not None:
                between = _body_after_def(lines, def_idx, guard_idx_in_orig)

                if _is_docstring_only(between):
                    # Restore: emit guard body AS-IS (indentation is already correct
                    # for the class/function body — the guard's 4-space indent equals
                    # the required body indent for top-level definitions)
                    restored = list(guard_body)
                    if restored and not restored[-1].endswith("\n"):
                        restored[-1] += "\n"
                    new_lines.extend(restored)
                    new_lines.append("\n")
                    i = next_i
                    changed = True
                    continue

            # Guard not preceded by an empty definition — keep it
            new_lines.append(line)
            i += 1
        else:
            new_lines.append(line)
            i += 1

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")

    return changed


def repair_directory(root: Path, dry_run: bool = False) -> list[tuple[str, str]]:
    """Walk *root* and repair all damaged Python files.

    Returns list of (path, status) for all processed files.
    """
    _SKIP_DIRS = {"__pycache__", "venv", ".venv", ".tox", "node_modules",
                  "build", "dist", ".git", "examples", "invalid"}

    results: list[tuple[str, str]] = []

    for py in sorted(root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in py.parts):
            continue
        if dry_run:
            status = "skipped (dry-run)"
        else:
            try:
                fixed = repair_file(py)
                status = "fixed" if fixed else "ok"
            except Exception as exc:
                status = f"error: {exc}"
        results.append((str(py), status))

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Restore stolen class/function bodies")
    parser.add_argument("root", nargs="?", default="/home/tom/github/semcod",
                        help="Directory to scan (default: /home/tom/github/semcod)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    results = repair_directory(root, dry_run=args.dry_run)

    fixed = [(p, s) for p, s in results if s == "fixed"]
    errors = [(p, s) for p, s in results if s.startswith("error")]

    for p, s in fixed:
        print(f"FIXED  {p}")
    for p, s in errors:
        print(f"ERROR  {p}: {s}", file=sys.stderr)

    print(f"\n{len(fixed)} fixed, {len(errors)} errors, {len(results)} scanned")

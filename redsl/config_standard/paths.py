"""Path helpers for redsl config documents and proposals."""

from __future__ import annotations

import copy
import re
from collections.abc import Iterable
from typing import Any

_PATH_TOKEN_RE = re.compile(r"([^[.\]]+)|\[(\d+)\]")


def parse_config_path(path: str) -> list[str | int]:
    """Parse a dotted / indexed config path into navigation tokens."""
    if not path or not path.strip():
        raise ValueError("Path cannot be empty")

    tokens: list[str | int] = []
    for part in path.split("."):
        for match in _PATH_TOKEN_RE.finditer(part):
            name, index = match.groups()
            if name is not None:
                tokens.append(name)
            elif index is not None:
                tokens.append(int(index))
    if not tokens:
        raise ValueError(f"Could not parse config path: {path!r}")
    return tokens


def _navigate(
    data: Any, tokens: list[str | int], *, create_missing: bool = False
) -> tuple[Any, str | int]:
    if not tokens:
        raise ValueError("Path must contain at least one token")

    current = data
    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(current, list):
                raise TypeError(f"Expected list while navigating through {token!r}")
            if token < 0:
                raise IndexError(token)
            if token >= len(current):
                if not create_missing:
                    raise IndexError(token)
                while len(current) <= token:
                    current.append({})
            current = current[token]
        else:
            if not isinstance(current, dict):
                raise TypeError(f"Expected mapping while navigating through {token!r}")
            if token not in current:
                if not create_missing:
                    raise KeyError(token)
                current[token] = {}
            current = current[token]
    return current, tokens[-1]


def get_nested_value(data: Any, path: str, *, default: Any = None) -> Any:
    tokens = parse_config_path(path)
    current = data
    try:
        for token in tokens:
            if isinstance(token, int):
                current = current[token]
            else:
                current = current[token]
    except (KeyError, IndexError, TypeError):
        return default
    return current


def set_nested_value(
    data: Any, path: str, value: Any, *, allow_create: bool = True, add: bool = False
) -> None:
    tokens = parse_config_path(path)
    parent, final_token = _navigate(data, tokens, create_missing=allow_create)

    if isinstance(final_token, int):
        if not isinstance(parent, list):
            raise TypeError(f"Expected list at {path!r}")
        if final_token < 0:
            raise IndexError(final_token)
        if final_token > len(parent):
            if not allow_create:
                raise IndexError(final_token)
            while len(parent) < final_token:
                parent.append(None)
        if final_token == len(parent):
            parent.append(value)
        else:
            parent[final_token] = value
        return

    if not isinstance(parent, dict):
        raise TypeError(f"Expected mapping at {path!r}")

    if add and final_token in parent and not allow_create:
        raise KeyError(f"Path already exists: {path}")
    parent[final_token] = value


def remove_nested_value(data: Any, path: str) -> Any:
    tokens = parse_config_path(path)
    parent, final_token = _navigate(data, tokens, create_missing=False)

    if isinstance(final_token, int):
        if not isinstance(parent, list):
            raise TypeError(f"Expected list at {path!r}")
        if final_token < 0 or final_token >= len(parent):
            raise IndexError(final_token)
        return parent.pop(final_token)

    if not isinstance(parent, dict):
        raise TypeError(f"Expected mapping at {path!r}")
    return parent.pop(final_token)


def deep_merge(base: Any, overlay: Any) -> Any:
    """Recursively merge *overlay* into *base* and return a new object."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = copy.deepcopy(base)
        for key, value in overlay.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    if overlay is None:
        return copy.deepcopy(base)
    return copy.deepcopy(overlay)


def deep_diff(base: Any, current: Any) -> Any:
    """Return the minimal overlay needed to transform *base* into *current*."""
    if isinstance(base, dict) and isinstance(current, dict):
        diff: dict[str, Any] = {}
        for key in current:
            if key not in base:
                diff[key] = copy.deepcopy(current[key])
                continue
            child_diff = deep_diff(base[key], current[key])
            if child_diff != _NO_DIFF:
                diff[key] = child_diff
        return diff if diff else _NO_DIFF

    if isinstance(base, list) and isinstance(current, list):
        return current if base != current else _NO_DIFF

    return current if base != current else _NO_DIFF


_NO_DIFF = object()


def materialize_diff(base: Any, current: Any) -> Any:
    """Public wrapper around :func:`deep_diff` that always returns JSON-friendly data."""
    diff = deep_diff(base, current)
    if diff is _NO_DIFF:
        return {}
    return diff


def walk_paths(data: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield dotted paths for scalar leaves in a nested mapping/list tree."""
    if isinstance(data, dict):
        for key, value in data.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from walk_paths(value, child_prefix)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            child_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from walk_paths(value, child_prefix)
    else:
        yield prefix, data


__all__ = [
    "deep_diff",
    "deep_merge",
    "get_nested_value",
    "materialize_diff",
    "parse_config_path",
    "remove_nested_value",
    "set_nested_value",
    "walk_paths",
]

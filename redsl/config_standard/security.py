"""Secret redaction helpers for config and debug flows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "openrouter_key": re.compile(r"sk-or-v1-[a-zA-Z0-9]{16,}"),
    "openai_key": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "anthropic_key": re.compile(r"sk-ant-[a-zA-Z0-9\-_]{20,}"),
    "generic_jwt": re.compile(r"eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+"),
    "bearer_token": re.compile(r"[Bb]earer\s+[a-zA-Z0-9_\-\.]{20,}"),
}

SENSITIVE_KEY_HINTS = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASS",
    "API_KEY",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "AUTH",
)

SENSITIVE_KEY_PREFIXES = (
    "OPENAI_",
    "OPENROUTER_",
    "ANTHROPIC_",
    "XAI_",
    "AWS_",
    "GITHUB_",
    "GITLAB_",
)


@dataclass(slots=True)
class SecretMatch:
    pattern_name: str
    placeholder: str
    original: str
    start: int
    end: int


class SecretInterceptor:
    """Redact secret-looking substrings before data is shown to an LLM."""

    def __init__(self) -> None:
        self._vault: dict[str, str] = {}
        self._counter = 0

    def redact(self, text: str) -> tuple[str, list[SecretMatch]]:
        """Return redacted text and match metadata."""
        if not text:
            return text, []

        spans: list[tuple[int, int, str, str]] = []
        seen: set[tuple[int, int, str]] = set()
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                key = (match.start(), match.end(), name)
                if key in seen:
                    continue
                seen.add(key)
                spans.append((match.start(), match.end(), name, match.group(0)))

        if not spans:
            return text, []

        spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        chunks: list[str] = []
        matches: list[SecretMatch] = []
        last_index = 0
        for start, end, pattern_name, original in spans:
            if start < last_index:
                continue
            chunks.append(text[last_index:start])
            self._counter += 1
            placeholder = f"[REDACTED_SECRET_{self._counter}]"
            self._vault[placeholder] = original
            chunks.append(placeholder)
            matches.append(
                SecretMatch(
                    pattern_name=pattern_name,
                    placeholder=placeholder,
                    original=original,
                    start=start,
                    end=end,
                )
            )
            last_index = end
        chunks.append(text[last_index:])
        return "".join(chunks), matches

    def resolve(self, placeholder: str) -> str:
        """Resolve a placeholder back to the original secret."""
        if placeholder not in self._vault:
            raise ValueError(f"Unknown placeholder: {placeholder}")
        return self._vault[placeholder]

    def clear(self) -> None:
        """Wipe all captured secrets from the local vault."""
        self._vault.clear()


def is_sensitive_key(key: str) -> bool:
    upper = key.upper()
    return upper.startswith(SENSITIVE_KEY_PREFIXES) or any(
        hint in upper for hint in SENSITIVE_KEY_HINTS
    )


def mask_sensitive_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with secret-like values masked."""
    masked: dict[str, Any] = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            masked[key] = "<redacted>"
            continue
        if isinstance(value, str):
            interceptor = SecretInterceptor()
            redacted, _ = interceptor.redact(value)
            masked[key] = redacted
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_mapping(value)
        else:
            masked[key] = value
    return masked


__all__ = [
    "SECRET_PATTERNS",
    "SENSITIVE_KEY_HINTS",
    "SENSITIVE_KEY_PREFIXES",
    "SecretInterceptor",
    "SecretMatch",
    "is_sensitive_key",
    "mask_sensitive_mapping",
]

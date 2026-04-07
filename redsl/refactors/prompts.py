"""
Szablony promptów dla silnika refaktoryzacji.
"""

from __future__ import annotations

from redsl.dsl import RefactorAction

PROMPTS = {
    RefactorAction.EXTRACT_FUNCTIONS: """
You are an expert Python refactoring assistant.
Your task: EXTRACT smaller functions from a complex function.

RULES:
- Keep behavior IDENTICAL (no behavioral changes!)
- Each extracted function should have a single responsibility
- Use descriptive names (verb_noun pattern)
- Preserve all error handling and logging
- Add type hints to new functions
- DO NOT change public API signatures
- DO NOT remove tests, configuration, or logging

Target function: {function_name}
Current cyclomatic complexity: {cc}
Target: CC < 10 per function

File: {file_path}
Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "extract_functions",
    "summary": "human-readable description of changes",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "full refactored file content",
            "description": "what changed and why"
        }}
    ]
}}
""",

    RefactorAction.SPLIT_MODULE: """
You are an expert Python refactoring assistant.
Your task: SPLIT a god module into smaller, focused modules.

RULES:
- Keep ALL existing imports working (use re-exports in __init__.py if needed)
- Group by responsibility (routes, business logic, models, utilities)
- Each new module should be < 200 lines
- Preserve all public APIs
- Create proper __init__.py with re-exports

Current module: {file_path} ({lines} lines, {functions} functions)

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "split_module",
    "summary": "description of the split strategy",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "new/module/path.py",
            "refactored_code": "content of the new file",
            "description": "what this module contains"
        }}
    ]
}}
""",

    RefactorAction.DEDUPLICATE: """
You are an expert Python refactoring assistant.
Your task: DEDUPLICATE code by extracting common logic.

RULES:
- Create a shared utility module for the common code
- Update all files that use the duplicated code to import from the shared module
- Keep behavior IDENTICAL
- Preserve all function signatures

Duplicate found in:
{duplicate_files}

Duplicate code ({dup_lines} lines, similarity: {similarity}):
```python
{dup_code}
```

Return JSON:
{{
    "refactor_type": "deduplicate",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "shared/module.py",
            "refactored_code": "content",
            "description": "shared utility"
        }},
        {{
            "file_path": "original/file.py",
            "refactored_code": "updated content importing from shared",
            "description": "updated to use shared module"
        }}
    ]
}}
""",

    RefactorAction.REDUCE_FAN_OUT: """
You are an expert Python refactoring assistant.
Your task: REDUCE fan-out by introducing facade or mediator pattern.

RULES:
- Introduce a facade/mediator to reduce direct dependencies
- Keep behavior IDENTICAL
- New abstractions should be well-named and documented

Function: {function_name}
Current fan-out: {fan_out}
Target: fan-out < 10

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "reduce_fan_out",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
""",

    RefactorAction.SIMPLIFY_CONDITIONALS: """
You are an expert Python refactoring assistant.
Your task: SIMPLIFY complex conditional logic.

TECHNIQUES to apply:
- Early return / guard clauses
- Replace nested if/else with match/case or dictionary dispatch
- Extract complex conditions into named boolean functions
- Reduce nesting depth to maximum 3

Function: {function_name}
Current CC: {cc}

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "simplify_conditionals",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
""",
}

# Domyślny prompt dla akcji bez dedykowanego szablonu
DEFAULT_PROMPT = """
You are an expert Python refactoring assistant.
Task: {action}
Target: {file_path}
{extra_context}

RULES:
- Keep behavior IDENTICAL
- Improve code quality without breaking anything
- Add type hints where missing
- Follow PEP 8

Code:
```python
{code}
```

Return JSON:
{{
    "refactor_type": "{action}",
    "summary": "description",
    "confidence": 0.0-1.0,
    "changes": [
        {{
            "file_path": "{file_path}",
            "refactored_code": "content",
            "description": "what changed"
        }}
    ]
}}
"""

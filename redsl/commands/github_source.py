"""GitHub source adapter for planfile sync.

Fetches issues from GitHub REST API and maps them to PlanTask-compatible dicts
with external_id, external_fingerprint, and source metadata.

Never logs or stores tokens in plaintext — auth is resolved via auth_ref
(env:VARNAME, file:PATH, or keyring:SERVICE/KEY) through ``resolve_auth_ref``.

Public API
----------
    resolve_auth_ref(auth_ref: str) -> str
    fetch_issues(source_config: dict) -> list[dict]
    fingerprint_issue(issue: dict) -> str
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Auth resolution
# ---------------------------------------------------------------------------

def resolve_auth_ref(auth_ref: str) -> str:
    """Resolve an auth_ref string to a plaintext token.

    Supported schemes:
        env:VARNAME          — read from environment variable
        file:PATH            — read from file (first line, stripped)
        keyring:SERVICE/KEY  — read from system keyring (requires keyring package)

    The returned token is NEVER written to disk or included in any log message.
    """
    if not auth_ref:
        raise ValueError("auth_ref is empty")

    if auth_ref.startswith("env:"):
        var = auth_ref[4:]
        token = os.environ.get(var)
        if not token:
            raise ValueError(
                f"Environment variable {var!r} is not set. "
                f"Set it before running: export {var}=<your_token>"
            )
        return token

    if auth_ref.startswith("file:"):
        path = Path(auth_ref[5:]).expanduser()
        if not path.exists():
            raise ValueError(f"Token file not found: {path}")
        return path.read_text(encoding="utf-8").splitlines()[0].strip()

    if auth_ref.startswith("keyring:"):
        # service/key format
        service_key = auth_ref[8:]
        if "/" not in service_key:
            raise ValueError("keyring auth_ref must be keyring:SERVICE/KEY")
        service, key = service_key.split("/", 1)
        try:
            import keyring  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "Install 'keyring' package to use keyring auth: pip install keyring"
            ) from exc
        token = keyring.get_password(service, key)
        if not token:
            raise ValueError(f"No token found in keyring for {service}/{key}")
        return token

    raise ValueError(
        f"Unknown auth_ref scheme: {auth_ref!r}. "
        "Supported: env:VARNAME, file:PATH, keyring:SERVICE/KEY"
    )


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------

def fingerprint_issue(issue: dict[str, Any]) -> str:
    """Compute a stable fingerprint of the externally-visible issue state.

    Only fields that matter for conflict detection are hashed:
    title, state, label names, assignee login, body hash.

    Returns:   sha256:<hex>
    """
    body = issue.get("body") or ""
    body_hash = hashlib.sha256(body.encode()).hexdigest()[:16]

    key_data = {
        "title": issue.get("title", ""),
        "state": issue.get("state", ""),
        "labels": sorted(lb["name"] for lb in issue.get("labels", [])),
        "assignee": (issue.get("assignee") or {}).get("login", ""),
        "body_hash": body_hash,
    }
    raw = json.dumps(key_data, sort_keys=True, ensure_ascii=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"sha256:{digest}"


# ---------------------------------------------------------------------------
# Fetch issues
# ---------------------------------------------------------------------------

def fetch_issues(source_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch issues from GitHub according to source_config.

    Returns a list of normalised issue dicts with keys:
        external_id, external_fingerprint, title, status, priority,
        labels, url, number, assignee, body_snippet
    """
    import urllib.request
    import urllib.parse

    repo = source_config.get("repo", "")
    if not repo or "/" not in repo:
        raise ValueError(f"source.repo must be 'owner/repo', got: {repo!r}")

    auth_ref = source_config.get("auth_ref", "")
    token = resolve_auth_ref(auth_ref) if auth_ref else None
    headers = _build_headers(token)
    first_url = _build_url(repo, source_config.get("filters") or {})

    logger.debug("Fetching issues from %s", repo)
    all_issues = _fetch_all_pages(first_url, headers, source_config["id"], urllib)
    logger.debug("Fetched %d issues from %s", len(all_issues), repo)
    return all_issues


def _build_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "redsl-planfile/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _build_url(repo: str, filters: dict[str, Any]) -> str:
    import urllib.parse
    state = filters.get("state", "open")
    params: dict[str, str] = {"state": state, "per_page": "100"}
    if filters.get("labels"):
        params["labels"] = ",".join(filters["labels"])
    if filters.get("assignee"):
        params["assignee"] = filters["assignee"]
    if filters.get("milestone") is not None:
        params["milestone"] = str(filters["milestone"])
    return f"{_GITHUB_API}/repos/{repo}/issues?" + urllib.parse.urlencode(params)


def _fetch_all_pages(
    start_url: str,
    headers: dict[str, str],
    source_id: str,
    urllib: Any,
) -> list[dict[str, Any]]:
    """Follow GitHub pagination and collect all normalised issues."""
    all_issues: list[dict[str, Any]] = []
    current_url: str | None = start_url

    while current_url:
        req = urllib.request.Request(current_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                page_data = json.loads(resp.read().decode())
                current_url = _parse_next_link(resp.headers.get("Link", ""))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            raise RuntimeError(
                f"GitHub API error {exc.code}: {body[:200]}"
            ) from exc

        for issue in page_data:
            if "pull_request" not in issue:
                all_issues.append(_normalise_issue(issue, source_id))

    return all_issues


def _parse_next_link(link_header: str) -> str | None:
    """Parse GitHub Link header to find next page URL."""
    if not link_header:
        return None
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            url_part = part.split(";")[0].strip()
            if url_part.startswith("<") and url_part.endswith(">"):
                return url_part[1:-1]
    return None


def _normalise_issue(issue: dict[str, Any], source_id: str) -> dict[str, Any]:
    """Map a raw GitHub issue to the planfile external task format."""
    labels = [lb["name"] for lb in issue.get("labels", [])]

    # Map GH state → planfile status
    gh_state = issue.get("state", "open")
    status = "todo" if gh_state == "open" else "done"

    # Heuristic priority from labels
    priority = _priority_from_labels(labels)

    body = issue.get("body") or ""
    body_snippet = body[:200].replace("\n", " ").strip() if body else ""

    return {
        "source": source_id,
        "external_id": f"{issue.get('repo_full_name', source_id)}#{issue['number']}",
        "external_fingerprint": fingerprint_issue(issue),
        "number": issue["number"],
        "title": issue.get("title", ""),
        "status": status,
        "priority": priority,
        "labels": labels,
        "url": issue.get("html_url", ""),
        "assignee": (issue.get("assignee") or {}).get("login", ""),
        "body_snippet": body_snippet,
    }


def _priority_from_labels(labels: list[str]) -> int:
    """Derive planfile priority (1–4) from GitHub label names."""
    lowered = {lb.lower() for lb in labels}
    if lowered & {"critical", "blocker", "p0", "priority: critical"}:
        return 1
    if lowered & {"high", "p1", "priority: high", "important"}:
        return 2
    if lowered & {"low", "p3", "priority: low", "nice-to-have", "wontfix"}:
        return 4
    return 3  # medium default

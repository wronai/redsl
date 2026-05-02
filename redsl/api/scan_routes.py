"""Remote scan endpoints for analyzing repositories by URL."""

from __future__ import annotations

import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ScanRepoRequest(BaseModel):
    """Request to scan a remote repository."""
    repo_url: str = Field(description="Git repository URL (https or ssh)")
    branch: str = Field("main", description="Branch to checkout")
    depth: int = Field(1, description="Clone depth (1 for shallow)")


class ScanRepoResponse(BaseModel):
    """Response from remote repository scan."""
    status: str
    repo_url: str
    total_files: int
    total_lines: int
    avg_cc: float
    critical_count: int
    alerts: list[dict]
    top_issues: list[dict]
    summary: str


def _clone_repo(repo_url: str, branch: str = "main", depth: int = 1) -> Path | None:
    """Clone a repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="redsl_scan_")
    logger.info("Starting clone of %s to %s", repo_url, temp_dir)
    try:
        # Check if git is available
        git_check = subprocess.run(["git", "--version"], capture_output=True, timeout=5)
        if git_check.returncode != 0:
            logger.error("Git not available: %s", git_check.stderr.decode()[:200])
            return None
        
        cmd = [
            "git", "clone",
            "--depth", str(depth),
            "--branch", branch,
            "--single-branch",
            "--no-tags",
            repo_url,
            temp_dir
        ]
        logger.info("Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for larger repos
        )
        if result.returncode == 0:
            logger.info("Clone successful: %s", temp_dir)
            return Path(temp_dir)
        
        logger.warning("Clone failed with rc=%d: %s", result.returncode, result.stderr[:500])
        
        # Try with 'master' branch if main fails
        if branch == "main":
            logger.info("Trying 'master' branch instead of 'main'")
            # Need to cleanup first
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = tempfile.mkdtemp(prefix="redsl_scan_")
            cmd_master = [
                "git", "clone",
                "--depth", str(depth),
                "--branch", "master",
                "--single-branch",
                "--no-tags",
                repo_url,
                temp_dir
            ]
            result = subprocess.run(cmd_master, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info("Clone with master branch successful")
                return Path(temp_dir)
            logger.error("Master branch also failed: %s", result.stderr[:500])
        
        # Try default branch (no --branch specified)
        logger.info("Trying default branch (no --branch)")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir = tempfile.mkdtemp(prefix="redsl_scan_")
        cmd_default = ["git", "clone", "--depth", str(depth), repo_url, temp_dir]
        result = subprocess.run(cmd_default, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info("Clone with default branch successful")
            return Path(temp_dir)
        
        logger.error("All clone attempts failed for %s: %s", repo_url, result.stderr[:500])
        return None
    except subprocess.TimeoutExpired:
        logger.error("Clone timeout for %s after 300s", repo_url)
        return None
    except Exception as e:
        logger.exception("Clone error for %s", repo_url)
        return None


def _cleanup_repo(repo_path: Path | None) -> None:
    """Clean up temporary repository."""
    if repo_path and repo_path.exists():
        try:
            import shutil
            shutil.rmtree(repo_path, ignore_errors=True)
        except Exception as e:
            logger.debug("Cleanup error: %s", e)


def _validate_repo_url(repo_url: str) -> bool:
    """Validate repository URL format."""
    try:
        parsed = urlparse(repo_url)
        # Allow https://github.com/... or git@github.com:...
        if parsed.scheme == 'https' and parsed.netloc:
            return True
        if repo_url.startswith('git@') and ':' in repo_url:
            return True
        # Allow file:// URLs for local testing
        if parsed.scheme == 'file':
            return True
        return False
    except Exception:
        return False


def _extract_top_issues(analysis: dict, limit: int = 5) -> list[dict]:
    """Extract top issues from analysis for outreach templates."""
    issues = []
    alerts = analysis.get('alerts', [])
    
    for alert in alerts[:limit]:
        # Alerts are dicts from AnalysisResult
        issue = {
            'type': alert.get('type', 'unknown') if isinstance(alert, dict) else 'unknown',
            'name': alert.get('name', 'unknown') if isinstance(alert, dict) else str(alert),
            'severity': alert.get('severity', 1) if isinstance(alert, dict) else 1,
            'value': alert.get('value', 0) if isinstance(alert, dict) else 0,
            'limit': alert.get('limit', 10) if isinstance(alert, dict) else 10,
            'message': alert.get('message', '') if isinstance(alert, dict) else '',
        }
        
        # Add human-readable description
        if issue['type'] == 'cc_exceeded':
            issue['description'] = (
                f"Funkcja `{issue['name']}` ma złożoność CC={issue['value']} "
                f"(norma to max {issue['limit']}) — każda zmiana to ryzyko"
            )
        elif issue['type'] == 'duplication':
            issue['description'] = (
                f"Znaleziono duplikację kodu — można wyekstraktować wspólną funkcję"
            )
        else:
            issue['description'] = f"{issue['type']}: {issue['name']}"
        
        issues.append(issue)
    
    return issues


def _generate_summary(analysis: dict) -> str:
    """Generate human-readable summary of analysis."""
    files = analysis.get('total_files', 0)
    lines = analysis.get('total_lines', 0)
    cc = analysis.get('avg_cc', 0)
    critical = analysis.get('critical_count', 0)
    
    parts = []
    if files > 0:
        parts.append(f"{files} plików")
    if lines > 0:
        parts.append(f"{lines:,} linii kodu".replace(",", " "))
    if cc > 0:
        parts.append(f"średnia CC={cc:.1f}")
    if critical > 0:
        parts.append(f"{critical} krytycznych problemów")
    
    return ", ".join(parts) if parts else "Brak danych"


def _register_scan_routes(app: Any) -> None:
    """Register remote scan endpoints."""
    from fastapi import HTTPException
    
    @app.post("/scan/remote", response_model=ScanRepoResponse)
    async def scan_remote(req: ScanRepoRequest):
        """Scan a remote repository by URL.
        
        Clones the repo temporarily, analyzes it, and returns metrics.
        Useful for marketing outreach and initial assessment.
        """
        # Validate URL
        if not _validate_repo_url(req.repo_url):
            raise HTTPException(status_code=400, detail="Invalid repository URL")
        
        # Clone repository
        repo_path = _clone_repo(req.repo_url, req.branch, req.depth)
        if repo_path is None:
            raise HTTPException(status_code=400, detail="Failed to clone repository")
        
        try:
            # Analyze the cloned repo
            from redsl.analyzers import CodeAnalyzer
            
            analyzer = CodeAnalyzer()
            analysis = analyzer.analyze_project(repo_path)
            
            # AnalysisResult has alerts as list[dict] already
            analysis_dict = {
                'total_files': getattr(analysis, 'total_files', 0),
                'total_lines': getattr(analysis, 'total_lines', 0),
                'avg_cc': getattr(analysis, 'avg_cc', 0),
                'critical_count': getattr(analysis, 'critical_count', 0),
                'alerts': analysis.alerts if analysis.alerts else [],
            }
            
            top_issues = _extract_top_issues(analysis_dict)
            summary = _generate_summary(analysis_dict)
            
            return ScanRepoResponse(
                status="success",
                repo_url=req.repo_url,
                total_files=analysis_dict['total_files'],
                total_lines=analysis_dict['total_lines'],
                avg_cc=analysis_dict['avg_cc'],
                critical_count=analysis_dict['critical_count'],
                alerts=analysis_dict['alerts'],
                top_issues=top_issues,
                summary=summary,
            )
            
        except Exception as e:
            logger.exception("Analysis error for %s", req.repo_url)
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        finally:
            _cleanup_repo(repo_path)

"""Scheduler — periodic self-improvement loop.

Three modes:
  watch      — monitor and alert only
  suggest    — monitor + generate dry-run proposals
  autonomous — monitor + apply changes + create PR
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AutonomyMode(str, Enum):
    WATCH = "watch"
    SUGGEST = "suggest"
    AUTONOMOUS = "autonomous"


class Scheduler:
    """Periodic quality-improvement loop."""

    def __init__(
        self,
        project_dir: Path,
        mode: AutonomyMode = AutonomyMode.SUGGEST,
        check_interval_minutes: int = 30,
        max_actions_per_cycle: int = 3,
    ) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.mode = mode
        self.interval = check_interval_minutes * 60
        self.max_actions = max_actions_per_cycle
        self._cycle_count = 0
        self._last_head: str | None = None
        self._running = False

    async def run(self) -> None:
        """Main scheduler loop — runs until stopped."""
        self._running = True
        logger.info(
            "Scheduler started: project=%s, mode=%s, interval=%ds",
            self.project_dir, self.mode.value, self.interval,
        )

        while self._running:
            self._cycle_count += 1
            try:
                if not self._has_changes_since_last_check():
                    logger.debug("Cycle %d: no changes, sleeping.", self._cycle_count)
                    await asyncio.sleep(self.interval)
                    continue

                analysis = self._analyze()
                trends = self._check_trends()
                proactive = self._check_proactive()

                if self.mode == AutonomyMode.WATCH:
                    self._report_findings(analysis, trends, proactive)

                elif self.mode == AutonomyMode.SUGGEST:
                    proposals = self._generate_proposals(analysis)
                    self._save_proposals(proposals)
                    self._report_findings(analysis, trends, proactive)

                elif self.mode == AutonomyMode.AUTONOMOUS:
                    proposals = self._generate_proposals(analysis)
                    applied = self._apply_safe(proposals)
                    if applied:
                        self._create_pr(applied)
                    self._report_findings(analysis, trends, proactive)

                if self._cycle_count % 5 == 0:
                    self._self_assess()

            except Exception as exc:
                logger.error("Cycle %d error: %s", self._cycle_count, exc)

            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self._running = False

    def run_once(self) -> dict[str, Any]:
        """Execute a single improvement cycle (synchronous)."""
        self._cycle_count += 1
        analysis = self._analyze()
        trends = self._check_trends()
        proactive = self._check_proactive()

        result: dict[str, Any] = {
            "cycle": self._cycle_count,
            "mode": self.mode.value,
            "analysis_summary": "",
            "proposals": [],
            "applied": [],
            "trends": trends,
            "proactive": proactive,
        }

        if self.mode == AutonomyMode.WATCH:
            result["analysis_summary"] = self._summary(analysis)

        elif self.mode == AutonomyMode.SUGGEST:
            proposals = self._generate_proposals(analysis)
            result["proposals"] = proposals
            result["analysis_summary"] = self._summary(analysis)

        elif self.mode == AutonomyMode.AUTONOMOUS:
            proposals = self._generate_proposals(analysis)
            applied = self._apply_safe(proposals)
            result["proposals"] = proposals
            result["applied"] = applied
            result["analysis_summary"] = self._summary(analysis)

        return result

    # ---- internal helpers ---------------------------------------------------

    def _has_changes_since_last_check(self) -> bool:
        head = self._git_head()
        if head is None:
            return True
        if self._last_head is None:
            self._last_head = head
            return True
        changed = head != self._last_head
        self._last_head = head
        return changed

    def _git_head(self) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True,
                cwd=str(self.project_dir), timeout=5,
            )
            return proc.stdout.strip() if proc.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _analyze(self) -> Any:
        from redsl.analyzers import CodeAnalyzer
        return CodeAnalyzer().analyze_project(self.project_dir)

    def _check_trends(self) -> dict:
        try:
            from redsl.awareness import AwarenessManager
            mgr = AwarenessManager()
            snapshot = mgr.build_snapshot(self.project_dir, depth=10)
            return {k: v.to_dict() for k, v in snapshot.trends.items()}
        except Exception:
            return {}

    def _check_proactive(self) -> list[dict]:
        try:
            from redsl.awareness import AwarenessManager
            mgr = AwarenessManager()
            snapshot = mgr.build_snapshot(self.project_dir, depth=10)
            return [a.to_dict() for a in snapshot.alerts[:5]]
        except Exception:
            return []

    def _generate_proposals(self, analysis: Any) -> list[dict]:
        from redsl.config import AgentConfig
        from redsl.orchestrator import RefactorOrchestrator

        config = AgentConfig.from_env()
        config.refactor.dry_run = True
        orch = RefactorOrchestrator(config)

        contexts = analysis.to_dsl_contexts()
        decisions = orch.dsl_engine.evaluate(contexts)
        decisions = sorted(decisions, key=lambda d: d.score, reverse=True)

        return [
            {
                "action": d.action.value,
                "target": d.target_file,
                "function": d.target_function,
                "score": round(d.score, 2),
                "rationale": d.rationale,
            }
            for d in decisions[: self.max_actions]
        ]

    def _save_proposals(self, proposals: list[dict]) -> None:
        import json
        out = self.project_dir / "logs" / "redsl_proposals.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(proposals, indent=2, default=str))
        logger.info("Saved %d proposals to %s", len(proposals), out)

    def _apply_safe(self, proposals: list[dict]) -> list[dict]:
        from redsl.config import AgentConfig
        from redsl.orchestrator import RefactorOrchestrator

        config = AgentConfig.from_env()
        config.refactor.dry_run = False
        orch = RefactorOrchestrator(config)

        applied: list[dict] = []
        report = orch.run_cycle(
            self.project_dir,
            max_actions=self.max_actions,
        )
        if report.proposals_applied > 0:
            for p in proposals[: report.proposals_applied]:
                applied.append(p)
        return applied

    def _create_pr(self, applied: list[dict]) -> None:
        branch = f"redsl/auto-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch],
                capture_output=True, text=True,
                cwd=str(self.project_dir), timeout=10,
            )
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True, text=True,
                cwd=str(self.project_dir), timeout=10,
            )
            msg = f"redsl: auto-refactor ({len(applied)} changes)"
            subprocess.run(
                ["git", "commit", "-m", msg],
                capture_output=True, text=True,
                cwd=str(self.project_dir), timeout=30,
            )
            logger.info("Created branch %s with %d changes", branch, len(applied))
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.warning("PR creation failed: %s", exc)

    def _report_findings(self, analysis: Any, trends: dict, proactive: list) -> None:
        logger.info(
            "Cycle %d [%s]: %s | trends=%d | alerts=%d",
            self._cycle_count, self.mode.value,
            self._summary(analysis),
            len(trends), len(proactive),
        )

    def _summary(self, analysis: Any) -> str:
        return (
            f"files={analysis.total_files} lines={analysis.total_lines} "
            f"cc={analysis.avg_cc:.1f} critical={analysis.critical_count}"
        )

    def _self_assess(self) -> None:
        try:
            from redsl.awareness import AwarenessManager
            mgr = AwarenessManager()
            report = mgr.self_assess()
            logger.info("Self-assessment cycle %d: %s", self._cycle_count, report)
        except Exception:
            pass

"""CQRS Projections - Read Models built from Event Stream."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from redsl.api.cqrs.events import (
    event_store,
    DomainEvent,
    ScanStarted,
    ScanProgress,
    ScanCompleted,
    ScanFailed,
    RefactorStarted,
    RefactorProgress,
    RefactorCompleted,
)

logger = logging.getLogger(__name__)


class Projection(ABC):
    """Base class for read model projections."""
    
    def __init__(self, aggregate_id: str) -> None:
        self.aggregate_id = aggregate_id
        self.version = 0
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def apply(self, event_data: dict[str, Any]) -> None:
        """Apply event to projection."""
        ...
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize projection to dictionary."""
        ...
    
    async def update_version(self) -> None:
        """Increment version."""
        async with self._lock:
            self.version += 1


@dataclass
class ScanProjection(Projection):
    """Projection for scan results."""
    
    aggregate_id: str = ""
    repo_url: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed
    progress_percent: int = 0
    phase: str = ""
    
    # Results
    total_files: int = 0
    total_lines: int = 0
    avg_cc: float = 0.0
    critical_count: int = 0
    alerts: list[dict] = field(default_factory=list)
    top_issues: list[dict] = field(default_factory=list)
    summary: str = ""
    
    # Error info
    error_message: str = ""
    error_type: str = ""
    
    def __post_init__(self) -> None:
        super().__init__(self.aggregate_id)
    
    async def apply(self, event_data: dict[str, Any]) -> None:
        """Apply scan-related events."""
        event_type = event_data.get("event_type")
        payload = event_data.get("payload", {})
        
        if event_type == "ScanStarted":
            self.status = "in_progress"
            self.repo_url = payload.get("repo_url", "")
            self.phase = "clone"
            self.progress_percent = 5
            
        elif event_type == "ScanProgress":
            self.phase = payload.get("phase", "")
            self.progress_percent = payload.get("progress_percent", 0)
            
        elif event_type == "ScanCompleted":
            self.status = "completed"
            self.progress_percent = 100
            self.phase = "complete"
            self.total_files = payload.get("total_files", 0)
            self.total_lines = payload.get("total_lines", 0)
            self.avg_cc = payload.get("avg_cc", 0.0)
            self.critical_count = payload.get("critical_count", 0)
            self.alerts = payload.get("alerts", [])
            self.top_issues = payload.get("top_issues", [])
            self.summary = payload.get("summary", "")
            
        elif event_type == "ScanFailed":
            self.status = "failed"
            self.error_message = payload.get("error_message", "")
            self.error_type = payload.get("error_type", "")
        
        await self.update_version()
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "repo_url": self.repo_url,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "phase": self.phase,
            "version": self.version,
            "results": {
                "total_files": self.total_files,
                "total_lines": self.total_lines,
                "avg_cc": self.avg_cc,
                "critical_count": self.critical_count,
                "alerts": self.alerts,
                "top_issues": self.top_issues,
                "summary": self.summary,
            },
            "error": {
                "message": self.error_message,
                "type": self.error_type,
            } if self.error_message else None,
        }


@dataclass
class ProjectHealthProjection(Projection):
    """Projection for project health over time."""
    
    aggregate_id: str = ""
    project_dir: str = ""
    
    # Health metrics history
    scans: list[dict] = field(default_factory=list)
    refactors: list[dict] = field(default_factory=list)
    
    # Current state
    current_avg_cc: float = 0.0
    current_critical_count: int = 0
    total_files: int = 0
    
    # Trends
    cc_trend: str = "stable"  # improving, stable, worsening
    critical_trend: str = "stable"
    
    def __post_init__(self) -> None:
        super().__init__(self.aggregate_id)
    
    async def apply(self, event_data: dict[str, Any]) -> None:
        """Apply health-related events."""
        event_type = event_data.get("event_type")
        payload = event_data.get("payload", {})
        
        if event_type == "ScanCompleted":
            scan_data = {
                "occurred_at": event_data.get("occurred_at"),
                "avg_cc": payload.get("avg_cc", 0.0),
                "critical_count": payload.get("critical_count", 0),
                "total_files": payload.get("total_files", 0),
                "total_lines": payload.get("total_lines", 0),
            }
            self.scans.append(scan_data)
            
            # Update current state
            self.current_avg_cc = scan_data["avg_cc"]
            self.current_critical_count = scan_data["critical_count"]
            self.total_files = scan_data["total_files"]
            
            # Calculate trends (simplified)
            if len(self.scans) >= 2:
                prev = self.scans[-2]
                curr = self.scans[-1]
                
                if curr["avg_cc"] < prev["avg_cc"]:
                    self.cc_trend = "improving"
                elif curr["avg_cc"] > prev["avg_cc"]:
                    self.cc_trend = "worsening"
                else:
                    self.cc_trend = "stable"
                
                if curr["critical_count"] < prev["critical_count"]:
                    self.critical_trend = "improving"
                elif curr["critical_count"] > prev["critical_count"]:
                    self.critical_trend = "worsening"
                else:
                    self.critical_trend = "stable"
        
        elif event_type == "RefactorCompleted":
            refactor_data = {
                "occurred_at": event_data.get("occurred_at"),
                "proposals_applied": payload.get("proposals_applied", 0),
                "proposals_rejected": payload.get("proposals_rejected", 0),
                "files_modified": payload.get("files_modified", []),
            }
            self.refactors.append(refactor_data)
        
        await self.update_version()
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "project_dir": self.project_dir,
            "current": {
                "avg_cc": self.current_avg_cc,
                "critical_count": self.current_critical_count,
                "total_files": self.total_files,
            },
            "trends": {
                "cc_trend": self.cc_trend,
                "critical_trend": self.critical_trend,
            },
            "history": {
                "scan_count": len(self.scans),
                "refactor_count": len(self.refactors),
                "recent_scans": self.scans[-5:] if self.scans else [],
                "recent_refactors": self.refactors[-5:] if self.refactors else [],
            },
            "version": self.version,
        }


class ProjectionManager:
    """Manages projections and rebuilds them from events."""
    
    def __init__(self) -> None:
        self._projections: dict[str, Projection] = {}
        self._subscribed = False
    
    def _get_key(self, projection_type: str, aggregate_id: str) -> str:
        """Generate key for projection."""
        return f"{projection_type}:{aggregate_id}"
    
    def get(self, projection_type: str, aggregate_id: str) -> Projection | None:
        """Get projection by type and aggregate ID."""
        key = self._get_key(projection_type, aggregate_id)
        return self._projections.get(key)
    
    def set(self, projection_type: str, aggregate_id: str, projection: Projection) -> None:
        """Store projection."""
        key = self._get_key(projection_type, aggregate_id)
        self._projections[key] = projection
    
    async def _on_event(self, event: DomainEvent) -> None:
        """Handle new events and update projections."""
        event_dict = event.to_dict()
        event_type = event_dict.get("event_type")
        aggregate_id = event_dict.get("aggregate_id")
        
        if not aggregate_id:
            return
        
        # Update ScanProjection
        if event_type in ("ScanStarted", "ScanProgress", "ScanCompleted", "ScanFailed"):
            key = self._get_key("scan", aggregate_id)
            if key not in self._projections:
                self._projections[key] = ScanProjection(aggregate_id=aggregate_id)
            await self._projections[key].apply(event_dict)
        
        # Update ProjectHealthProjection
        if event_type in ("ScanCompleted", "RefactorCompleted"):
            # Extract project dir from aggregate_id
            if aggregate_id.startswith("scan:"):
                project_key = aggregate_id.replace("scan:", "project:")
            elif aggregate_id.startswith("refactor:"):
                project_key = aggregate_id.replace("refactor:", "project:")
            else:
                project_key = aggregate_id
            
            key = self._get_key("health", project_key)
            if key not in self._projections:
                self._projections[key] = ProjectHealthProjection(
                    aggregate_id=project_key,
                    project_dir=project_key.replace("project:", ""),
                )
            await self._projections[key].apply(event_dict)
    
    def subscribe_to_events(self) -> None:
        """Subscribe to event store updates."""
        if not self._subscribed:
            event_store.subscribe("ScanStarted", self._on_event)
            event_store.subscribe("ScanProgress", self._on_event)
            event_store.subscribe("ScanCompleted", self._on_event)
            event_store.subscribe("ScanFailed", self._on_event)
            event_store.subscribe("RefactorCompleted", self._on_event)
            self._subscribed = True
            logger.debug("ProjectionManager subscribed to events")
    
    async def rebuild(self, aggregate_id: str) -> None:
        """Rebuild projection from event history."""
        # Clear existing projection
        for key in list(self._projections.keys()):
            if key.endswith(f":{aggregate_id}") or key == aggregate_id:
                del self._projections[key]
        
        # Replay events
        await event_store.replay(aggregate_id, self._on_event)


# Global projection manager
projection_manager = ProjectionManager()
projection_manager.subscribe_to_events()

"""Event Sourcing - Domain Events and Event Store."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Protocol

logger = logging.getLogger(__name__)


class DomainEvent(ABC):
    """Base class for domain events."""
    
    def __init__(
        self,
        event_id: str | None = None,
        aggregate_id: str | None = None,
        occurred_at: datetime | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        self.event_id = event_id or str(uuid.uuid4())
        self.aggregate_id = aggregate_id or ""
        self.occurred_at = occurred_at or datetime.now(timezone.utc)
        self.metadata = metadata or {}
        self.event_type = self.__class__.__name__
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": self.metadata,
            "payload": self._get_payload(),
        }
    
    @abstractmethod
    def _get_payload(self) -> dict[str, Any]:
        """Get event-specific payload."""
        ...


@dataclass
class ScanStarted(DomainEvent):
    """Event emitted when remote scan starts."""
    repo_url: str = ""
    branch: str = "main"
    depth: int = 1
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "repo_url": self.repo_url,
            "branch": self.branch,
            "depth": self.depth,
        }


@dataclass
class ScanProgress(DomainEvent):
    """Event emitted during scan progress."""
    repo_url: str = ""
    phase: str = ""  # 'clone', 'analyze', 'complete'
    progress_percent: int = 0
    message: str = ""
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "repo_url": self.repo_url,
            "phase": self.phase,
            "progress_percent": self.progress_percent,
            "message": self.message,
        }


@dataclass
class ScanCompleted(DomainEvent):
    """Event emitted when scan completes successfully."""
    repo_url: str = ""
    total_files: int = 0
    total_lines: int = 0
    avg_cc: float = 0.0
    critical_count: int = 0
    alerts: list[dict] = field(default_factory=list)
    top_issues: list[dict] = field(default_factory=list)
    summary: str = ""
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "repo_url": self.repo_url,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "avg_cc": self.avg_cc,
            "critical_count": self.critical_count,
            "alerts": self.alerts,
            "top_issues": self.top_issues,
            "summary": self.summary,
        }


@dataclass
class ScanFailed(DomainEvent):
    """Event emitted when scan fails."""
    repo_url: str = ""
    error_message: str = ""
    error_type: str = ""  # 'clone_error', 'analysis_error', 'timeout'
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "repo_url": self.repo_url,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }


@dataclass
class RefactorStarted(DomainEvent):
    """Event emitted when refactoring starts."""
    project_dir: str = ""
    dry_run: bool = True
    max_actions: int = 5
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "dry_run": self.dry_run,
            "max_actions": self.max_actions,
        }


@dataclass
class RefactorProgress(DomainEvent):
    """Event emitted during refactoring."""
    project_dir: str = ""
    phase: str = ""  # 'perceive', 'decide', 'plan', 'execute', 'reflect'
    current_action: int = 0
    total_actions: int = 0
    message: str = ""
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "phase": self.phase,
            "current_action": self.current_action,
            "total_actions": self.total_actions,
            "message": self.message,
        }


@dataclass
class RefactorCompleted(DomainEvent):
    """Event emitted when refactoring completes."""
    project_dir: str = ""
    cycle_number: int = 0
    decisions_count: int = 0
    proposals_applied: int = 0
    proposals_rejected: int = 0
    files_modified: list[str] = field(default_factory=list)
    
    def _get_payload(self) -> dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "cycle_number": self.cycle_number,
            "decisions_count": self.decisions_count,
            "proposals_applied": self.proposals_applied,
            "proposals_rejected": self.proposals_rejected,
            "files_modified": self.files_modified,
        }


# Event handler type
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventStore:
    """Append-only event store with file-based persistence.
    
    Implements Event Sourcing pattern:
    - All events are immutable and append-only
    - Events are the source of truth
    - Projections are built from event stream
    """
    
    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or Path.home() / ".redsl" / "event_store"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.storage_dir / "events.jsonl"
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._lock = asyncio.Lock()
    
    def _get_stream_path(self, aggregate_id: str) -> Path:
        """Get path to event stream for specific aggregate."""
        return self.storage_dir / f"{aggregate_id}.jsonl"
    
    async def append(self, event: DomainEvent) -> None:
        """Append event to store and notify subscribers."""
        async with self._lock:
            # Write to global event stream
            with self.events_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            
            # Write to aggregate-specific stream
            if event.aggregate_id:
                stream_path = self._get_stream_path(event.aggregate_id)
                with stream_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        
        logger.debug(f"Event appended: {event.event_type} [{event.event_id}]")
        
        # Notify subscribers
        await self._notify(event)
    
    async def _notify(self, event: DomainEvent) -> None:
        """Notify all subscribers of new event."""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.event_type}: {e}")
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe handler from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
    
    async def get_events(
        self,
        aggregate_id: str | None = None,
        event_types: list[str] | None = None,
        since: datetime | None = None,
        limit: int = 1000
    ) -> list[DomainEvent]:
        """Query events from store."""
        events: list[DomainEvent] = []
        
        source = self._get_stream_path(aggregate_id) if aggregate_id else self.events_file
        if not source.exists():
            return events
        
        with source.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    
                    # Filter by event type
                    if event_types and data.get("event_type") not in event_types:
                        continue
                    
                    # Filter by time
                    if since:
                        event_time = datetime.fromisoformat(data.get("occurred_at", ""))
                        if event_time < since:
                            continue
                    
                    # Reconstruct event (simplified - would need proper deserialization)
                    events.append(data)
                    
                    if len(events) >= limit:
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        return events
    
    async def replay(
        self,
        aggregate_id: str,
        handler: Callable[[dict], Coroutine[Any, Any, None]]
    ) -> None:
        """Replay all events for aggregate."""
        source = self._get_stream_path(aggregate_id)
        if not source.exists():
            return
        
        with source.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    await handler(data)
                except Exception as e:
                    logger.error(f"Replay error: {e}")


# Global event store instance
event_store = EventStore()

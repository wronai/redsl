"""CQRS Query Handlers - Read side operations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from redsl.api.cqrs.events import event_store, DomainEvent

logger = logging.getLogger(__name__)


# Query classes
@dataclass
class Query:
    """Base query."""
    query_id: str = ""


@dataclass
class ScanResultQuery(Query):
    """Query for scan results."""
    repo_url: str = ""


@dataclass 
class ProjectHealthQuery(Query):
    """Query for project health metrics."""
    project_dir: str = ""


@dataclass
class RecentEventsQuery(Query):
    """Query for recent events."""
    event_types: list[str] | None = None
    since: datetime | None = None
    limit: int = 100


@dataclass
class AggregateHistoryQuery(Query):
    """Query for aggregate event history."""
    aggregate_id: str = ""
    limit: int = 1000


class QueryHandler(ABC):
    """Base query handler."""
    
    @abstractmethod
    async def handle(self, query: Query) -> dict[str, Any]:
        """Handle query, return result."""
        ...


class ScanResultHandler(QueryHandler):
    """Handler for ScanResultQuery - reads from projection."""
    
    async def handle(self, query: ScanResultQuery) -> dict[str, Any]:
        """Get scan result from projection."""
        from redsl.api.cqrs.projections import projection_manager
        
        aggregate_id = f"scan:{query.repo_url}"
        projection = projection_manager.get("scan", aggregate_id)
        
        if not projection:
            return {"status": "not_found", "message": "No scan results found"}
        
        return {
            "status": "success",
            "repo_url": query.repo_url,
            "data": projection.to_dict(),
        }


class ProjectHealthHandler(QueryHandler):
    """Handler for ProjectHealthQuery."""
    
    async def handle(self, query: ProjectHealthQuery) -> dict[str, Any]:
        """Get project health metrics."""
        from redsl.api.cqrs.projections import projection_manager
        from pathlib import Path
        
        aggregate_id = f"project:{query.project_dir}"
        projection = projection_manager.get("health", aggregate_id)
        
        if not projection:
            # Build from scratch
            return {
                "status": "no_data",
                "project_dir": query.project_dir,
                "message": "No health data available. Run analysis first.",
            }
        
        return {
            "status": "success",
            "project_dir": query.project_dir,
            "health": projection.to_dict(),
        }


class RecentEventsHandler(QueryHandler):
    """Handler for RecentEventsQuery - reads from event store."""
    
    async def handle(self, query: RecentEventsQuery) -> dict[str, Any]:
        """Get recent events from event store."""
        events = await event_store.get_events(
            event_types=query.event_types,
            since=query.since,
            limit=query.limit,
        )
        
        return {
            "status": "success",
            "count": len(events),
            "events": events,
        }


class AggregateHistoryHandler(QueryHandler):
    """Handler for AggregateHistoryQuery."""
    
    async def handle(self, query: AggregateHistoryQuery) -> dict[str, Any]:
        """Get event history for aggregate."""
        events = await event_store.get_events(
            aggregate_id=query.aggregate_id,
            limit=query.limit,
        )
        
        return {
            "status": "success",
            "aggregate_id": query.aggregate_id,
            "event_count": len(events),
            "events": events,
        }


class QueryBus:
    """Query Bus - dispatches queries to handlers."""
    
    def __init__(self) -> None:
        self._handlers: dict[type, QueryHandler] = {}
    
    def register(self, query_type: type, handler: QueryHandler) -> None:
        """Register handler for query type."""
        self._handlers[query_type] = handler
        logger.debug(f"Registered query handler for {query_type.__name__}")
    
    async def dispatch(self, query: Query) -> dict[str, Any]:
        """Dispatch query to appropriate handler."""
        handler = self._handlers.get(type(query))
        if not handler:
            raise ValueError(f"No handler registered for {type(query).__name__}")
        
        logger.debug(f"Dispatching query {type(query).__name__}")
        return await handler.handle(query)


# Global query bus
query_bus = QueryBus()

# Register handlers
query_bus.register(ScanResultQuery, ScanResultHandler())
query_bus.register(ProjectHealthQuery, ProjectHealthHandler())
query_bus.register(RecentEventsQuery, RecentEventsHandler())
query_bus.register(AggregateHistoryQuery, AggregateHistoryHandler())

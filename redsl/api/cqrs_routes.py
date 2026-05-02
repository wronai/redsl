"""CQRS/ES API Routes - REST commands/queries + WebSocket events."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from redsl.api.cqrs import (
    # Commands
    command_bus,
    ScanRemoteCommand,
    RefactorCommand,
    # Queries
    query_bus,
    ScanResultQuery,
    ProjectHealthQuery,
    RecentEventsQuery,
    AggregateHistoryQuery,
    # WebSocket
    ws_manager,
    # Projections
    projection_manager,
)

logger = logging.getLogger(__name__)


# Request/Response models
class ScanRemoteRequest(BaseModel):
    """Request to scan remote repository."""
    repo_url: str = Field(description="Git repository URL")
    branch: str = Field("main", description="Branch to checkout")
    depth: int = Field(1, description="Clone depth")
    async_mode: bool = Field(False, description="Return immediately, check status via query")


class ScanRemoteResponse(BaseModel):
    """Response from scan operation."""
    status: str
    aggregate_id: str | None = None
    correlation_id: str | None = None
    message: str | None = None
    data: dict[str, Any] | None = None


class RefactorRequest(BaseModel):
    """Request to run refactoring."""
    project_dir: str = Field(description="Path to project directory")
    dry_run: bool = Field(True, description="Plan-only mode")
    max_actions: int = Field(5, description="Maximum actions to execute")
    llm_model: str | None = Field(None, description="LLM model to use")
    async_mode: bool = Field(False, description="Return immediately, check status via query")


class QueryResponse(BaseModel):
    """Generic query response."""
    status: str
    data: dict[str, Any] | None = None
    message: str | None = None


class EventStreamRequest(BaseModel):
    """Request for event stream subscription."""
    aggregate_id: str | None = None
    event_types: list[str] | None = None


def _register_cqrs_routes(app: Any) -> None:
    """Register CQRS/ES endpoints."""
    
    # ─────────────────────────────────────────────────────────────────
    # COMMAND ENDPOINTS (Write side)
    # ─────────────────────────────────────────────────────────────────
    
    @app.post("/cqrs/scan/remote", response_model=ScanRemoteResponse)
    async def cqrs_scan_remote(req: ScanRemoteRequest) -> dict[str, Any]:
        """Start remote repository scan - CQRS Command.
        
        Emits events:
        - ScanStarted
        - ScanProgress (multiple)
        - ScanCompleted or ScanFailed
        
        Use /cqrs/query/scan/status to check async results.
        """
        import uuid
        
        correlation_id = str(uuid.uuid4())
        aggregate_id = f"scan:{req.repo_url}"
        
        command = ScanRemoteCommand(
            command_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            repo_url=req.repo_url,
            branch=req.branch,
            depth=req.depth,
            notify_ws=True,  # Always notify via WebSocket
        )
        
        if req.async_mode:
            # In async mode, command runs in background
            # Client checks status via query endpoint
            import asyncio
            asyncio.create_task(command_bus.dispatch(command))
            
            return {
                "status": "accepted",
                "aggregate_id": aggregate_id,
                "correlation_id": correlation_id,
                "message": "Scan started. Check status via /cqrs/query/scan/status",
            }
        
        # Synchronous execution
        result = await command_bus.dispatch(command)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("detail", "Scan failed"))
        
        return {
            "status": "success",
            "aggregate_id": aggregate_id,
            "correlation_id": correlation_id,
            "data": result,
        }
    
    @app.post("/cqrs/refactor", response_model=ScanRemoteResponse)
    async def cqrs_refactor(req: RefactorRequest) -> dict[str, Any]:
        """Start refactoring cycle - CQRS Command.
        
        Emits events:
        - RefactorStarted
        - RefactorProgress (multiple)
        - RefactorCompleted or RefactorFailed
        """
        import uuid
        
        correlation_id = str(uuid.uuid4())
        aggregate_id = f"refactor:{req.project_dir}"
        
        command = RefactorCommand(
            command_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            project_dir=req.project_dir,
            dry_run=req.dry_run,
            max_actions=req.max_actions,
            llm_model=req.llm_model,
            notify_ws=True,
        )
        
        if req.async_mode:
            import asyncio
            asyncio.create_task(command_bus.dispatch(command))
            
            return {
                "status": "accepted",
                "aggregate_id": aggregate_id,
                "correlation_id": correlation_id,
                "message": "Refactoring started. Check status via /cqrs/query/refactor/status",
            }
        
        result = await command_bus.dispatch(command)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("detail", "Refactor failed"))
        
        return {
            "status": "success",
            "aggregate_id": aggregate_id,
            "correlation_id": correlation_id,
            "data": result,
        }
    
    # ─────────────────────────────────────────────────────────────────
    # QUERY ENDPOINTS (Read side)
    # ─────────────────────────────────────────────────────────────────
    
    @app.get("/cqrs/query/scan/status")
    async def query_scan_status(repo_url: str) -> dict[str, Any]:
        """Query scan status and results from projection.
        
        Returns current state including:
        - status: pending|in_progress|completed|failed
        - progress_percent: 0-100
        - phase: clone|analyze|complete
        - results: if completed
        - error: if failed
        """
        query = ScanResultQuery(repo_url=repo_url)
        result = await query_bus.dispatch(query)
        
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="No scan found for this repository")
        
        return result
    
    @app.get("/cqrs/query/project/health")
    async def query_project_health(project_dir: str) -> dict[str, Any]:
        """Query project health metrics and trends."""
        query = ProjectHealthQuery(project_dir=project_dir)
        result = await query_bus.dispatch(query)
        return result
    
    @app.get("/cqrs/query/events/recent")
    async def query_recent_events(
        event_types: str | None = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Query recent events from event store.
        
        Args:
            event_types: Comma-separated list of event types (e.g., "ScanStarted,ScanCompleted")
            limit: Maximum number of events to return
        """
        types_list = event_types.split(",") if event_types else None
        
        query = RecentEventsQuery(
            event_types=types_list,
            limit=limit,
        )
        result = await query_bus.dispatch(query)
        return result
    
    @app.get("/cqrs/query/aggregate/history")
    async def query_aggregate_history(
        aggregate_id: str,
        limit: int = 1000
    ) -> dict[str, Any]:
        """Query event history for specific aggregate."""
        query = AggregateHistoryQuery(
            aggregate_id=aggregate_id,
            limit=limit,
        )
        result = await query_bus.dispatch(query)
        return result
    
    @app.get("/cqrs/query/projections/list")
    async def list_projections() -> dict[str, Any]:
        """List all active projections and their versions."""
        stats = {
            "projection_count": len(projection_manager._projections),
            "projections": [
                {
                    "key": key,
                    "type": type(proj).__name__,
                    "aggregate_id": getattr(proj, "aggregate_id", None),
                    "version": getattr(proj, "version", 0),
                }
                for key, proj in projection_manager._projections.items()
            ],
        }
        return {"status": "success", "data": stats}
    
    # ─────────────────────────────────────────────────────────────────
    # WEBSOCKET ENDPOINT (Real-time events)
    # ─────────────────────────────────────────────────────────────────
    
    @app.websocket("/ws/cqrs/events")
    async def ws_cqrs_events(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time CQRS events.
        
        Protocol:
        1. Client connects and receives connection.established
        2. Client can subscribe to aggregates via:
           {"type": "subscribe", "aggregate_id": "scan:https://github.com/..."}
        3. Server pushes events:
           {"type": "event", "data": {...event payload...}}
        4. Client can ping:
           {"type": "ping", "timestamp": 1234567890}
           Server responds with pong
        
        Events are automatically broadcast for:
        - ScanStarted, ScanProgress, ScanCompleted, ScanFailed
        - RefactorStarted, RefactorProgress, RefactorCompleted
        """
        await ws_manager.handle_client(websocket)
    
    @app.get("/ws/stats")
    async def ws_stats() -> dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {"status": "success", "data": ws_manager.get_stats()}
    
    @app.post("/ws/health-check")
    async def ws_health_check() -> dict[str, Any]:
        """Run health check on WebSocket connections."""
        result = await ws_manager.health_check()
        return {"status": "success", "data": result}
    
    # ─────────────────────────────────────────────────────────────────
    # EVENT STREAM ENDPOINT (SSE alternative)
    # ─────────────────────────────────────────────────────────────────
    
    @app.get("/cqrs/events/stream")
    async def events_stream(
        aggregate_id: str | None = None,
        since: str | None = None,
        limit: int = 100
    ) -> Any:
        """Server-Sent Events endpoint for event streaming.
        
        Returns text/event-stream with JSON-encoded events.
        Alternative to WebSocket for simpler clients.
        """
        from datetime import datetime
        from fastapi.responses import StreamingResponse
        import json
        import asyncio
        
        since_dt = datetime.fromisoformat(since) if since else None
        
        async def event_generator():
            """Generate SSE events."""
            events = await event_store.get_events(
                aggregate_id=aggregate_id,
                since=since_dt,
                limit=limit,
            )
            
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
            
            # Keep connection alive with heartbeat
            while True:
                yield ":heartbeat\n\n"
                await asyncio.sleep(30)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    
    # ─────────────────────────────────────────────────────────────────
    # PROJECTION ADMIN
    # ─────────────────────────────────────────────────────────────────
    
    @app.post("/cqrs/projections/rebuild")
    async def rebuild_projection(aggregate_id: str) -> dict[str, Any]:
        """Rebuild projection from event history.
        
        Useful for:
        - Recovering from corruption
        - Schema migrations
        - Debugging
        """
        await projection_manager.rebuild(aggregate_id)
        
        return {
            "status": "success",
            "message": f"Projection {aggregate_id} rebuilt",
        }
    
    logger.info("CQRS/ES routes registered")

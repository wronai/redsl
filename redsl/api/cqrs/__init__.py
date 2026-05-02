"""CQRS/ES Architecture for ReDSL API.

Command Query Responsibility Segregation with Event Sourcing:
- Commands: Write operations that generate events
- Queries: Read operations from projections
- Event Store: Append-only log of all domain events
- Projections: Read models built from event stream
- WebSocket: Real-time event streaming
"""

from redsl.api.cqrs.commands import (
    Command,
    CommandHandler,
    ScanRemoteCommand,
    RefactorCommand,
    command_bus,
)
from redsl.api.cqrs.events import (
    DomainEvent,
    EventStore,
    ScanStarted,
    ScanCompleted,
    ScanFailed,
    RefactorStarted,
    RefactorCompleted,
    event_store,
)
from redsl.api.cqrs.queries import (
    Query,
    QueryHandler,
    ScanResultQuery,
    ProjectHealthQuery,
    RecentEventsQuery,
    AggregateHistoryQuery,
    query_bus,
)
from redsl.api.cqrs.projections import (
    Projection,
    ScanProjection,
    ProjectHealthProjection,
    projection_manager,
)
from redsl.api.cqrs.websocket_manager import (
    WebSocketManager,
    ws_manager,
)

__all__ = [
    # Commands
    "Command",
    "CommandHandler", 
    "ScanRemoteCommand",
    "RefactorCommand",
    "command_bus",
    # Events
    "DomainEvent",
    "EventStore",
    "ScanStarted",
    "ScanCompleted",
    "ScanFailed",
    "RefactorStarted",
    "RefactorCompleted",
    "event_store",
    # Queries
    "Query",
    "QueryHandler",
    "ScanResultQuery",
    "ProjectHealthQuery",
    "RecentEventsQuery",
    "AggregateHistoryQuery",
    "query_bus",
    # Projections
    "Projection",
    "ScanProjection",
    "ProjectHealthProjection",
    "projection_manager",
    # WebSocket
    "WebSocketManager",
    "ws_manager",
]

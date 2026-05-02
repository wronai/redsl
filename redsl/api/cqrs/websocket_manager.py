"""WebSocket Manager for real-time CQRS/ES event streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time event streaming.
    
    Features:
    - Connection pooling
    - Event broadcasting
    - Subscription-based filtering
    - Heartbeat/ping-pong
    """
    
    def __init__(self) -> None:
        # Active connections
        self._connections: dict[str, WebSocket] = {}
        # Subscriptions: aggregate_id -> list of connection_ids
        self._subscriptions: dict[str, set[str]] = {}
        # Connection metadata
        self._metadata: dict[str, dict[str, Any]] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str | None = None,
        subscriptions: list[str] | None = None
    ) -> str:
        """Accept and register new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket object
            connection_id: Optional custom ID, auto-generated if not provided
            subscriptions: List of aggregate IDs to subscribe to
            
        Returns:
            connection_id: The ID assigned to this connection
        """
        await websocket.accept()
        
        conn_id = connection_id or f"ws_{id(websocket)}_{asyncio.get_event_loop().time()}"
        
        async with self._lock:
            self._connections[conn_id] = websocket
            self._metadata[conn_id] = {
                "connected_at": asyncio.get_event_loop().time(),
                "subscriptions": set(subscriptions or []),
                "message_count": 0,
            }
            
            # Register subscriptions
            for aggregate_id in subscriptions or []:
                if aggregate_id not in self._subscriptions:
                    self._subscriptions[aggregate_id] = set()
                self._subscriptions[aggregate_id].add(conn_id)
        
        logger.info(f"WebSocket connected: {conn_id}")
        
        # Send welcome message
        await self.send_to(conn_id, {
            "type": "connection.established",
            "connection_id": conn_id,
            "subscriptions": subscriptions or [],
        })
        
        return conn_id
    
    async def disconnect(self, connection_id: str) -> None:
        """Remove and cleanup WebSocket connection."""
        async with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
            
            if connection_id in self._metadata:
                meta = self._metadata.pop(connection_id, {})
                # Remove from all subscriptions
                for aggregate_id in meta.get("subscriptions", set()):
                    if aggregate_id in self._subscriptions:
                        self._subscriptions[aggregate_id].discard(connection_id)
                        if not self._subscriptions[aggregate_id]:
                            del self._subscriptions[aggregate_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe(self, connection_id: str, aggregate_id: str) -> bool:
        """Subscribe connection to aggregate events.
        
        Returns:
            True if successful, False if connection not found
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            # Add to connection metadata
            self._metadata[connection_id]["subscriptions"].add(aggregate_id)
            
            # Add to subscription index
            if aggregate_id not in self._subscriptions:
                self._subscriptions[aggregate_id] = set()
            self._subscriptions[aggregate_id].add(connection_id)
        
        logger.debug(f"{connection_id} subscribed to {aggregate_id}")
        
        await self.send_to(connection_id, {
            "type": "subscription.confirmed",
            "aggregate_id": aggregate_id,
        })
        
        return True
    
    async def unsubscribe(self, connection_id: str, aggregate_id: str) -> bool:
        """Unsubscribe connection from aggregate events."""
        async with self._lock:
            if connection_id in self._metadata:
                self._metadata[connection_id]["subscriptions"].discard(aggregate_id)
            
            if aggregate_id in self._subscriptions:
                self._subscriptions[aggregate_id].discard(connection_id)
                if not self._subscriptions[aggregate_id]:
                    del self._subscriptions[aggregate_id]
        
        logger.debug(f"{connection_id} unsubscribed from {aggregate_id}")
        return True
    
    async def send_to(self, connection_id: str, message: dict[str, Any]) -> bool:
        """Send message to specific connection.
        
        Returns:
            True if sent successfully, False if connection not found or error
        """
        websocket = self._connections.get(connection_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_json(message)
            
            async with self._lock:
                if connection_id in self._metadata:
                    self._metadata[connection_id]["message_count"] += 1
            
            return True
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            return False
    
    async def broadcast_event(self, event_data: dict[str, Any]) -> int:
        """Broadcast event to all subscribed connections.
        
        Args:
            event_data: Event dictionary (should have 'aggregate_id' and 'event_type')
            
        Returns:
            Number of connections that received the event
        """
        aggregate_id = event_data.get("aggregate_id")
        if not aggregate_id:
            # Broadcast to all if no aggregate_id
            return await self.broadcast_all(event_data)
        
        async with self._lock:
            subscribers = self._subscriptions.get(aggregate_id, set()).copy()
        
        if not subscribers:
            return 0
        
        message = {
            "type": "event",
            "data": event_data,
        }
        
        sent_count = 0
        for conn_id in subscribers:
            if await self.send_to(conn_id, message):
                sent_count += 1
        
        logger.debug(f"Broadcasted {event_data.get('event_type')} to {sent_count}/{len(subscribers)} subscribers")
        return sent_count
    
    async def broadcast_all(self, message: dict[str, Any]) -> int:
        """Broadcast message to ALL connected clients.
        
        Returns:
            Number of connections that received the message
        """
        async with self._lock:
            connections = list(self._connections.keys())
        
        sent_count = 0
        for conn_id in connections:
            if await self.send_to(conn_id, message):
                sent_count += 1
        
        return sent_count
    
    async def handle_client(
        self,
        websocket: WebSocket,
        connection_id: str | None = None
    ) -> None:
        """Handle WebSocket client connection lifecycle.
        
        This method runs indefinitely until client disconnects.
        Processes incoming messages for subscription management.
        """
        conn_id = await self.connect(websocket, connection_id)
        
        try:
            while True:
                # Wait for client message
                data = await websocket.receive_json()
                
                # Process commands from client
                msg_type = data.get("type", "")
                
                if msg_type == "subscribe":
                    aggregate_id = data.get("aggregate_id")
                    if aggregate_id:
                        await self.subscribe(conn_id, aggregate_id)
                
                elif msg_type == "unsubscribe":
                    aggregate_id = data.get("aggregate_id")
                    if aggregate_id:
                        await self.unsubscribe(conn_id, aggregate_id)
                
                elif msg_type == "ping":
                    await self.send_to(conn_id, {"type": "pong", "timestamp": data.get("timestamp")})
                
                else:
                    logger.warning(f"Unknown message type from {conn_id}: {msg_type}")
                    
        except WebSocketDisconnect:
            logger.info(f"Client {conn_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {conn_id}: {e}")
        finally:
            await self.disconnect(conn_id)
    
    def get_stats(self) -> dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "total_connections": len(self._connections),
            "total_subscriptions": sum(len(subs) for subs in self._subscriptions.values()),
            "unique_aggregates": len(self._subscriptions),
            "connections": {
                conn_id: {
                    "subscriptions": list(meta.get("subscriptions", set())),
                    "message_count": meta.get("message_count", 0),
                    "connected_seconds": asyncio.get_event_loop().time() - meta.get("connected_at", 0),
                }
                for conn_id, meta in self._metadata.items()
            },
        }
    
    async def health_check(self) -> dict[str, Any]:
        """Perform health check on all connections."""
        disconnected = []
        
        for conn_id, websocket in list(self._connections.items()):
            try:
                await websocket.send_json({"type": "health.check"})
            except Exception:
                disconnected.append(conn_id)
        
        # Cleanup disconnected
        for conn_id in disconnected:
            await self.disconnect(conn_id)
        
        return {
            "checked": len(self._connections) + len(disconnected),
            "healthy": len(self._connections),
            "disconnected": len(disconnected),
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()

"""
WebSocket routes for real-time communication during phone recording.

Provides real-time updates for:
- Recording status (start, pause, resume, stop)
- Audio level monitoring
- Progress updates during transcription
- Error notifications
- System status monitoring
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from pydantic import BaseModel

from ..core.events import EventType, Event, subscribe, unsubscribe
from ..core.logging_setup import get_logger

logger = get_logger(__name__)

# WebSocket router
websocket_router = APIRouter()

# Active WebSocket connections management
class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""

    def __init__(self):
        # Different connection types for different purposes
        self.recording_connections: Set[WebSocket] = set()
        self.monitoring_connections: Set[WebSocket] = set()
        self.debug_connections: Set[WebSocket] = set()
        self.all_connections: Set[WebSocket] = set()

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Last known states for new connections
        self.last_recording_state = {
            "status": "idle",
            "session_id": None,
            "duration": 0,
            "audio_levels": {"mic": 0.0, "system": 0.0}
        }

        self.last_system_state = {
            "blackhole_available": False,
            "devices_count": 0,
            "cpu_usage": 0.0,
            "memory_usage": 0.0
        }

    async def connect_recording(self, websocket: WebSocket, client_id: str = None):
        """Connect a client for recording updates."""
        await websocket.accept()
        self.recording_connections.add(websocket)
        self.all_connections.add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "type": "recording",
            "client_id": client_id or f"client_{id(websocket)}",
            "connected_at": datetime.now(),
            "message_count": 0
        }

        logger.info(f"Recording client connected: {client_id}, total recording connections: {len(self.recording_connections)}")

        # Send current state to new connection
        await self.send_to_connection(websocket, {
            "type": "initial_state",
            "recording_state": self.last_recording_state,
            "timestamp": time.time()
        })

    async def connect_monitoring(self, websocket: WebSocket, client_id: str = None):
        """Connect a client for system monitoring."""
        await websocket.accept()
        self.monitoring_connections.add(websocket)
        self.all_connections.add(websocket)

        self.connection_metadata[websocket] = {
            "type": "monitoring",
            "client_id": client_id or f"monitor_{id(websocket)}",
            "connected_at": datetime.now(),
            "message_count": 0
        }

        logger.info(f"Monitoring client connected: {client_id}, total monitoring connections: {len(self.monitoring_connections)}")

        # Send current system state
        await self.send_to_connection(websocket, {
            "type": "system_state",
            "system_state": self.last_system_state,
            "timestamp": time.time()
        })

    async def connect_debug(self, websocket: WebSocket, client_id: str = None):
        """Connect a client for debug information."""
        await websocket.accept()
        self.debug_connections.add(websocket)
        self.all_connections.add(websocket)

        self.connection_metadata[websocket] = {
            "type": "debug",
            "client_id": client_id or f"debug_{id(websocket)}",
            "connected_at": datetime.now(),
            "message_count": 0
        }

        logger.info(f"Debug client connected: {client_id}, total debug connections: {len(self.debug_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a client."""
        metadata = self.connection_metadata.get(websocket, {})
        client_type = metadata.get("type", "unknown")
        client_id = metadata.get("client_id", "unknown")

        # Remove from appropriate sets
        self.recording_connections.discard(websocket)
        self.monitoring_connections.discard(websocket)
        self.debug_connections.discard(websocket)
        self.all_connections.discard(websocket)

        # Clean up metadata
        self.connection_metadata.pop(websocket, None)

        logger.info(f"{client_type.title()} client disconnected: {client_id}")

    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific connection."""
        try:
            await websocket.send_text(json.dumps(message))

            # Update message count
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["message_count"] += 1

        except Exception as e:
            logger.error(f"Error sending message to connection: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_recording(self, message: Dict[str, Any]):
        """Broadcast message to all recording clients."""
        if not self.recording_connections:
            logger.debug("No recording connections to broadcast to")
            return

        # Update last state for new connections
        if message.get("type") == "recording_update":
            self.last_recording_state.update(message.get("data", {}))

        # Send to all recording connections
        disconnected = []
        for connection in self.recording_connections:
            try:
                await self.send_to_connection(connection, message)
            except Exception as e:
                logger.error(f"Error broadcasting to recording connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)

        logger.debug(f"Broadcasted recording message to {len(self.recording_connections)} connections")

    async def broadcast_to_monitoring(self, message: Dict[str, Any]):
        """Broadcast message to all monitoring clients."""
        if not self.monitoring_connections:
            return

        # Update last system state
        if message.get("type") == "system_update":
            self.last_system_state.update(message.get("data", {}))

        disconnected = []
        for connection in self.monitoring_connections:
            try:
                await self.send_to_connection(connection, message)
            except Exception as e:
                logger.error(f"Error broadcasting to monitoring connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)

    async def broadcast_to_debug(self, message: Dict[str, Any]):
        """Broadcast message to all debug clients."""
        if not self.debug_connections:
            return

        disconnected = []
        for connection in self.debug_connections:
            try:
                await self.send_to_connection(connection, message)
            except Exception as e:
                logger.error(f"Error broadcasting to debug connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        await self.broadcast_to_recording(message)
        await self.broadcast_to_monitoring(message)
        await self.broadcast_to_debug(message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections."""
        return {
            "total_connections": len(self.all_connections),
            "recording_connections": len(self.recording_connections),
            "monitoring_connections": len(self.monitoring_connections),
            "debug_connections": len(self.debug_connections),
            "connection_details": [
                {
                    "client_id": metadata.get("client_id"),
                    "type": metadata.get("type"),
                    "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                    "message_count": metadata.get("message_count", 0)
                }
                for metadata in self.connection_metadata.values()
            ]
        }


# Global connection manager
connection_manager = ConnectionManager()


class AudioLevelData(BaseModel):
    """Real-time audio level data."""
    microphone_level: float
    system_level: float
    timestamp: float


class RecordingStatusData(BaseModel):
    """Recording status update data."""
    status: str  # idle, recording, paused, processing, completed, error
    session_id: Optional[str] = None
    duration: float = 0.0
    message: Optional[str] = None
    error: Optional[str] = None


class SystemStatusData(BaseModel):
    """System monitoring data."""
    blackhole_available: bool
    device_count: int
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None


# WebSocket endpoints
@websocket_router.websocket("/ws/recording")
async def websocket_recording_endpoint(websocket: WebSocket):
    """WebSocket endpoint for recording-related real-time updates."""
    client_id = None
    try:
        # Get client ID from query parameters if provided
        query_params = dict(websocket.query_params)
        client_id = query_params.get("client_id")

        await connection_manager.connect_recording(websocket, client_id)

        while True:
            try:
                # Wait for client messages (for keep-alive or client commands)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Parse and handle client message
                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")

                    if message_type == "ping":
                        # Respond to ping with pong
                        await connection_manager.send_to_connection(websocket, {
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message_type == "request_status":
                        # Send current status
                        await connection_manager.send_to_connection(websocket, {
                            "type": "recording_update",
                            "data": connection_manager.last_recording_state,
                            "timestamp": time.time()
                        })

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from recording client {client_id}: {message}")

            except asyncio.TimeoutError:
                # Send ping to check if connection is alive
                await connection_manager.send_to_connection(websocket, {
                    "type": "ping",
                    "timestamp": time.time()
                })

    except WebSocketDisconnect:
        logger.info(f"Recording client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in recording WebSocket {client_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@websocket_router.websocket("/ws/monitoring")
async def websocket_monitoring_endpoint(websocket: WebSocket):
    """WebSocket endpoint for system monitoring updates."""
    client_id = None
    try:
        query_params = dict(websocket.query_params)
        client_id = query_params.get("client_id")

        await connection_manager.connect_monitoring(websocket, client_id)

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")

                    if message_type == "ping":
                        await connection_manager.send_to_connection(websocket, {
                            "type": "pong",
                            "timestamp": time.time()
                        })

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from monitoring client {client_id}: {message}")

            except asyncio.TimeoutError:
                await connection_manager.send_to_connection(websocket, {
                    "type": "ping",
                    "timestamp": time.time()
                })

    except WebSocketDisconnect:
        logger.info(f"Monitoring client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in monitoring WebSocket {client_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@websocket_router.websocket("/ws/debug")
async def websocket_debug_endpoint(websocket: WebSocket):
    """WebSocket endpoint for debug information."""
    client_id = None
    try:
        query_params = dict(websocket.query_params)
        client_id = query_params.get("client_id")

        await connection_manager.connect_debug(websocket, client_id)

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)

                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")

                    if message_type == "ping":
                        await connection_manager.send_to_connection(websocket, {
                            "type": "pong",
                            "timestamp": time.time()
                        })
                    elif message_type == "get_stats":
                        stats = connection_manager.get_connection_stats()
                        await connection_manager.send_to_connection(websocket, {
                            "type": "connection_stats",
                            "data": stats,
                            "timestamp": time.time()
                        })

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from debug client {client_id}: {message}")

            except asyncio.TimeoutError:
                await connection_manager.send_to_connection(websocket, {
                    "type": "ping",
                    "timestamp": time.time()
                })

    except WebSocketDisconnect:
        logger.info(f"Debug client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in debug WebSocket {client_id}: {e}")
    finally:
        await connection_manager.disconnect(websocket)


# Helper functions for broadcasting updates
async def broadcast_recording_status(status_data: RecordingStatusData):
    """Broadcast recording status update to all recording clients."""
    message = {
        "type": "recording_update",
        "data": status_data.dict(),
        "timestamp": time.time()
    }
    await connection_manager.broadcast_to_recording(message)


async def broadcast_audio_levels(audio_data: AudioLevelData):
    """Broadcast audio level data to recording clients."""
    message = {
        "type": "audio_levels",
        "data": audio_data.dict(),
        "timestamp": time.time()
    }
    await connection_manager.broadcast_to_recording(message)


async def broadcast_system_status(system_data: SystemStatusData):
    """Broadcast system status to monitoring clients."""
    message = {
        "type": "system_update",
        "data": system_data.dict(),
        "timestamp": time.time()
    }
    await connection_manager.broadcast_to_monitoring(message)


async def broadcast_debug_message(debug_data: Dict[str, Any]):
    """Broadcast debug information to debug clients."""
    message = {
        "type": "debug_info",
        "data": debug_data,
        "timestamp": time.time()
    }
    await connection_manager.broadcast_to_debug(message)


# Event handlers for integration with existing event system
async def handle_recording_event(event: Event):
    """Handle recording events and broadcast to clients."""
    if event.event_type == EventType.PROGRESS_UPDATE:
        status_data = RecordingStatusData(
            status=event.data.get("status", "unknown"),
            session_id=event.data.get("session_id"),
            duration=event.data.get("duration", 0.0),
            message=event.data.get("message")
        )
        await broadcast_recording_status(status_data)

    elif event.event_type == EventType.ERROR:
        status_data = RecordingStatusData(
            status="error",
            error=event.data.get("error", "Unknown error"),
            message=event.data.get("message")
        )
        await broadcast_recording_status(status_data)


# Initialize event subscriptions
def setup_websocket_event_handlers():
    """Set up event handlers for WebSocket integration."""
    subscribe(EventType.PROGRESS_UPDATE, handle_recording_event)
    subscribe(EventType.TRANSCRIPTION_FAILED, handle_recording_event)
    subscribe(EventType.EXTRACTION_FAILED, handle_recording_event)
    subscribe(EventType.PHONE_PROCESSING_FAILED, handle_recording_event)
    logger.info("WebSocket event handlers initialized")


# Cleanup function
def cleanup_websocket_handlers():
    """Clean up event handlers."""
    unsubscribe(EventType.PROGRESS_UPDATE, handle_recording_event)
    unsubscribe(EventType.ERROR, handle_recording_event)
    logger.info("WebSocket event handlers cleaned up")
# app/utils/connection_manager.py
import logging
from typing import Dict, List
from fastapi import WebSocket

log = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages active WebSocket connections.
    This class is instantiated once and shared to handle all socket connections.
    """
    def __init__(self):
        # Stores active connections using session_id as the key
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accepts a new WebSocket connection and adds it to the manager."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        log.info(f"WebSocket connected: {session_id} (Total: {len(self.active_connections)})")

    def disconnect(self, session_id: str):
        """Removes a WebSocket connection from the manager."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            log.info(f"WebSocket disconnected: {session_id} (Remaining: {len(self.active_connections)})")
        else:
            log.warning(f"Attempted to disconnect non-existent session: {session_id}")

    async def send_json(self, session_id: str, data: dict):
        """Sends JSON data to a specific WebSocket connection."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(data)
                log.debug(f"Sent JSON to {session_id}: Type={data.get('type', 'N/A')}")
            except Exception as e:
                # Handle cases where client disconnected unexpectedly
                log.error(f"Error sending JSON to {session_id}: {e}")
                self.disconnect(session_id)
        else:
            log.warning(f"Attempted to send JSON to non-existent session: {session_id}")

    async def broadcast(self, message: str):
        """Sends a text message to ALL active WebSocket connections."""
        disconnected_sessions = []
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                log.error(f"Error broadcasting to {session_id}, marking for removal: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up connections that failed
        for session_id in disconnected_sessions:
            self.disconnect(session_id)

# Create a single, shared instance to be imported by other modules
manager = ConnectionManager()
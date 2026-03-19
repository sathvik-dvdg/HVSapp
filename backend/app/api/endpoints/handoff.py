# app/api/endpoints/handoff.py
import asyncio
import logging
from typing import Dict, Optional, Any

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    status
)
from sqlalchemy.orm import Session

# Import project components
from app.db.session import get_db
from app.api import deps # Contains user_service and verify_token
from app.models.user import User
from app.services import asr_service # Handles the ASR processing
from app.utils.connection_manager import manager # WebSocket connection manager
from app.schemas.session import SessionState # State object for the connection

# --- Logging Setup ---
log = logging.getLogger(__name__)

# --- Global dictionary to hold all active session states ---
active_session_states: Dict[str, SessionState] = {}

# --- WebSocket Authentication Dependency ---
async def get_current_user_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Access Token passed as query parameter"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to authenticate WebSocket connections via a query parameter token.
    Closes the connection if authentication fails.
    """
    username = deps.verify_token(token)
    if not username:
        log.warning("WebSocket authentication failed: Invalid or missing token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication Required")

    user = deps.user_service.get_user_by_username(db, username=username)
    if not user:
        log.warning(f"WebSocket authentication failed: User '{username}' not found.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")

    log.info(f"WebSocket authenticated for user: {user.username}")
    return user

# --- API Router Definition ---
router = APIRouter()

# --- WebSocket Endpoint for Dictation ---
@router.websocket("/ws/dictation/{session_id}")
async def websocket_dictation_endpoint(
    websocket: WebSocket,
    session_id: str,
    encounter_id: int = Query(..., description="The ID of the encounter for this dictation"),
    current_user: User = Depends(get_current_user_ws) # Use the WS-specific auth
):
    """
    WebSocket endpoint for real-time clinical dictation.
    URL Example: ws://host:port/ws/dictation/some_session_id?encounter_id=123&token=YOUR_JWT_TOKEN
    """
    state: Optional[SessionState] = None # Initialize for reliable cleanup
    try:
        # 1. Accept Connection & Initialize Session State
        await manager.connect(session_id, websocket)
        state = SessionState(session_id)
        state.encounter_id = encounter_id
        state.author_id = current_user.id

    except WebSocketDisconnect as e:
        log.warning(f"WebSocket client {session_id} disconnected: Code {e.code}, Reason: {e.reason}")
    except Exception as e:
        log.error(f"Unhandled error in dictation session {session_id}: {e}", exc_info=True)
        try:
            if websocket.client_state == status.WS_STATE_CONNECTED:
                 await manager.send_json(session_id, {"status": "fatal_error", "message": f"Server error: {type(e).__name__}"})
        except Exception:
            pass # Ignore errors during error reporting

    finally:
        # --- Final Cleanup Logic ---
        log.info(f"Cleaning up dictation WS session {session_id}.")
        if state:
            state.is_active = False # Signal tasks to stop
            if state.audio_queue:
                try:
                    state.audio_queue.put_nowait(None) # Ensure generator exits
                except asyncio.QueueFull:
                    pass 
        manager.disconnect(session_id)
        if session_id in active_session_states:
            del active_session_states[session_id]
        log.info(f"Dictation WS session {session_id} cleanup complete.")
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config.security import verify_token
from src.modules.transcription.schemas import SessionState
from src.modules.transcription.service import process_dictation_and_save_note
from src.websocket.connection_manager import manager

log = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/dictation/{encounter_id}")
async def dictation_websocket(websocket: WebSocket, encounter_id: int):
    # Create a unique session ID for the connection manager
    session_id = f"dictation_{encounter_id}_{id(websocket)}"
    await manager.connect(session_id, websocket)
    
    state = None
    
    try:
        # 1. Authentication Check
        auth_msg = await websocket.receive_json()
        token = auth_msg.get("token")
        
        user_subject = verify_token(token)
        if not user_subject:
            log.warning(f"Unauthorized WS attempt for encounter {encounter_id}")
            await websocket.close(code=1008)
            manager.disconnect(session_id)
            return

        # 2. Initialize the Audio State Queue
        state = SessionState(
            id=session_id,
            encounter_id=encounter_id,
            author_id=int(user_subject) if user_subject.isdigit() else 1,
            note_type="DOCTOR_DICTATION"
        )

        # 3. Detach ASR Processing to a Background Task
        asr_task = asyncio.create_task(process_dictation_and_save_note(websocket, state))

        # 4. Stream Raw Audio to the Queue
        while True:
            data = await websocket.receive_bytes()
            await state.audio_queue.put(data)

    except WebSocketDisconnect:
        log.info(f"Client disconnected cleanly from encounter {encounter_id}")
    except Exception as e:
        log.error(f"WebSocket stream interrupted: {e}", exc_info=True)
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()
    finally:
        if state:
            state.is_active = False
            # Push a None payload to gracefully unblock the audio generator
            await state.audio_queue.put(None) 
        manager.disconnect(session_id)
# app/schemas/session.py
import asyncio
from typing import Optional

class SessionState:
    """
    Keeps track of the state for a single active WebSocket session
    (e.g., dictation or handoff).
    """
    def __init__(self, session_id: str):
        self.id = session_id
        self.audio_queue = asyncio.Queue()
        self.is_active = True
        self.final_transcript = "" # Accumulates the full transcript text

        # Contextual data, set by the endpoint upon connection
        self.encounter_id: Optional[int] = None
        self.author_id: Optional[int] = None
        self.note_type: Optional[str] = None # e.g., 'doctor_dictation'
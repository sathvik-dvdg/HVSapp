import asyncio
from pydantic import BaseModel, Field

class SessionState(BaseModel):
    id: str
    encounter_id: int
    author_id: int
    note_type: str = "DOCTOR_DICTATION"
    is_active: bool = True
    final_transcript: str = ""
    # Pydantic requires arbitrary_types_allowed to handle asyncio.Queue
    audio_queue: asyncio.Queue = Field(default_factory=asyncio.Queue)

    class Config:
        arbitrary_types_allowed = True
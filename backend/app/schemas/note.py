# app/schemas/note.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import the enum from the model
from app.models.note import NoteType

# --- Base Schema (Common fields) ---
class NoteBase(BaseModel):
    content: str
    note_type: NoteType = NoteType.OTHER

# --- Schema for Creating a Note ---
# This is used by the service layer, as notes are created
# by the ASR service, not a direct user POST.
class NoteCreate(NoteBase):
    encounter_id: int
    author_id: int

# --- Schema for Reading Note Data (sent to client) ---
class NoteRead(NoteBase):
    """
    Data sent back to the client when reading a clinical note.
    """
    id: int
    encounter_id: int
    author_id: int
    created_at: datetime
    # You could add author details here later if needed
    # author: Optional[UserRead] = None 

    class Config:
        from_attributes = True  # Enable ORM mode (SQLAlchemy -> Pydantic)
from pydantic import BaseModel
from datetime import datetime

class NoteBase(BaseModel):
    content: str
    note_type: str

class NoteRead(NoteBase):
    id: int
    encounter_id: int
    author_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
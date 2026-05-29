from sqlalchemy.orm import Session
from src.modules.patients.note_models import ClinicalNote

def get_notes_for_encounter(db: Session, encounter_id: int):
    return db.query(ClinicalNote).filter(ClinicalNote.encounter_id == encounter_id).all()

def create_note(db: Session, **kwargs):
    pass # Implementation for ASR logic will go here
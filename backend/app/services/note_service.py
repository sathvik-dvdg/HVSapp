# app/services/note_service.py
import logging
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import project components
from app.models.note import ClinicalNote, NoteType
from app.models.encounter import Encounter # For validation
from app.models.user import User # For validation

log = logging.getLogger(__name__)

def create_note(
    db: Session,
    *,
    encounter_id: int,
    author_id: int,
    note_type: NoteType,
    content: str
) -> Optional[ClinicalNote]:
    """
    Creates and saves a clinical note to the database.
    Validates encounter and author existence.
    """
    log.info(f"Attempting to save note for encounter {encounter_id} by author {author_id}")

    # --- Basic Validation ---
    # 1. Check if encounter exists
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        log.error(f"Cannot save note: Encounter {encounter_id} not found.")
        return None
    
    # 2. Check if author exists
    author = db.query(User).filter(User.id == author_id).first()
    if not author:
        log.error(f"Cannot save note: Author {author_id} not found.")
        return None
    
    # 3. Check for empty content
    if not content or not content.strip():
        log.warning(f"Attempted to save empty note for encounter {encounter_id}.")
        return None # Don't save empty notes

    try:
        # Create the ClinicalNote object
        db_note = ClinicalNote(
            encounter_id=encounter_id,
            author_id=author_id,
            note_type=note_type,
            content=content.strip() # Ensure no leading/trailing whitespace
        )
        
        # Add, commit, and refresh
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        log.info(f"Successfully saved note ID: {db_note.id} for encounter {encounter_id}")
        return db_note

    except SQLAlchemyError as e:
        log.error(f"Database error saving note for encounter {encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None
    except Exception as e:
        log.error(f"Unexpected error saving note for encounter {encounter_id}: {e}", exc_info=True)
        db.rollback()
        return None

def get_notes_for_encounter(db: Session, *, encounter_id: int) -> List[ClinicalNote]:
    """
    Retrieves all clinical notes associated with a specific encounter,
    ordered by creation time (newest first).
    """
    log.debug(f"Querying for notes associated with encounter ID: {encounter_id}")
    
    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.encounter_id == encounter_id)
        .order_by(ClinicalNote.created_at.desc()) # Show newest notes first
        .all()
    )
    
    log.info(f"Found {len(notes)} notes for encounter ID: {encounter_id}")
    return notes
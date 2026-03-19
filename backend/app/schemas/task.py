# app/schemas/task.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import the enum from the model
from app.models.task import TaskStatus

# --- Base Schema (Common fields) ---
class TaskBase(BaseModel):
    """Base Pydantic model for Task, defines common fields."""
    description: str
    encounter_id: int # Must be linked to an encounter
    due_at: Optional[datetime] = None
    assigned_nurse_id: Optional[int] = None # Can be assigned later

# --- Schema for Creating a Task ---
class TaskCreate(TaskBase):
    """Data required to create a new task."""
    pass # No extra fields needed beyond TaskBase

# --- Schema for Updating a Task ---
class TaskUpdate(BaseModel):
    """Pydantic model for updating a task (all fields optional)."""
    description: Optional[str] = None
    status: Optional[TaskStatus] = None # e.g., to 'CANCELLED' or 'DELAYED'
    due_at: Optional[datetime] = None
    assigned_nurse_id: Optional[int] = None

# --- Schema for Reading Task Data (sent to client) ---
class TaskRead(TaskBase):
    """
    Data sent back to the client when reading a task.
    Includes the generated ID and status/timestamps.
    """
    id: int
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    # You could join and add author/nurse details here later
    # assigned_nurse: Optional[UserRead] = None 

    class Config:
        from_attributes = True # Enable ORM mode (SQLAlchemy -> Pydantic)
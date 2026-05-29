# app/db/base.py

# Import the Base class that all models inherit from
from src.db.base_class import Base

# --- CRITICAL ---
# Import all your models here so that Alembic can
# detect them and generate migrations.
from src.schemas.user import User
from src.schemas.patient import Patient
from src.schemas.encounter import Encounter
from src.schemas.note import ClinicalNote
from src.schemas.task import NurseTask
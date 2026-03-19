# app/db/base.py

# Import the Base class that all models inherit from
from app.db.base_class import Base

# --- CRITICAL ---
# Import all your models here so that Alembic can
# detect them and generate migrations.
from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.note import ClinicalNote
from app.models.task import NurseTask
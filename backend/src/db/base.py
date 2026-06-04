# src/db/base.py
from src.db.base_class import Base

# --- CRITICAL ---
from src.modules.auth.models import User
from src.modules.patients.models import Patient
from src.modules.patients.encounter_models import Encounter
from src.modules.patients.note_models import ClinicalNote

from src.modules.tasks.models import NurseTask
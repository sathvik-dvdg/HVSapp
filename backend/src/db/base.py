# src/db/base.py
from src.db.base_class import Base

# --- CRITICAL ---
from src.modules.auth.models import User
from src.modules.audit.models import AuditLog
from src.modules.medication.models import MedicationOrder, MedicationTask
from src.modules.patients.models import Patient
from src.modules.patients.encounter_models import Encounter
from src.modules.patients.note_models import ClinicalNote

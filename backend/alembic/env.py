import os
import sys
# Ensure the root backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.base_class import Base
# Import all models so Alembic autogenerate detects them
from src.modules.auth.models import User
from src.modules.patients.models import Patient
from src.modules.patients.encounter_models import Encounter

target_metadata = Base.metadata
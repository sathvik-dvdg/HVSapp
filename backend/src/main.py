# backend/src/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.session import engine
# Import domain-specific routers
from src.modules.auth import router as auth_router
from src.modules.patients import router as patient_router
from src.modules.patients import encounter_router
from src.modules.transcription import ws_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("--- HVS Backend Startup ---")
    try:
        with engine.connect() as connection:
            log.info("Database connection successful!")
    except Exception as e:
        log.critical(f"FATAL: Database connection failed: {e}")
    yield
    engine.dispose()

app = FastAPI(title="HVS API Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
app.include_router(auth_router.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(patient_router.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(encounter_router.router, prefix="/api/v1/encounters", tags=["Encounters"])
app.include_router(ws_router.router, tags=["Real-Time Dictation"])

@app.get("/", tags=["Root"])
def health_check():
    return {"Status": "HVS Backend is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
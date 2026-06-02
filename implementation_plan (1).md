# Hospital Handoff Validation System (HVS-APP)
# Implementation Plan — Continuation from Existing Codebase

**Document Version:** 1.0  
**Prepared For:** Engineering & Clinical Informatics Team  
**Classification:** Internal — Safety-Critical Healthcare System  
**Date:** 2025

---

## CRITICAL SAFETY DISCLAIMER

This is a safety-critical healthcare system. Every implementation decision in this document prioritizes **patient safety over development velocity**. No feature should be shipped without passing the clinical validation checkpoints defined in this plan. Violations of these checkpoints may directly harm patients.

---

## TABLE OF CONTENTS

1. [Existing Architecture Analysis](#1-existing-architecture-analysis)
2. [Feature Map](#2-feature-map)
3. [Gap Analysis](#3-gap-analysis)
4. [Recommended System Architecture](#4-recommended-system-architecture)
5. [Database Design](#5-database-design)
6. [API Design](#6-api-design)
7. [ASR Recommendation](#7-asr-recommendation)
8. [Medication Scheduler Design](#8-medication-scheduler-design)
9. [Handoff Validation Workflow](#9-handoff-validation-workflow)
10. [Notification Architecture](#10-notification-architecture)
11. [Safety Mechanisms](#11-safety-mechanisms)
12. [Security Model](#12-security-model)
13. [Implementation Roadmap](#13-implementation-roadmap)
14. [Refactoring Risks](#14-refactoring-risks)
15. [Production Readiness Strategy](#15-production-readiness-strategy)

---

## 1. EXISTING ARCHITECTURE ANALYSIS

### 1.1 Technology Stack

| Layer | Technology | Evidence |
|---|---|---|
| Frontend | React Native (Expo) | `frontend/package.json`, `app.json` |
| Frontend UI | React Native Paper | `package.json` dependencies |
| Frontend Routing | Expo Router (file-based) | `frontend/src/app/` directory structure |
| Backend | Python 3, FastAPI, Uvicorn | `backend/requirements.txt`, `main.py` |
| Database | PostgreSQL via SQLAlchemy ORM | `backend/src/db/session.py`, `base_class.py` |
| Migrations | Alembic | `backend/alembic/versions/` |
| Authentication | OAuth2 + JWT Bearer | `backend/src/config/security.py`, `auth/router.py` |
| ASR | Google Cloud Speech-to-Text (medical_dictation model) | `backend/src/modules/transcription/service.py` |
| Real-time | WebSockets (FastAPI native) | `backend/src/modules/transcription/ws_router.py` |
| State Management | React Context API | `frontend/src/features/auth/AuthContext.js` |

**Confidence: HIGH** — All conclusions drawn from observed folder structure and codebase analysis provided.

### 1.2 Existing Backend Module Analysis

#### `backend/src/modules/auth/`
- **Purpose:** User registration, login, and JWT issuance.
- **Files:** `models.py`, `router.py`, `schemas.py`, `service.py`, `token_schema.py`
- **Flow:** POST to `/api/v1/login/token` → `authenticate_user()` → bcrypt verify → issue JWT with username as subject
- **RBAC:** Roles `DOCTOR`, `NURSE`, `ADMIN` defined. No `RECEPTIONIST`, `LAB_TECHNICIAN`, or `PHARMACIST` roles exist yet.
- **⚠️ Risk:** Open registration endpoint `/api/v1/register` has no guard against self-assigning `ADMIN` role.

#### `backend/src/modules/patients/`
- **Purpose:** Patient record management and encounter lifecycle tracking.
- **Files:** `models.py`, `router.py`, `schemas.py`, `service.py`, `encounter_models.py`, `encounter_router.py`, `encounter_schemas.py`, `encounter_service.py`, `note_models.py`, `note_schemas.py`, `note_service.py`
- **Flow:** Patient created → Encounter opened → Status transitions (`PENDING_TRIAGE → ACTIVE → DISCHARGED`) → Labs/meds patched incrementally
- **ENUMs detected:** `EncounterType`, `EncounterStatus`, `LabReportStatus`
- **⚠️ Risk:** `Patient.id` is a String primary key (format `YYYYMMDD-XXXX`). Foreign key joins will degrade at scale. Needs integer or UUID surrogate key.

#### `backend/src/modules/transcription/`
- **Purpose:** Real-time ASR via WebSocket streaming to Google Cloud Speech API.
- **Files:** `ws_router.py`, `service.py`, `schemas.py`
- **Flow:** WS connection → `SessionState` created → `process_dictation_and_save_note()` spawned → audio queue feeds `audio_stream_generator()` → Google Speech streaming → interim transcripts sent back → on disconnect, `ClinicalNote` saved via `asyncio.to_thread`
- **⚠️ CRITICAL BUG:** Token delivery mismatch. Frontend sends token in URL query string; backend waits for JSON payload. This causes a connection hang or `1008 Policy Violation` crash. **Core feature is broken.**
- **⚠️ Risk:** `SessionLocal()` opened dynamically in async context; pool exhaustion possible on crash.

#### `backend/src/modules/medication/`
- **File:** `service.py` only
- **Status:** Stub/incomplete. No router, no model, no schema. **Not wired to any endpoint.**

#### `backend/src/modules/validation/`
- **File:** `service.py` only
- **Status:** Stub/incomplete. No router, no model. **Not wired to any endpoint.**

#### `backend/src/modules/audit/`
- **Status:** Directory exists, no files visible. **Completely unimplemented.**

### 1.3 Existing Frontend Module Analysis

#### `frontend/src/app/(auth)/login.js`
- Standard login form. Calls `/api/v1/login/token`.
- Stores JWT in context via `AuthContext`.

#### `frontend/src/app/(tabs)/dashboard.js`
- Role-aware: Doctor sees critical alerts; Nurse sees tasks + alerts.
- Calls `/api/v1/encounters/alerts/critical` via HTTP pull (not WebSocket push).
- Uses `RefreshControl` — manual pull-to-refresh only. **No real-time alerting.**

#### `frontend/src/app/patient/[id]/dictation.js`
- Entry point for voice dictation.
- Depends on `legacy_api.js → startStreamingAudio()`.
- **⚠️ CRITICAL BUG:** `startStreamingAudio()` opens a WebSocket but does not stream audio chunks. Comment in code reads: *"True streaming not yet implemented."*

#### `frontend/src/features/handoff/audioStream.js`
- Contains native audio streaming logic using `react-native-live-audio-stream`.
- **⚠️ Orphaned:** Not imported by any screen. Completely disconnected from the dictation flow.

#### `frontend/src/services/legacy_api.js`
- Hardcodes backend IP `10.19.73.68:8000`.
- Single-file API abstraction with fetch wrappers and WebSocket management.
- **⚠️ Risk:** Will fail on any network change. Must be migrated to `EXPO_PUBLIC_API_URL`.

---

## 2. FEATURE MAP

### ✅ Implemented (Verified)

| Feature | Status | Confidence |
|---|---|---|
| User login with JWT | Working | HIGH |
| Role-based routing (Doctor/Nurse) | Working | HIGH |
| Patient registration | Working | HIGH |
| Patient search | Working | HIGH |
| Encounter creation and state transitions | Working | HIGH |
| Lab status update endpoints | Working | HIGH |
| Critical alerts aggregation endpoint | Working | HIGH |
| Clinical note model + save on dictation end | Working (backend only) | HIGH |
| WebSocket connection management (in-memory) | Working | HIGH |
| Google ASR integration (backend generator) | Implemented, untested end-to-end | MEDIUM |

### ⚠️ Partially Implemented

| Feature | Status | Gap |
|---|---|---|
| Live dictation (ASR) | Backend ready, frontend broken | WS auth mismatch + no audio streaming |
| Medication module | DB schema may exist, service stub only | No router, no scheduler, no task engine |
| Validation module | Service stub only | No logic implemented |
| Audit logging | Directory exists, no code | Completely missing |

### ❌ Not Implemented

| Feature | Priority |
|---|---|
| Handoff validation workflow | CRITICAL |
| Medication task scheduler | CRITICAL |
| Smart notification engine | HIGH |
| Push notifications for critical alerts | HIGH |
| Token refresh mechanism | HIGH |
| Vitals tracking | HIGH |
| Allergy and risk factor management | HIGH |
| Digital signature for handoffs | HIGH |
| Lab report attachment/upload | MEDIUM |
| Ward/ICU transfer tracking | MEDIUM |
| Pharmacist and Lab Tech roles | MEDIUM |
| Tamper-proof audit trail | HIGH |
| PHI encryption at rest | HIGH |

---

## 3. GAP ANALYSIS

### What Exists and is Reusable

- FastAPI application shell, CORS config, Alembic migration pipeline → **KEEP AS-IS**
- Auth module (JWT issuance, bcrypt hashing) → **EXTEND** (add refresh tokens, new roles)
- Patient and Encounter models → **EXTEND** (add vitals, allergies, transfer history)
- WebSocket connection manager → **EXTEND** (add room-based broadcasting)
- Google ASR integration backend service → **FIX + EXTEND**
- Expo Router navigation structure → **KEEP + ADD screens**
- AuthContext → **EXTEND** (add role permissions matrix)

### What Must Be Fixed Before Any New Feature

| Issue | Risk Level | Why |
|---|---|---|
| WebSocket auth mismatch | 🔴 CRITICAL | Core dictation feature crashes. Fix first. |
| Audio streaming gap in frontend | 🔴 CRITICAL | Even after auth fix, no audio reaches backend. |
| Hardcoded IP in `legacy_api.js` | 🔴 HIGH | App fails on any network change or production build. |
| Open admin registration | 🔴 HIGH | Security hole. Any user can self-promote to ADMIN. |

### What Should Be Extended (Medium Risk)

| Item | Change Type | Risk |
|---|---|---|
| Patient model | Add vitals, allergies, risk flags | MEDIUM — requires migration |
| Encounter model | Add handoff status, transfer records | MEDIUM — requires migration |
| RBAC roles | Add PHARMACIST, LAB_TECH, RECEPTIONIST | LOW — additive change |
| Notification infrastructure | New module | MEDIUM |
| Medication module | Complete from stub | MEDIUM |

### What Should Be Rewritten

| Item | Reason | Risk |
|---|---|---|
| `legacy_api.js` | Hardcoded IP, mixed concerns, no streaming | MEDIUM — must not break login/patient flows |
| WebSocket auth in `ws_router.py` | Protocol mismatch causes crashes | LOW — isolated file |
| `startStreamingAudio()` in legacy_api.js | Doesn't stream audio | LOW after audioStream.js integration |

### What Must Never Be Touched Without Migration Plan

- Alembic migration files already applied to production DB
- `Patient.id` string format — changing primary key type requires full data migration
- JWT secret key environment variable — rotation requires all active sessions to re-login

---

## 4. RECOMMENDED SYSTEM ARCHITECTURE

### 4.1 Updated Backend Architecture

```
backend/src/
├── config/
│   ├── config.py              ← Add: EXPO_PUBLIC_API_URL, Redis URL, FCM key
│   └── security.py            ← Add: refresh token logic
├── db/
│   ├── base_class.py
│   └── session.py             ← Add: connection pool config (max_overflow, pool_timeout)
├── middleware/
│   ├── audit_middleware.py     ← NEW: log every state-changing request
│   └── rate_limit.py          ← NEW: protect auth endpoints
├── modules/
│   ├── auth/                  ← EXTEND: add refresh tokens, new roles
│   ├── patients/              ← EXTEND: add vitals, allergies, transfers
│   ├── encounters/            ← EXTEND: add handoff_status field
│   ├── handoff/               ← NEW: handoff validation workflow
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── router.py
│   │   └── service.py
│   ├── medication/            ← COMPLETE: full task engine
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── scheduler.py
│   ├── notifications/         ← NEW: push + in-app notification engine
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── router.py
│   │   └── service.py
│   ├── transcription/         ← FIX: auth bug + EXTEND for structured extraction
│   ├── audit/                 ← COMPLETE: tamper-proof audit logs
│   │   ├── models.py
│   │   └── service.py
│   └── validation/            ← COMPLETE: clinical safety rule engine
│       ├── rules.py
│       └── service.py
├── tasks/
│   └── celery_app.py          ← NEW: async task queue (Celery + Redis)
└── main.py                    ← Add: Celery startup, new routers
```

### 4.2 Updated Frontend Architecture

```
frontend/src/
├── app/
│   ├── (auth)/
│   │   └── login.js
│   ├── (tabs)/
│   │   ├── dashboard.js       ← EXTEND: real-time WS alerts
│   │   ├── patients.js
│   │   ├── handoff/           ← NEW: handoff screens
│   │   └── notifications.js   ← NEW
│   └── patient/[id]/
│       ├── index.js
│       ├── dictation.js       ← FIX: wire audioStream.js
│       ├── medications.js     ← NEW: medication task view
│       ├── vitals.js          ← NEW
│       ├── handoff.js         ← NEW: initiate/accept handoff
│       ├── history.js
│       ├── notes.js
│       └── tasks.js
├── features/
│   ├── auth/
│   │   └── AuthContext.js     ← EXTEND: permissions matrix
│   ├── handoff/
│   │   ├── audioStream.js     ← INTEGRATE into dictation.js
│   │   └── HandoffContext.js  ← NEW
│   ├── medications/           ← NEW
│   ├── notifications/         ← NEW: FCM integration
│   └── validation/            ← NEW: client-side safety checks
└── services/
    ├── api.js                 ← NEW: replace legacy_api.js with env-variable-based client
    ├── websocket.js           ← NEW: unified WS manager
    └── legacy_api.js          ← DEPRECATE: keep during transition only
```

### 4.3 Infrastructure Additions Required

| Component | Purpose | Technology |
|---|---|---|
| Task Queue | Medication scheduling, async notifications | Celery + Redis |
| Push Notifications | Critical alerts to nurses/doctors | Firebase Cloud Messaging (FCM) |
| Background Worker | Cron jobs for overdue medication escalation | Celery Beat |
| Secrets Management | API keys, JWT secrets | Environment variables / Vault |

---

## 5. DATABASE DESIGN

### 5.1 Extended Entity Relationship Model

#### Existing Tables (Extend Only)

**`users` table — EXTEND**
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS
  refresh_token       VARCHAR(512),
  device_token        VARCHAR(512),   -- FCM push token
  last_active         TIMESTAMP,
  is_active           BOOLEAN DEFAULT TRUE,
  ward_assignment     VARCHAR(100);

-- Add new roles to ENUM
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECEPTIONIST';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'LAB_TECHNICIAN';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PHARMACIST';
```

**`patients` table — EXTEND**
```sql
ALTER TABLE patients ADD COLUMN IF NOT EXISTS
  date_of_birth       DATE,
  gender              VARCHAR(20),
  blood_group         VARCHAR(10),
  phone_number        VARCHAR(20),
  emergency_contact   VARCHAR(200),
  known_allergies     TEXT[],          -- Array of allergy strings
  risk_flags          TEXT[],          -- ['FALL_RISK', 'DNR', 'ISOLATION']
  primary_doctor_id   INTEGER REFERENCES users(id),
  ward                VARCHAR(100),
  bed_number          VARCHAR(20),
  admission_weight_kg FLOAT,
  created_at          TIMESTAMP DEFAULT NOW();
```

**`encounters` table — EXTEND**
```sql
ALTER TABLE encounters ADD COLUMN IF NOT EXISTS
  handoff_status      VARCHAR(50) DEFAULT 'NOT_REQUIRED',
  -- Values: NOT_REQUIRED, PENDING_HANDOFF, HANDOFF_IN_PROGRESS, HANDOFF_COMPLETE
  attending_nurse_id  INTEGER REFERENCES users(id),
  transfer_from_ward  VARCHAR(100),
  transfer_to_ward    VARCHAR(100),
  estimated_discharge DATE,
  icu_flag            BOOLEAN DEFAULT FALSE,
  fall_risk_score     INTEGER,
  pain_score          INTEGER,
  last_vitals_at      TIMESTAMP,
  updated_at          TIMESTAMP;
```

#### New Tables

**`vitals`**
```sql
CREATE TABLE vitals (
  id                SERIAL PRIMARY KEY,
  encounter_id      INTEGER NOT NULL REFERENCES encounters(id),
  recorded_by       INTEGER NOT NULL REFERENCES users(id),
  recorded_at       TIMESTAMP NOT NULL DEFAULT NOW(),
  systolic_bp       INTEGER,
  diastolic_bp      INTEGER,
  heart_rate        INTEGER,
  spo2_percent      FLOAT,
  temperature_c     FLOAT,
  respiratory_rate  INTEGER,
  blood_glucose     FLOAT,
  pain_score        INTEGER CHECK (pain_score BETWEEN 0 AND 10),
  gcs_score         INTEGER CHECK (gcs_score BETWEEN 3 AND 15),
  notes             TEXT
);
CREATE INDEX idx_vitals_encounter ON vitals(encounter_id);
CREATE INDEX idx_vitals_recorded_at ON vitals(recorded_at DESC);
```

**`medication_orders`**
```sql
CREATE TABLE medication_orders (
  id                SERIAL PRIMARY KEY,
  encounter_id      INTEGER NOT NULL REFERENCES encounters(id),
  ordered_by        INTEGER NOT NULL REFERENCES users(id),
  drug_name         VARCHAR(200) NOT NULL,
  dose              VARCHAR(100) NOT NULL,
  route             VARCHAR(50) NOT NULL,   -- PO, IV, IM, SC, etc.
  frequency         VARCHAR(100) NOT NULL,  -- '8 hourly', 'QD', 'PRN', etc.
  start_datetime    TIMESTAMP NOT NULL,
  end_datetime      TIMESTAMP,
  is_active         BOOLEAN DEFAULT TRUE,
  special_instructions TEXT,
  created_at        TIMESTAMP DEFAULT NOW()
);
```

**`medication_tasks`** (the schedulable unit)
```sql
CREATE TABLE medication_tasks (
  id                SERIAL PRIMARY KEY,
  order_id          INTEGER NOT NULL REFERENCES medication_orders(id),
  encounter_id      INTEGER NOT NULL REFERENCES encounters(id),
  assigned_nurse_id INTEGER REFERENCES users(id),
  scheduled_at      TIMESTAMP NOT NULL,
  due_by            TIMESTAMP NOT NULL,     -- scheduled_at + grace_window (e.g. 30 min)
  status            VARCHAR(50) DEFAULT 'PENDING',
  -- Values: PENDING, ADMINISTERED, MISSED, SKIPPED, ESCALATED
  administered_at   TIMESTAMP,
  administered_by   INTEGER REFERENCES users(id),
  skipped_reason    TEXT,
  witness_id        INTEGER REFERENCES users(id),  -- for controlled substances
  notes             TEXT,
  escalation_level  INTEGER DEFAULT 0,
  -- 0=none, 1=reminder, 2=overdue_alert, 3=critical_escalation
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP
);
CREATE INDEX idx_med_tasks_scheduled ON medication_tasks(scheduled_at);
CREATE INDEX idx_med_tasks_status ON medication_tasks(status);
CREATE INDEX idx_med_tasks_encounter ON medication_tasks(encounter_id);
```

**`handoff_sessions`**
```sql
CREATE TABLE handoff_sessions (
  id                    SERIAL PRIMARY KEY,
  encounter_id          INTEGER NOT NULL REFERENCES encounters(id),
  outgoing_nurse_id     INTEGER NOT NULL REFERENCES users(id),
  incoming_nurse_id     INTEGER REFERENCES users(id),
  initiated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at          TIMESTAMP,
  status                VARCHAR(50) DEFAULT 'INITIATED',
  -- Values: INITIATED, IN_PROGRESS, PENDING_ACCEPTANCE, ACCEPTED, REJECTED, ESCALATED, EXPIRED
  checklist_snapshot    JSONB NOT NULL,  -- snapshot of all checks at initiation time
  validation_results    JSONB,           -- detailed pass/fail per check
  outstanding_items     TEXT[],          -- items blocking acceptance
  outgoing_signature    TEXT,            -- base64 digital signature
  incoming_signature    TEXT,
  rejection_reason      TEXT,
  supervisor_notified   BOOLEAN DEFAULT FALSE,
  escalated_to          INTEGER REFERENCES users(id),
  audit_hash            VARCHAR(256)     -- SHA-256 of session JSON for tamper detection
);
CREATE INDEX idx_handoff_encounter ON handoff_sessions(encounter_id);
CREATE INDEX idx_handoff_status ON handoff_sessions(status);
```

**`handoff_checklist_items`**
```sql
CREATE TABLE handoff_checklist_items (
  id                SERIAL PRIMARY KEY,
  handoff_session_id INTEGER NOT NULL REFERENCES handoff_sessions(id),
  category          VARCHAR(100) NOT NULL,
  -- Values: MEDICATIONS, VITALS, LABS, DOCTOR_INSTRUCTIONS, ALLERGIES, FALL_RISK,
  --         PENDING_TASKS, EMERGENCY_RISKS, SPECIAL_OBSERVATIONS
  item_key          VARCHAR(200) NOT NULL,
  description       TEXT NOT NULL,
  is_critical       BOOLEAN DEFAULT FALSE,
  status            VARCHAR(50) DEFAULT 'PENDING',
  -- Values: PENDING, PASSED, FAILED, ACKNOWLEDGED_WITH_RISK
  verified_by       INTEGER REFERENCES users(id),
  verified_at       TIMESTAMP,
  notes             TEXT
);
```

**`notifications`**
```sql
CREATE TABLE notifications (
  id                SERIAL PRIMARY KEY,
  recipient_id      INTEGER NOT NULL REFERENCES users(id),
  sender_id         INTEGER REFERENCES users(id),
  type              VARCHAR(100) NOT NULL,
  -- Values: MED_DUE, MED_OVERDUE, MED_CRITICAL, HANDOFF_REQUEST, HANDOFF_ACCEPTED,
  --         HANDOFF_REJECTED, LAB_READY, CRITICAL_ALERT, DOCTOR_INSTRUCTION, ESCALATION
  priority          VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
  -- Values: LOW, MEDIUM, HIGH, CRITICAL
  title             VARCHAR(200) NOT NULL,
  body              TEXT NOT NULL,
  related_entity_type VARCHAR(50),    -- 'encounter', 'medication_task', 'handoff_session'
  related_entity_id INTEGER,
  is_read           BOOLEAN DEFAULT FALSE,
  is_delivered      BOOLEAN DEFAULT FALSE,
  push_sent_at      TIMESTAMP,
  read_at           TIMESTAMP,
  expires_at        TIMESTAMP,
  created_at        TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read);
CREATE INDEX idx_notifications_priority ON notifications(priority, created_at DESC);
```

**`audit_logs`** (tamper-evident)
```sql
CREATE TABLE audit_logs (
  id                BIGSERIAL PRIMARY KEY,
  timestamp         TIMESTAMP NOT NULL DEFAULT NOW(),
  user_id           INTEGER REFERENCES users(id),
  action            VARCHAR(200) NOT NULL,
  resource_type     VARCHAR(100) NOT NULL,
  resource_id       VARCHAR(200),
  patient_id        VARCHAR(100),
  ip_address        INET,
  user_agent        TEXT,
  request_payload   JSONB,
  response_status   INTEGER,
  old_value         JSONB,
  new_value         JSONB,
  session_id        VARCHAR(200),
  hash_chain        VARCHAR(256)   -- each record hashes itself + previous hash
);
-- Append-only: no UPDATE or DELETE should ever be issued against this table
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_patient ON audit_logs(patient_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
```

---

## 6. API DESIGN

### 6.1 Auth Extensions

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/auth/token` | POST | Login (rename from `/login/token`) | Form Data |
| `/api/v1/auth/refresh` | POST | Refresh JWT using refresh token | Bearer |
| `/api/v1/auth/logout` | POST | Invalidate refresh token | Bearer |
| `/api/v1/auth/device-token` | PUT | Register FCM device token | Bearer |

### 6.2 Patient Extensions

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/patients/{id}/vitals` | POST | Record vitals reading | Bearer |
| `/api/v1/patients/{id}/vitals` | GET | Vitals history (paginated) | Bearer |
| `/api/v1/patients/{id}/vitals/latest` | GET | Most recent vitals | Bearer |
| `/api/v1/patients/{id}/allergies` | PUT | Update allergy list | Bearer (DOCTOR) |
| `/api/v1/patients/{id}/risk-flags` | PUT | Update risk flags | Bearer (DOCTOR, NURSE) |
| `/api/v1/patients/{id}/transfer` | POST | Ward/ICU transfer | Bearer (DOCTOR, ADMIN) |

### 6.3 Medication Endpoints

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/encounters/{id}/medications` | POST | Create medication order | Bearer (DOCTOR) |
| `/api/v1/encounters/{id}/medications` | GET | List active orders | Bearer |
| `/api/v1/encounters/{id}/medications/{order_id}` | PATCH | Update/discontinue order | Bearer (DOCTOR) |
| `/api/v1/medication-tasks/my-tasks` | GET | Nurse's assigned tasks for current shift | Bearer (NURSE) |
| `/api/v1/medication-tasks/{id}/administer` | POST | Mark medication as administered | Bearer (NURSE) |
| `/api/v1/medication-tasks/{id}/skip` | POST | Skip with reason + supervisor notification | Bearer (NURSE) |
| `/api/v1/medication-tasks/overdue` | GET | All overdue tasks (escalation dashboard) | Bearer (ADMIN, DOCTOR) |

### 6.4 Handoff Endpoints

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/handoff/initiate` | POST | Start handoff for encounter | Bearer (NURSE) |
| `/api/v1/handoff/{session_id}` | GET | Fetch handoff session + checklist | Bearer |
| `/api/v1/handoff/{session_id}/checklist/{item_id}` | PATCH | Verify a checklist item | Bearer (NURSE) |
| `/api/v1/handoff/{session_id}/accept` | POST | Incoming nurse accepts (digital signature) | Bearer (NURSE) |
| `/api/v1/handoff/{session_id}/reject` | POST | Reject with reason | Bearer (NURSE) |
| `/api/v1/handoff/{session_id}/escalate` | POST | Escalate to supervisor | Bearer |
| `/api/v1/handoff/pending` | GET | Pending handoffs awaiting acceptance | Bearer |

### 6.5 Notification Endpoints

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `/api/v1/notifications` | GET | Inbox (paginated, filtered by priority) | Bearer |
| `/api/v1/notifications/{id}/read` | PATCH | Mark as read | Bearer |
| `/api/v1/notifications/read-all` | PATCH | Mark all as read | Bearer |
| `/api/v1/notifications/unread-count` | GET | Badge count | Bearer |

### 6.6 WebSocket Endpoints (Fixed + Extended)

| Endpoint | Purpose | Fix Required |
|---|---|---|
| `/ws/dictation/{encounter_id}` | Live ASR dictation | Fix auth mismatch (see Section 14) |
| `/ws/alerts` | Real-time critical alert broadcast | NEW |
| `/ws/handoff/{session_id}` | Live handoff progress sync | NEW |

---

## 7. ASR RECOMMENDATION

### 7.1 Comparison Matrix

| System | Medical Vocab | Latency | Offline | Cost | Deployment |
|---|---|---|---|---|---|
| Google Cloud Medical Speech | ★★★★★ | Low (streaming) | No | Moderate | Cloud API |
| AWS Transcribe Medical | ★★★★☆ | Low (streaming) | No | Moderate | Cloud API |
| Azure Cognitive Speech | ★★★★☆ | Low | No | Moderate | Cloud API |
| OpenAI Whisper (base/medium) | ★★★☆☆ | Medium (batch) | Yes | Low | Self-hosted |
| Medical Whisper (fine-tuned) | ★★★★☆ | Medium | Yes | Low/infra | Self-hosted |
| Deepgram Medical | ★★★★☆ | Very low | No | Low | Cloud API |

### 7.2 Recommendation

**Primary:** Continue with Google Cloud Speech-to-Text (`medical_dictation` model). Evidence basis: already integrated in `backend/src/modules/transcription/service.py`. The model handles drug names, clinical abbreviations, and medical terminology with high accuracy. Switching to another provider would require replacing a working backend integration without clear benefit.

**Secondary (Offline/Fallback):** Integrate Medical Whisper as a fallback for when Google API is unavailable (network outage, quota exhaustion). Run as a local containerized service.

### 7.3 Structured Note Extraction

After raw transcript is produced, add a post-processing pipeline using Claude API (or a locally-hosted LLM) to extract structured fields:

```
Input:  "Patient blood pressure dropped to 90 over 60. Doctor informed. Metoprolol paused."

Output: {
  "vitals_mentioned": { "systolic_bp": 90, "diastolic_bp": 60 },
  "actions_taken": ["Doctor notified", "Metoprolol paused"],
  "alert_level": "HIGH",
  "medications_changed": [{ "drug": "Metoprolol", "action": "PAUSED" }]
}
```

**Validation Rule:** Extracted structured data must be reviewed and confirmed by the nurse before it is committed to the patient record. No automatic acceptance of AI-extracted clinical data.

### 7.4 Noise Handling

- Apply Google's enhanced noise cancellation model parameter (`use_enhanced: true` in `RecognitionConfig`).
- Set `audio_channel_count: 1`, `sample_rate_hertz: 16000` (matches existing frontend config).
- Add voice activity detection (VAD) pause to avoid transcribing background hospital noise between spoken sentences.

---

## 8. MEDICATION SCHEDULER DESIGN

### 8.1 Architecture

```
Medication Order Created (by Doctor)
          │
          ▼
  OrderExpansionService
  (Generates individual MedicationTask records from frequency + start_datetime)
          │
          ▼
  medication_tasks table
          │
          ├──── Celery Beat (cron every 5 minutes) ────> MedicationTaskMonitor
          │                                                     │
          │                                          ┌──────────┴──────────┐
          │                                          │                     │
          │                                   Tasks due in        Tasks overdue
          │                                   next 30 min        past due_by
          │                                          │                     │
          │                                   Send REMINDER      Send OVERDUE ALERT
          │                                   notification       + escalate_level++
          │
          └──── WebSocket push ──────────────> Dashboard nurse card (real-time badge)
```

### 8.2 Task Generation Logic

When a medication order is created, generate tasks:

```python
# Pseudocode for task expansion
def expand_medication_order(order: MedicationOrder) -> List[MedicationTask]:
    tasks = []
    current = order.start_datetime
    while current < order.end_datetime (or open-ended):
        tasks.append(MedicationTask(
            order_id=order.id,
            encounter_id=order.encounter_id,
            scheduled_at=current,
            due_by=current + timedelta(minutes=30),  # 30-min grace window
            status="PENDING"
        ))
        current += frequency_to_timedelta(order.frequency)
    return tasks
```

### 8.3 Escalation Logic

| Time Past Due | Action | Level |
|---|---|---|
| 0–30 min | Reminder notification to assigned nurse | 1 |
| 31–60 min | Overdue alert to assigned nurse + charge nurse | 2 |
| 61–120 min | Critical escalation to attending doctor | 3 |
| 120+ min | Page doctor + log to audit trail as CRITICAL_MISS | 4 |

### 8.4 Safety Rules

- **Duplicate prevention:** A task cannot be marked ADMINISTERED if another task for the same drug is ADMINISTERED within the minimum dose interval.
- **Controlled substance witness:** High-risk medications (opioids, insulin) require a second nurse to confirm administration (`witness_id` field).
- **Allergy cross-check:** On order creation, cross-reference `drug_name` against patient's `known_allergies`. Block order if match found. Require physician override with reason.

### 8.5 Reliability

- Celery tasks are idempotent (checking status before sending notification prevents double-alerts).
- Redis used as broker with message persistence (`appendonly yes` in Redis config).
- On Celery worker restart, Beat scheduler re-scans all PENDING tasks with `due_by < NOW()` to catch missed windows.

---

## 9. HANDOFF VALIDATION WORKFLOW

### 9.1 Overview

The handoff system ensures that when Nurse A ends their shift, Nurse B cannot begin caring for a patient without explicitly acknowledging every critical item. **The handoff session blocks the encounter transfer until all CRITICAL checklist items are PASSED or ACKNOWLEDGED_WITH_RISK.**

### 9.2 Step-by-Step Workflow

```
STEP 1: INITIATION
  Nurse A initiates handoff for encounter X via /api/v1/handoff/initiate
  System auto-generates HandoffSession + ChecklistItems by querying:
    - Pending medication tasks
    - Outstanding lab results
    - Unacknowledged doctor instructions in ClinicalNotes
    - Active allergy flags
    - Risk flags (fall risk, DNR, isolation)
    - Vitals overdue (last vitals > 4 hours ago)
    - Pending NurseTask records
  HandoffSession.status = INITIATED

STEP 2: IN-PROGRESS REVIEW
  Nurse A reviews each ChecklistItem via PATCH /handoff/{id}/checklist/{item_id}
  Nurse A adds verbal context notes to each item
  System tracks: which items are PASSED vs still PENDING
  Critical items cannot be skipped — only PASSED or ACKNOWLEDGED_WITH_RISK

STEP 3: TRANSFER REQUEST
  Nurse A selects incoming_nurse_id (Nurse B)
  System sends Nurse B a HANDOFF_REQUEST notification (push + in-app)
  HandoffSession.status = PENDING_ACCEPTANCE

STEP 4: INCOMING REVIEW
  Nurse B opens handoff session on their device
  Nurse B reviews all checklist items and Nurse A's notes
  Nurse B may add questions/notes per item
  Any FAILED item blocks acceptance

STEP 5: DIGITAL ACCEPTANCE
  Nurse B provides device authentication (biometric or PIN)
  Nurse B submits digital signature to /handoff/{id}/accept
  System validates:
    - All CRITICAL items are PASSED or ACKNOWLEDGED_WITH_RISK
    - Nurse B has acknowledged allergy warnings
    - At least one valid clinical note exists for this encounter
  If validation passes: HandoffSession.status = ACCEPTED
  Encounter.attending_nurse_id updated to Nurse B

STEP 6: AUDIT TRAIL
  Full handoff session JSON is hashed and stored in audit_logs
  Both nurse IDs, timestamps, and checklist states are immutable records
```

### 9.3 Blocking Rules (Handoff CANNOT be accepted if:)

| Rule | Category | Override Allowed? |
|---|---|---|
| Any medication task is OVERDUE without escalation logged | MEDICATIONS | NO |
| Any CRITICAL lab result is unacknowledged | LABS | NO |
| Known allergy is not acknowledged by incoming nurse | ALLERGIES | NO |
| Patient vitals not recorded in last 4 hours | VITALS | Supervisor only |
| Doctor instruction notes exist but are unread | DOCTOR_INSTRUCTIONS | NO |
| DNR/isolation status not acknowledged | EMERGENCY_RISKS | NO |
| Incoming nurse is not on shift roster | SYSTEM | NO |

### 9.4 Escalation and Failure Scenarios

- If Nurse B rejects: Nurse A receives HANDOFF_REJECTED notification with reason. Nurse A must resolve outstanding items and re-initiate.
- If 30 minutes pass with no acceptance: Supervisor notified automatically.
- If 60 minutes pass with no acceptance: Doctor alerted. HandoffSession.status = ESCALATED.
- If Nurse B is unavailable: Charge nurse can delegate acceptance with audit trail entry.

---

## 10. NOTIFICATION ARCHITECTURE

### 10.1 Notification Delivery Stack

```
Event Trigger (e.g., medication overdue detected by Celery Beat)
        │
        ▼
NotificationService.create_notification(recipient_id, type, priority, ...)
        │
        ├──── Persist to notifications table (always)
        │
        ├──── WebSocket push (if recipient has active WS /ws/alerts session)
        │
        └──── FCM Push Notification (if recipient has registered device_token)
               Priority mapping:
               LOW      → FCM data-only (silent background)
               MEDIUM   → FCM notification (banner)
               HIGH     → FCM high priority notification (wake screen)
               CRITICAL → FCM high priority + sound + vibration + badge
```

### 10.2 Priority Levels and SLA

| Priority | Use Case | Max Delivery Time |
|---|---|---|
| LOW | Lab result ready (non-urgent), new note added | 5 minutes |
| MEDIUM | Medication due in 30 min, handoff request | 60 seconds |
| HIGH | Medication overdue, handoff incomplete 30min | 10 seconds |
| CRITICAL | Critical patient deterioration, 2+ hour medication miss | Immediate |

### 10.3 Escalation Chain

```
CRITICAL notification sent to Nurse
  └── No acknowledgement in 5 min → Escalate to Charge Nurse
       └── No acknowledgement in 5 min → Escalate to Attending Doctor
            └── No acknowledgement in 5 min → Page Doctor (SMS/pager integration)
                 └── Log as CRITICAL_UNACKNOWLEDGED in audit_logs
```

---

## 11. SAFETY MECHANISMS

### 11.1 Medication Safety Rules

| Rule Type | Description | Enforcement |
|---|---|---|
| Hard Block | Allergy cross-check on order creation | API rejects 409 CONFLICT; physician override requires explicit reason |
| Hard Block | Duplicate active order for same drug | API validates no active order for same drug in same encounter |
| Hard Block | Dose outside normal range | Validate against drug reference database (e.g., RxNorm) |
| Soft Warning | Controlled substance with no witness | Allow but flag task, require witness_id before task is CLOSED |
| Soft Warning | Medication administered significantly early (>20% window) | Allow but log warning in audit_trail |
| Forced Confirmation | High-alert medications (insulin, heparin, chemotherapy) | Two-step confirmation UI with drug name repeat-back |

### 11.2 Patient Identity Safety

- Every medication administration screen displays: patient name, DOB, bed number, and known allergies before the nurse can confirm.
- Barcode scanning integration (future phase) will link medication barcode to patient wristband QR code for positive patient identification.
- Wrong-patient protection: Nurse's assigned encounter list is filtered; a nurse cannot administer medication to a patient not in their ward assignment.

### 11.3 Clinical Checkpoint Model

```
LOW RISK actions (view records, add non-clinical notes)  → No checkpoint
MEDIUM RISK actions (add clinical notes, update vitals)  → Single confirmation
HIGH RISK actions (administer medication, update orders) → Two-step confirmation + identity check
CRITICAL actions (skip medication, override allergy block, discharge) → Supervisor confirmation required
```

### 11.4 Audit Trail Integrity

- All `audit_logs` records include a hash chain (`hash_chain = SHA256(current_record_json + previous_hash_chain)`).
- The audit table is append-only; database role for application user has no `UPDATE` or `DELETE` privileges on `audit_logs`.
- Periodic integrity checks: a Celery Beat task re-validates hash chain continuity daily and alerts admin on any break.

---

## 12. SECURITY MODEL

### 12.1 Role-Based Access Control Matrix

| Permission | ADMIN | DOCTOR | NURSE | RECEPTIONIST | LAB_TECH | PHARMACIST |
|---|---|---|---|---|---|---|
| Create patient | ✓ | ✓ | — | ✓ | — | — |
| View patient record | ✓ | ✓ | ✓ (own ward) | ✓ (limited) | ✓ (limited) | ✓ (limited) |
| Create medication order | — | ✓ | — | — | — | — |
| Administer medication | — | — | ✓ | — | — | — |
| Update lab status | — | — | — | — | ✓ | — |
| Initiate handoff | — | — | ✓ | — | — | — |
| Accept handoff | — | — | ✓ | — | — | — |
| View audit logs | ✓ | — | — | — | — | — |
| Manage users | ✓ | — | — | — | — | — |
| Override allergy block | — | ✓ | — | — | — | ✓ |

### 12.2 Authentication Hardening

| Issue | Fix | Priority |
|---|---|---|
| Open admin registration | Check role in registration; only ADMIN can create ADMIN/DOCTOR accounts | 🔴 CRITICAL |
| No refresh token | Implement refresh token rotation; store hashed in DB | 🔴 HIGH |
| Wildcard CORS | Replace `["*"]` with explicit allowed origins list | 🔴 HIGH |
| Token in WS URL | Migrate to JSON payload auth message on WS open | 🔴 CRITICAL |
| Session management | Add device_token tracking; invalidate on logout | 🟡 MEDIUM |

### 12.3 PHI Protection

- All API responses containing patient data must be served over HTTPS only (enforce at reverse proxy layer).
- Database: enable PostgreSQL row-level security (RLS) as a secondary defense layer.
- Sensitive fields (`known_allergies`, `risk_flags`, clinical notes) should be encrypted at rest using application-level encryption (AES-256) before storage.
- Logs must never contain full PHI; patient identifiers in logs should use internal IDs only.

### 12.4 Rate Limiting

- Auth endpoints (`/token`, `/refresh`): 5 requests/minute per IP.
- All other endpoints: 100 requests/minute per authenticated user.
- WebSocket connections: 3 concurrent connections per user.

---

## 13. IMPLEMENTATION ROADMAP

### PHASE 0 — Emergency Fixes (Week 1–2)
**Do this before any new feature. These are production blockers.**

| Task | Files | Risk | Owner |
|---|---|---|---|
| Fix WebSocket auth mismatch | `ws_router.py`, `legacy_api.js` | LOW | Backend + Frontend |
| Wire `audioStream.js` into dictation flow | `dictation.js`, `audioStream.js`, `legacy_api.js` | LOW | Frontend |
| Migrate `BASE_URL` to `EXPO_PUBLIC_API_URL` | `legacy_api.js`, `.env` | LOW | Frontend |
| Block self-assigned ADMIN role on registration | `auth/router.py`, `auth/service.py` | LOW | Backend |
| Replace `allow_origins=["*"]` with explicit list | `main.py` | LOW | Backend |

**Rollback strategy:** All Phase 0 changes are isolated bug fixes in existing files. Git revert is sufficient.

---

### PHASE 1 — Foundation (Week 3–6)
**Database migrations, infrastructure, and auth hardening.**

| Task | Dependencies | Risk |
|---|---|---|
| Alembic migration: extend `users`, `patients`, `encounters` tables | Phase 0 complete | MEDIUM |
| Alembic migration: create `vitals`, `audit_logs`, `notifications` tables | Above | LOW |
| Implement JWT refresh token endpoint | Auth module | LOW |
| Add FCM device token registration | Auth module | LOW |
| Implement `audit_logs` middleware (log all state changes) | New middleware | MEDIUM |
| Set up Celery + Redis (local dev) | Infrastructure | MEDIUM |
| Add new RBAC roles to ENUM | Auth module | LOW |

**Testing requirement:** All migrations must be tested against a copy of production schema before applying.  
**Rollback strategy:** Each Alembic migration has a `downgrade()` function. Test it before merging.

---

### PHASE 2 — Core Clinical Features (Week 7–14)

**Part A: Medication Engine**
| Task | Dependencies | Risk |
|---|---|---|
| Medication order model + schema + router | Phase 1 | LOW |
| Medication task generation service | Phase 1 | MEDIUM |
| Celery Beat: medication monitor cron job | Phase 1 (Celery) | MEDIUM |
| Medication task escalation logic | Above | MEDIUM |
| Frontend: medication task list screen | Phase 1 | LOW |
| Frontend: administer/skip confirmation flow | Above | MEDIUM |
| Allergy cross-check on order creation | Patient model extension | HIGH |

**Part B: Notifications**
| Task | Dependencies | Risk |
|---|---|---|
| Notification model + service | Phase 1 | LOW |
| FCM push notification delivery | Phase 1 (device token) | MEDIUM |
| WebSocket alert channel `/ws/alerts` | Phase 0 WS fix | MEDIUM |
| Frontend: notification inbox screen | Above | LOW |
| Frontend: real-time dashboard alerts | `/ws/alerts` | MEDIUM |

**Part C: Vitals**
| Task | Dependencies | Risk |
|---|---|---|
| Vitals model + router + service | Phase 1 migration | LOW |
| Frontend: vitals recording form | Above | LOW |
| Vitals history graph screen | Above | LOW |

---

### PHASE 3 — Handoff System (Week 15–20)
**The most critical and complex feature. Treat as safety-critical software.**

| Task | Dependencies | Risk |
|---|---|---|
| Handoff session + checklist models | Phase 1 | LOW |
| Checklist auto-generation service | Medication + vitals + notes | HIGH |
| Handoff initiation API | Above | MEDIUM |
| Checklist verification API | Above | MEDIUM |
| Digital signature implementation | Auth module | HIGH |
| Handoff accept/reject/escalate APIs | Above | HIGH |
| Supervisor escalation Celery task | Phase 2 Celery | MEDIUM |
| Frontend: handoff initiation flow | Above | MEDIUM |
| Frontend: incoming nurse review screen | Above | MEDIUM |
| Frontend: checklist verification UX | Above | HIGH |
| WebSocket: live handoff sync | Phase 0 WS | MEDIUM |
| Audit hash chain for handoff records | Audit module | HIGH |

**Testing requirement:** Handoff workflow must be clinically reviewed before deployment. Run scenario walkthroughs with nursing staff.

---

### PHASE 4 — Hardening & Production Readiness (Week 21–26)

| Task | Risk |
|---|---|
| PHI encryption at rest (application-level AES-256) | MEDIUM |
| Database RLS policies | MEDIUM |
| Rate limiting middleware | LOW |
| Audit log integrity validator (Celery Beat) | LOW |
| Replace `legacy_api.js` completely | MEDIUM |
| End-to-end security penetration testing | LOW (no code change) |
| Clinical scenario testing with nursing staff | LOW (no code change) |
| HIPAA/compliance documentation | LOW |
| Horizontal scaling: multi-worker Uvicorn + Redis-backed WS | HIGH |
| Performance testing: 100 concurrent WS connections | LOW |

---

## 14. REFACTORING RISKS

| Refactoring | Risk Level | Reason | Mitigation |
|---|---|---|---|
| Changing `Patient.id` from String to UUID | 🔴 CRITICAL | Breaks all existing foreign key relationships | Do NOT change until full data migration plan exists. Keep string PK, add `uuid` column as secondary identifier in Phase 4 |
| Replacing `legacy_api.js` | 🟡 MEDIUM | All screens depend on it | Incremental: create `api.js`, migrate one screen at a time, deprecate last |
| Changing WebSocket auth protocol | 🟢 LOW | Isolated to one backend file + one frontend call | Fix both sides in same PR; test immediately |
| Adding DB columns to existing tables | 🟢 LOW | Additive schema change; old rows get NULL | Use `DEFAULT` values in migration; no downtime required |
| Alembic migration on production | 🟡 MEDIUM | Risk of migration failure mid-run | Always take DB snapshot before applying. Test migration on staging first |
| Changing JWT structure | 🔴 HIGH | All active sessions become invalid | Schedule during low-traffic window; notify all users |
| Replacing in-memory WS connection manager with Redis-backed | 🟡 MEDIUM | Required for multi-worker scaling | Phase 4 only; add Redis WS adapter alongside existing manager, cut over atomically |

---

## 15. PRODUCTION READINESS STRATEGY

### 15.1 Minimum Viable Production Criteria

The following must ALL be true before the system handles real patient data:

- [ ] Phase 0 fixes deployed and verified (WS auth, audio streaming, IP hardcoding)
- [ ] HTTPS enforced on all API endpoints (reverse proxy with TLS certificate)
- [ ] Admin registration guarded
- [ ] JWT refresh tokens implemented
- [ ] Audit logging active for all state-changing endpoints
- [ ] Medication allergy cross-check implemented
- [ ] Handoff system clinically reviewed by a registered nurse
- [ ] Backup and restore procedure documented and tested
- [ ] Staging environment mirrors production schema
- [ ] All Alembic migrations applied cleanly to staging first

### 15.2 Environment Configuration

```
# Required environment variables (never commit to source control)
DATABASE_URL=postgresql://user:pass@host:5432/hvs_db
JWT_SECRET_KEY=<256-bit random secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-credentials.json
REDIS_URL=redis://redis:6379/0
FCM_SERVER_KEY=<Firebase server key>
CORS_ALLOWED_ORIGINS=["https://app.hvs.hospital"]
EXPO_PUBLIC_API_URL=https://api.hvs.hospital
```

### 15.3 Deployment Architecture

```
[Mobile App (Expo)]
      │ HTTPS
      ▼
[Nginx Reverse Proxy]  ←─── TLS termination, rate limiting
      │
      ├──── /api/*  ──────> [Uvicorn (FastAPI)] ─── [PostgreSQL]
      │                          │
      │                          └─── [Redis (Celery broker + WS sessions)]
      │                                    │
      │                               [Celery Worker(s)]
      │                               [Celery Beat]
      │
      └──── /ws/*  ───────> [Uvicorn (FastAPI WS)] ─── [Redis pub/sub]
```

### 15.4 Monitoring

- Application logs: structured JSON logging to file + log aggregation service (e.g., Loki or CloudWatch).
- Health check endpoint: `/api/v1/health` — returns DB connectivity, Redis connectivity, Celery worker status.
- Alerting: If Celery Beat stops running (medication scheduler silent), trigger ops alert within 5 minutes.
- Database: Enable slow query logging (threshold: 500ms). Index any query appearing in slow log.

---

## APPENDIX: CONFIDENCE RATINGS

| Section | Confidence | Basis |
|---|---|---|
| Existing stack identification | HIGH | Direct file structure evidence |
| WebSocket auth bug | HIGH | Explicit mismatch between `legacy_api.js` and `ws_router.py` |
| Audio streaming gap | HIGH | Code comment + isolated `audioStream.js` |
| Medication module completeness | MEDIUM | Only `service.py` stub visible; no router/model confirmed |
| Audit module completeness | MEDIUM | Directory present, no files visible |
| Patient model schema details | MEDIUM | ENUMs and FKs inferred from encounter_models.py patterns |
| Google ASR backend functionality | MEDIUM | Code structure is correct; end-to-end untested due to WS auth bug |

---

## 16. PHASE 0 — DETAILED FIX SPECIFICATIONS

This section provides exact, file-level instructions for every Phase 0 fix. Engineers should treat each subsection as a single, atomic PR.

---

### 16.1 Fix: WebSocket Authentication Mismatch

**Files to change:** `backend/src/modules/transcription/ws_router.py`, `frontend/src/services/legacy_api.js`

**Root Cause:** The frontend sends the JWT as a URL query parameter (`?token=<jwt>`). The backend ignores the query string and blocks waiting for a JSON body message `{ "token": "..." }` that never arrives. The connection hangs until the Google API deadline fires.

**Backend Fix — `ws_router.py`**

```python
# BEFORE (broken - waits for JSON payload that never arrives)
@router.websocket("/dictation/{encounter_id}")
async def dictation_ws(websocket: WebSocket, encounter_id: int):
    await websocket.accept()
    auth_msg = await websocket.receive_json()   # <-- HANGS FOREVER
    token = auth_msg.get("token")

# AFTER (fixed - reads token from query string, consistent with frontend)
from fastapi import WebSocket, Query, WebSocketDisconnect
from src.config.security import decode_access_token

@router.websocket("/dictation/{encounter_id}")
async def dictation_ws(
    websocket: WebSocket,
    encounter_id: int,
    token: str = Query(...),          # reads ?token=<jwt> from URL
):
    await websocket.accept()
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=1008)  # Policy Violation
        return
    username = payload.get("sub")
    if username is None:
        await websocket.close(code=1008)
        return
    # Continue with session setup using verified username
    ...
```

**`security.py` addition needed:**

```python
# Add to backend/src/config/security.py
from jose import JWTError, jwt
from src.config.config import settings

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Frontend Fix — `legacy_api.js`**

```javascript
// BEFORE
const ws = new WebSocket(`ws://${BASE_URL}/ws/dictation/${sessionId}?encounter_id=${encounterId}&token=${token}`);

// AFTER (no change needed on frontend side once backend reads from Query)
// The existing URL format is CORRECT from the frontend's perspective.
// Only the backend needed fixing to read from Query instead of waiting for JSON.
// However, clean up the duplicate encounter_id parameter:
const ws = new WebSocket(`ws://${BASE_URL}/ws/dictation/${encounterId}?token=${token}`);
```

**Testing checklist for this PR:**
- [ ] WS connects without hanging
- [ ] Invalid token returns close code 1008
- [ ] Missing token returns close code 1008
- [ ] Valid token proceeds to audio session setup

---

### 16.2 Fix: Audio Streaming Gap

**Files to change:** `frontend/src/app/patient/[id]/dictation.js`, `frontend/src/services/legacy_api.js`, `frontend/src/features/handoff/audioStream.js`

**Root Cause:** `startStreamingAudio()` in `legacy_api.js` configures `expo-av` and opens a WebSocket but never pipes audio bytes to the socket. `audioStream.js` has the correct native streaming logic (using `react-native-live-audio-stream`) but is completely orphaned.

**Step 1: Update `legacy_api.js` to accept a WebSocket reference and wire the audio callback**

```javascript
// In legacy_api.js - replace startStreamingAudio()
import { startAudioStream, stopAudioStream } from '../features/handoff/audioStream';

export const startStreamingAudio = async (encounterId, token, onTranscript, onError) => {
  const wsUrl = `ws://${BASE_URL}/ws/dictation/${encounterId}?token=${token}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[Dictation] WebSocket open, starting audio stream');
    // Wire audio chunks directly to the open socket
    startAudioStream((pcmChunk) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(pcmChunk);   // <-- THIS IS THE MISSING PIECE
      }
    });
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.transcript) {
      onTranscript(data.transcript, data.is_final);
    }
  };

  ws.onerror = (error) => {
    console.error('[Dictation] WebSocket error:', error);
    onError(error);
  };

  ws.onclose = (event) => {
    console.log('[Dictation] WebSocket closed:', event.code, event.reason);
    stopAudioStream();
  };

  return ws;  // return so caller can close it
};

export const stopStreamingAudio = (ws) => {
  stopAudioStream();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close(1000, 'User ended dictation');
  }
};
```

**Step 2: Export `startAudioStream` and `stopAudioStream` from `audioStream.js`**

```javascript
// In frontend/src/features/handoff/audioStream.js
// Add these exports wrapping the existing logic:

import LiveAudioStream from 'react-native-live-audio-stream';

const AUDIO_OPTIONS = {
  sampleRate: 16000,
  channels: 1,
  bitsPerSample: 16,
  audioSource: 6,       // VOICE_COMMUNICATION on Android
  bufferSize: 4096,
};

export const startAudioStream = (onChunk) => {
  LiveAudioStream.init(AUDIO_OPTIONS);
  LiveAudioStream.on('data', (data) => {
    // data is base64-encoded PCM; decode to binary before sending
    const binary = Buffer.from(data, 'base64');
    onChunk(binary);
  });
  LiveAudioStream.start();
};

export const stopAudioStream = () => {
  LiveAudioStream.stop();
};
```

**Step 3: Update `dictation.js` to use the updated API**

```javascript
// In frontend/src/app/patient/[id]/dictation.js
import { startStreamingAudio, stopStreamingAudio } from '../../../../services/legacy_api';

// Store WS reference in component state
const [wsRef, setWsRef] = useState(null);
const [transcript, setTranscript] = useState('');

const handleStartDictation = async () => {
  const ws = await startStreamingAudio(
    encounterId,
    token,
    (text, isFinal) => {
      setTranscript(prev => isFinal ? prev + text + ' ' : prev + text);
    },
    (err) => Alert.alert('Dictation Error', err.message)
  );
  setWsRef(ws);
};

const handleStopDictation = () => {
  stopStreamingAudio(wsRef);
  setWsRef(null);
};
```

---

### 16.3 Fix: Hardcoded IP Address

**File to change:** `frontend/src/services/legacy_api.js`

```javascript
// BEFORE
const BASE_URL = '10.19.73.68:8000';

// AFTER
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'localhost:8000';
// Remove the protocol from BASE_URL; prepend explicitly per request type:
// HTTP:  `http://${BASE_URL}/api/...`
// WS:    `ws://${BASE_URL}/ws/...`
// HTTPS: `https://${BASE_URL}/api/...`  (production)
// WSS:   `wss://${BASE_URL}/ws/...`     (production)
```

**Create `frontend/.env.development`:**
```
EXPO_PUBLIC_API_URL=10.19.73.68:8000
```

**Create `frontend/.env.production`:**
```
EXPO_PUBLIC_API_URL=api.hvs.hospital
```

**Add to `frontend/.gitignore`:**
```
.env.development
.env.production
.env.local
```

---

### 16.4 Fix: Open Admin Registration

**File to change:** `backend/src/modules/auth/router.py`

```python
# BEFORE (allows anyone to register as ADMIN)
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return await create_user(db, user_data)

# AFTER — ADMIN and DOCTOR accounts require an existing ADMIN to create them
from src.api.dependencies import get_current_user

@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),  # optional auth
):
    # ADMIN and DOCTOR roles can only be created by an existing ADMIN
    if user_data.role in (UserRole.ADMIN, UserRole.DOCTOR):
        if current_user is None or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only an existing ADMIN can create ADMIN or DOCTOR accounts."
            )
    # NURSE, RECEPTIONIST accounts are self-registerable (adjust per hospital policy)
    return await create_user(db, user_data)
```

**Add `get_optional_current_user` to `dependencies.py`:**

```python
# In backend/src/api/dependencies.py
async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
```

---

### 16.5 Fix: CORS Wildcard

**File to change:** `backend/src/main.py`

```python
# BEFORE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER
from src.config.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,  # List[str] from env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

**Add to `config.py`:**
```python
CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:8081", "http://localhost:19006"]
# Override in production via environment variable: CORS_ALLOWED_ORIGINS='["https://app.hvs.hospital"]'
```

---

## 17. ALEMBIC MIGRATION TEMPLATES

All migrations must follow this naming convention: `YYYYMMDD_HHMM-<auto_hash>_<description>.py`

---

### Migration 001 — Extend Core Tables (Phase 1)

```python
# alembic/versions/001_extend_users_patients_encounters.py
"""Extend users, patients, encounters with clinical fields

Revision ID: 001_clinical_extensions
Revises: 73dad259939a  # last existing migration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ── users ──────────────────────────────────────────────────────────────
    op.add_column('users', sa.Column('refresh_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('device_token', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('last_active', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true'))
    op.add_column('users', sa.Column('ward_assignment', sa.String(100), nullable=True))

    # Add new roles to existing ENUM (PostgreSQL-specific, non-transactional)
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECEPTIONIST'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'LAB_TECHNICIAN'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PHARMACIST'")

    # ── patients ───────────────────────────────────────────────────────────
    op.add_column('patients', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('patients', sa.Column('gender', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('blood_group', sa.String(10), nullable=True))
    op.add_column('patients', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact', sa.String(200), nullable=True))
    op.add_column('patients', sa.Column('known_allergies',
        postgresql.ARRAY(sa.Text()), server_default='{}'))
    op.add_column('patients', sa.Column('risk_flags',
        postgresql.ARRAY(sa.Text()), server_default='{}'))
    op.add_column('patients', sa.Column('ward', sa.String(100), nullable=True))
    op.add_column('patients', sa.Column('bed_number', sa.String(20), nullable=True))
    op.add_column('patients', sa.Column('created_at',
        sa.DateTime(), server_default=sa.func.now()))

    # ── encounters ─────────────────────────────────────────────────────────
    op.add_column('encounters', sa.Column('handoff_status',
        sa.String(50), server_default='NOT_REQUIRED'))
    op.add_column('encounters', sa.Column('attending_nurse_id',
        sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('encounters', sa.Column('icu_flag',
        sa.Boolean(), server_default='false'))
    op.add_column('encounters', sa.Column('fall_risk_score', sa.Integer(), nullable=True))
    op.add_column('encounters', sa.Column('pain_score', sa.Integer(), nullable=True))
    op.add_column('encounters', sa.Column('last_vitals_at', sa.DateTime(), nullable=True))
    op.add_column('encounters', sa.Column('estimated_discharge', sa.Date(), nullable=True))
    op.add_column('encounters', sa.Column('updated_at', sa.DateTime(), nullable=True))

def downgrade():
    # Remove columns in reverse order
    for col in ['updated_at', 'estimated_discharge', 'last_vitals_at',
                'pain_score', 'fall_risk_score', 'icu_flag',
                'attending_nurse_id', 'handoff_status']:
        op.drop_column('encounters', col)

    for col in ['created_at', 'bed_number', 'ward', 'risk_flags',
                'known_allergies', 'emergency_contact', 'phone_number',
                'blood_group', 'gender', 'date_of_birth']:
        op.drop_column('patients', col)

    for col in ['ward_assignment', 'is_active', 'last_active',
                'device_token', 'refresh_token']:
        op.drop_column('users', col)
    # Note: cannot remove ENUM values in PostgreSQL without full type recreation
```

---

### Migration 002 — New Clinical Tables (Phase 1)

```python
# alembic/versions/002_create_clinical_tables.py
"""Create vitals, medication_orders, medication_tasks, notifications, audit_logs

Revision ID: 002_clinical_tables
Revises: 001_clinical_extensions
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # ── vitals ─────────────────────────────────────────────────────────────
    op.create_table('vitals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=False),
        sa.Column('recorded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('systolic_bp', sa.Integer()),
        sa.Column('diastolic_bp', sa.Integer()),
        sa.Column('heart_rate', sa.Integer()),
        sa.Column('spo2_percent', sa.Float()),
        sa.Column('temperature_c', sa.Float()),
        sa.Column('respiratory_rate', sa.Integer()),
        sa.Column('blood_glucose', sa.Float()),
        sa.Column('pain_score', sa.Integer(),
            sa.CheckConstraint('pain_score BETWEEN 0 AND 10')),
        sa.Column('gcs_score', sa.Integer(),
            sa.CheckConstraint('gcs_score BETWEEN 3 AND 15')),
        sa.Column('notes', sa.Text()),
    )
    op.create_index('idx_vitals_encounter', 'vitals', ['encounter_id'])
    op.create_index('idx_vitals_recorded_at', 'vitals', ['recorded_at'])

    # ── medication_orders ──────────────────────────────────────────────────
    op.create_table('medication_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=False),
        sa.Column('ordered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('drug_name', sa.String(200), nullable=False),
        sa.Column('dose', sa.String(100), nullable=False),
        sa.Column('route', sa.String(50), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('special_instructions', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_med_orders_encounter', 'medication_orders', ['encounter_id'])

    # ── medication_tasks ───────────────────────────────────────────────────
    op.create_table('medication_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('medication_orders.id'), nullable=False),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=False),
        sa.Column('assigned_nurse_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('due_by', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('administered_at', sa.DateTime()),
        sa.Column('administered_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('witness_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('skipped_reason', sa.Text()),
        sa.Column('notes', sa.Text()),
        sa.Column('escalation_level', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_med_tasks_scheduled', 'medication_tasks', ['scheduled_at'])
    op.create_index('idx_med_tasks_status', 'medication_tasks', ['status'])
    op.create_index('idx_med_tasks_encounter', 'medication_tasks', ['encounter_id'])

    # ── notifications ──────────────────────────────────────────────────────
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('priority', sa.String(20), server_default='MEDIUM', nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(50)),
        sa.Column('related_entity_id', sa.Integer()),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('is_delivered', sa.Boolean(), server_default='false'),
        sa.Column('push_sent_at', sa.DateTime()),
        sa.Column('read_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_notifications_recipient', 'notifications', ['recipient_id', 'is_read'])

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(200)),
        sa.Column('patient_id', sa.String(100)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('request_payload', sa.JSON()),
        sa.Column('response_status', sa.Integer()),
        sa.Column('old_value', sa.JSON()),
        sa.Column('new_value', sa.JSON()),
        sa.Column('session_id', sa.String(200)),
        sa.Column('hash_chain', sa.String(256)),
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_patient', 'audit_logs', ['patient_id'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('medication_tasks')
    op.drop_table('medication_orders')
    op.drop_table('vitals')
```

---

### Migration 003 — Handoff Tables (Phase 3)

```python
# alembic/versions/003_create_handoff_tables.py
"""Create handoff_sessions and handoff_checklist_items

Revision ID: 003_handoff_tables
Revises: 002_clinical_tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('handoff_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=False),
        sa.Column('outgoing_nurse_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('incoming_nurse_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('initiated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('status', sa.String(50), server_default='INITIATED', nullable=False),
        sa.Column('checklist_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('validation_results', postgresql.JSONB()),
        sa.Column('outstanding_items', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('outgoing_signature', sa.Text()),
        sa.Column('incoming_signature', sa.Text()),
        sa.Column('rejection_reason', sa.Text()),
        sa.Column('supervisor_notified', sa.Boolean(), server_default='false'),
        sa.Column('escalated_to', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('audit_hash', sa.String(256)),
    )
    op.create_index('idx_handoff_encounter', 'handoff_sessions', ['encounter_id'])
    op.create_index('idx_handoff_status', 'handoff_sessions', ['status'])

    op.create_table('handoff_checklist_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('handoff_session_id', sa.Integer(),
            sa.ForeignKey('handoff_sessions.id'), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('item_key', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_critical', sa.Boolean(), server_default='false'),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('verified_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('verified_at', sa.DateTime()),
        sa.Column('notes', sa.Text()),
    )

def downgrade():
    op.drop_table('handoff_checklist_items')
    op.drop_table('handoff_sessions')
```

---

## 18. BACKEND SERVICE BLUEPRINTS

### 18.1 Audit Middleware — `backend/src/middleware/audit_middleware.py`

```python
"""
Audit middleware: automatically logs every state-changing request to audit_logs.
Reads user identity from JWT without raising exceptions (silent fail on anon requests).
"""
import hashlib, json, time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.config.security import decode_access_token

AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in AUDITED_METHODS:
            return await call_next(request)

        # Capture request body for audit (must be re-injected for downstream)
        body_bytes = await request.body()
        try:
            payload_dict = json.loads(body_bytes) if body_bytes else {}
            # Redact sensitive fields
            for field in ("password", "token", "refresh_token"):
                payload_dict.pop(field, None)
        except Exception:
            payload_dict = {}

        response = await call_next(request)

        # Identify user from Bearer token (best-effort)
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_data = decode_access_token(auth_header[7:])
            if token_data:
                user_id = token_data.get("user_id")

        # Write audit record asynchronously
        db: Session = SessionLocal()
        try:
            from src.modules.audit.service import write_audit_log
            write_audit_log(
                db=db,
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                resource_type=_extract_resource_type(request.url.path),
                resource_id=_extract_resource_id(request.url.path),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                request_payload=payload_dict,
                response_status=response.status_code,
            )
        except Exception as e:
            print(f"[AUDIT] Failed to write audit log: {e}")
        finally:
            db.close()

        return response

def _extract_resource_type(path: str) -> str:
    parts = [p for p in path.split("/") if p and not p.isdigit()]
    return parts[-1] if parts else "unknown"

def _extract_resource_id(path: str) -> str | None:
    parts = path.split("/")
    for i, part in enumerate(parts):
        if part.isdigit():
            return part
    return None
```

**Register in `main.py`:**
```python
from src.middleware.audit_middleware import AuditMiddleware
app.add_middleware(AuditMiddleware)
```

---

### 18.2 Audit Service — `backend/src/modules/audit/service.py`

```python
import hashlib, json
from datetime import datetime
from sqlalchemy.orm import Session
from src.modules.audit.models import AuditLog

def write_audit_log(db: Session, **kwargs) -> AuditLog:
    """
    Appends an audit record with hash-chain integrity.
    NEVER call db.delete() or UPDATE on audit_logs.
    """
    # Get the most recent hash to chain from
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last.hash_chain if last else "GENESIS"

    # Build the record content for hashing
    record_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": kwargs.get("user_id"),
        "action": kwargs.get("action"),
        "resource_type": kwargs.get("resource_type"),
        "resource_id": kwargs.get("resource_id"),
        "previous_hash": previous_hash,
    }
    current_hash = hashlib.sha256(
        json.dumps(record_data, sort_keys=True).encode()
    ).hexdigest()

    log = AuditLog(
        **kwargs,
        timestamp=datetime.utcnow(),
        hash_chain=current_hash,
    )
    db.add(log)
    db.commit()
    return log
```

---

### 18.3 Medication Task Generator — `backend/src/modules/medication/service.py`

```python
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from src.modules.medication.models import MedicationOrder, MedicationTask

FREQUENCY_MAP = {
    "OD": timedelta(hours=24),
    "BD": timedelta(hours=12),
    "TDS": timedelta(hours=8),
    "QID": timedelta(hours=6),
    "Q4H": timedelta(hours=4),
    "Q2H": timedelta(hours=2),
    "STAT": None,  # one-time only
    "PRN": None,   # as-needed, not auto-scheduled
}

GRACE_WINDOW_MINUTES = 30  # nurse has 30 min after scheduled time to administer

def create_medication_order(db: Session, encounter_id: int, ordered_by: int,
                             order_data: dict) -> MedicationOrder:
    # Safety check: allergy cross-reference
    from src.modules.patients.service import get_patient_for_encounter
    patient = get_patient_for_encounter(db, encounter_id)
    drug = order_data["drug_name"].lower()
    for allergy in (patient.known_allergies or []):
        if allergy.lower() in drug or drug in allergy.lower():
            raise ValueError(
                f"ALLERGY_CONFLICT: Patient has known allergy to '{allergy}'. "
                f"Drug '{order_data['drug_name']}' may be contraindicated. "
                f"Physician override required."
            )

    order = MedicationOrder(encounter_id=encounter_id, ordered_by=ordered_by, **order_data)
    db.add(order)
    db.flush()  # get order.id before generating tasks

    tasks = expand_order_to_tasks(order)
    db.add_all(tasks)
    db.commit()
    return order

def expand_order_to_tasks(order: MedicationOrder) -> List[MedicationTask]:
    interval = FREQUENCY_MAP.get(order.frequency.upper())
    if interval is None:
        # PRN or STAT — no auto-scheduled tasks
        return []

    tasks = []
    current = order.start_datetime
    end = order.end_datetime or (order.start_datetime + timedelta(days=30))

    while current <= end:
        tasks.append(MedicationTask(
            order_id=order.id,
            encounter_id=order.encounter_id,
            scheduled_at=current,
            due_by=current + timedelta(minutes=GRACE_WINDOW_MINUTES),
            status="PENDING",
        ))
        current += interval

    return tasks

def administer_medication_task(db: Session, task_id: int, nurse_id: int,
                                notes: str = None, witness_id: int = None) -> MedicationTask:
    task = db.query(MedicationTask).filter(MedicationTask.id == task_id).first()
    if not task:
        raise ValueError("Task not found")
    if task.status not in ("PENDING", "ESCALATED"):
        raise ValueError(f"Cannot administer task in status: {task.status}")

    task.status = "ADMINISTERED"
    task.administered_at = datetime.utcnow()
    task.administered_by = nurse_id
    task.witness_id = witness_id
    task.notes = notes
    task.updated_at = datetime.utcnow()
    db.commit()
    return task
```

---

### 18.4 Handoff Checklist Generator — `backend/src/modules/handoff/service.py`

```python
"""
Handoff checklist auto-generation.
Queries all clinical state of the encounter and produces a structured checklist.
Every CRITICAL item must be resolved before acceptance.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.modules.handoff.models import HandoffSession, HandoffChecklistItem

VITALS_OVERDUE_HOURS = 4

def generate_checklist_items(db: Session, encounter_id: int) -> list[dict]:
    items = []
    now = datetime.utcnow()

    # ── 1. MEDICATIONS ─────────────────────────────────────────────────────
    from src.modules.medication.models import MedicationTask
    overdue_meds = db.query(MedicationTask).filter(
        MedicationTask.encounter_id == encounter_id,
        MedicationTask.status.in_(["PENDING", "ESCALATED"]),
        MedicationTask.due_by < now,
    ).all()
    for med in overdue_meds:
        items.append({
            "category": "MEDICATIONS",
            "item_key": f"overdue_med_{med.id}",
            "description": f"Medication task ID {med.id} is overdue (due: {med.due_by}). Confirm status.",
            "is_critical": True,
        })

    upcoming_meds = db.query(MedicationTask).filter(
        MedicationTask.encounter_id == encounter_id,
        MedicationTask.status == "PENDING",
        MedicationTask.scheduled_at.between(now, now + timedelta(hours=2)),
    ).all()
    for med in upcoming_meds:
        items.append({
            "category": "MEDICATIONS",
            "item_key": f"upcoming_med_{med.id}",
            "description": f"Medication due at {med.scheduled_at}. Ensure incoming nurse is aware.",
            "is_critical": False,
        })

    # ── 2. VITALS ──────────────────────────────────────────────────────────
    from src.modules.patients.encounter_models import Encounter
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if encounter and encounter.last_vitals_at:
        hours_since = (now - encounter.last_vitals_at).total_seconds() / 3600
        if hours_since > VITALS_OVERDUE_HOURS:
            items.append({
                "category": "VITALS",
                "item_key": "vitals_overdue",
                "description": f"Vitals last recorded {hours_since:.1f} hours ago. Record before handoff.",
                "is_critical": True,
            })

    # ── 3. ALLERGIES ───────────────────────────────────────────────────────
    from src.modules.patients.models import Patient
    patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
    if patient and patient.known_allergies:
        items.append({
            "category": "ALLERGIES",
            "item_key": "allergy_acknowledgement",
            "description": f"Patient allergies: {', '.join(patient.known_allergies)}. Incoming nurse must acknowledge.",
            "is_critical": True,
        })

    # ── 4. RISK FLAGS ──────────────────────────────────────────────────────
    if patient and patient.risk_flags:
        for flag in patient.risk_flags:
            items.append({
                "category": "EMERGENCY_RISKS",
                "item_key": f"risk_{flag.lower()}",
                "description": f"Patient flagged: {flag}. Confirm incoming nurse is aware.",
                "is_critical": flag in ("DNR", "ISOLATION", "CRITICAL"),
            })

    # ── 5. LABS ────────────────────────────────────────────────────────────
    # Query pending lab statuses from encounter
    if hasattr(encounter, 'lab_status') and encounter.lab_status == 'PENDING':
        items.append({
            "category": "LABS",
            "item_key": "pending_lab_results",
            "description": "Lab results are pending. Incoming nurse must monitor and notify doctor on arrival.",
            "is_critical": True,
        })

    # ── 6. PENDING TASKS ───────────────────────────────────────────────────
    from src.modules.patients.note_models import NurseTask
    pending_tasks = db.query(NurseTask).filter(
        NurseTask.encounter_id == encounter_id,
        NurseTask.is_completed == False,
    ).all() if hasattr(NurseTask, 'encounter_id') else []
    for task in pending_tasks:
        items.append({
            "category": "PENDING_TASKS",
            "item_key": f"task_{task.id}",
            "description": f"Incomplete task: {task.description}",
            "is_critical": False,
        })

    return items

def initiate_handoff(db: Session, encounter_id: int, outgoing_nurse_id: int) -> HandoffSession:
    import json, hashlib
    checklist_data = generate_checklist_items(db, encounter_id)

    session = HandoffSession(
        encounter_id=encounter_id,
        outgoing_nurse_id=outgoing_nurse_id,
        status="INITIATED",
        checklist_snapshot=checklist_data,
    )
    db.add(session)
    db.flush()

    for item_data in checklist_data:
        item = HandoffChecklistItem(
            handoff_session_id=session.id,
            **item_data,
        )
        db.add(item)

    # Compute initial audit hash
    snapshot_str = json.dumps(checklist_data, sort_keys=True, default=str)
    session.audit_hash = hashlib.sha256(snapshot_str.encode()).hexdigest()

    db.commit()
    return session

def validate_and_accept_handoff(db: Session, session_id: int,
                                 incoming_nurse_id: int, signature: str) -> HandoffSession:
    session = db.query(HandoffSession).filter(HandoffSession.id == session_id).first()
    if not session:
        raise ValueError("Handoff session not found")

    # Check all critical items are resolved
    from src.modules.handoff.models import HandoffChecklistItem
    unresolved_critical = db.query(HandoffChecklistItem).filter(
        HandoffChecklistItem.handoff_session_id == session_id,
        HandoffChecklistItem.is_critical == True,
        HandoffChecklistItem.status == "PENDING",
    ).all()

    if unresolved_critical:
        raise ValueError(
            f"HANDOFF_BLOCKED: {len(unresolved_critical)} critical checklist items remain unresolved: "
            + ", ".join(i.item_key for i in unresolved_critical)
        )

    session.incoming_nurse_id = incoming_nurse_id
    session.incoming_signature = signature
    session.status = "ACCEPTED"
    session.completed_at = datetime.utcnow()

    # Update encounter's attending nurse
    from src.modules.patients.encounter_models import Encounter
    encounter = db.query(Encounter).filter(Encounter.id == session.encounter_id).first()
    if encounter:
        encounter.attending_nurse_id = incoming_nurse_id
        encounter.handoff_status = "HANDOFF_COMPLETE"

    db.commit()
    return session
```

---

## 19. FRONTEND SCREEN BLUEPRINTS

### 19.1 Medication Task Screen — `frontend/src/app/patient/[id]/medications.js`

```javascript
import React, { useState, useEffect, useCallback } from 'react';
import { View, FlatList, Alert, RefreshControl } from 'react-native';
import { Card, Text, Button, Chip, Portal, Modal } from 'react-native-paper';
import { useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../../../features/auth/AuthContext';

const STATUS_COLORS = {
  PENDING: '#FFA500',
  ADMINISTERED: '#4CAF50',
  OVERDUE: '#F44336',
  ESCALATED: '#9C27B0',
  SKIPPED: '#9E9E9E',
};

export default function MedicationsScreen() {
  const { id: encounterId } = useLocalSearchParams();
  const { token, userRole } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [confirmTask, setConfirmTask] = useState(null);  // task pending confirmation
  const [drugNameInput, setDrugNameInput] = useState(''); // for repeat-back safety check

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/v1/encounters/${encounterId}/medication-tasks`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      setTasks(data);
    } finally {
      setLoading(false);
    }
  }, [encounterId, token]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const handleAdminister = async (task) => {
    // Safety check: require nurse to type drug name before confirming
    if (drugNameInput.trim().toLowerCase() !== task.drug_name.toLowerCase()) {
      Alert.alert('Confirmation Failed',
        `Please type the exact drug name "${task.drug_name}" to confirm administration.`);
      return;
    }
    try {
      await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/v1/medication-tasks/${task.id}/administer`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: '', witness_id: null }),
        }
      );
      setConfirmTask(null);
      setDrugNameInput('');
      fetchTasks();
    } catch (err) {
      Alert.alert('Error', 'Failed to record administration. Please try again.');
    }
  };

  const isOverdue = (task) => new Date(task.due_by) < new Date() && task.status === 'PENDING';

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <FlatList
        data={tasks}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchTasks} />}
        renderItem={({ item }) => (
          <Card style={{ marginBottom: 12, borderLeftWidth: 4,
            borderLeftColor: isOverdue(item) ? STATUS_COLORS.OVERDUE : STATUS_COLORS[item.status] }}>
            <Card.Content>
              <Text variant="titleMedium">{item.drug_name} — {item.dose}</Text>
              <Text variant="bodySmall">Route: {item.route} | Scheduled: {item.scheduled_at}</Text>
              <Chip style={{ marginTop: 8, alignSelf: 'flex-start' }}
                textStyle={{ color: '#fff' }}
                style={{ backgroundColor: isOverdue(item) ? STATUS_COLORS.OVERDUE : STATUS_COLORS[item.status] }}>
                {isOverdue(item) ? 'OVERDUE' : item.status}
              </Chip>
            </Card.Content>
            {userRole === 'NURSE' && item.status === 'PENDING' && (
              <Card.Actions>
                <Button mode="contained" onPress={() => setConfirmTask(item)}>
                  Administer
                </Button>
                <Button mode="outlined" onPress={() => {/* skip flow */}}>
                  Skip
                </Button>
              </Card.Actions>
            )}
          </Card>
        )}
      />

      {/* Two-step confirmation modal */}
      <Portal>
        <Modal visible={!!confirmTask} onDismiss={() => setConfirmTask(null)}
          contentContainerStyle={{ backgroundColor: 'white', padding: 24, margin: 16, borderRadius: 8 }}>
          {confirmTask && (
            <>
              <Text variant="titleLarge" style={{ marginBottom: 8 }}>Confirm Administration</Text>
              <Text variant="bodyMedium" style={{ marginBottom: 4 }}>
                Drug: <Text style={{ fontWeight: 'bold' }}>{confirmTask.drug_name}</Text>
              </Text>
              <Text variant="bodyMedium" style={{ marginBottom: 16 }}>
                Dose: {confirmTask.dose} | Route: {confirmTask.route}
              </Text>
              <Text variant="bodySmall" style={{ marginBottom: 8, color: '#666' }}>
                Type the drug name exactly to confirm:
              </Text>
              {/* TextInput for drug name repeat-back */}
              <Button mode="contained" onPress={() => handleAdminister(confirmTask)}
                style={{ marginTop: 16 }}>
                Confirm Administration
              </Button>
              <Button onPress={() => setConfirmTask(null)} style={{ marginTop: 8 }}>
                Cancel
              </Button>
            </>
          )}
        </Modal>
      </Portal>
    </View>
  );
}
```

---

### 19.2 Handoff Checklist Screen — `frontend/src/app/patient/[id]/handoff.js`

```javascript
import React, { useState, useEffect } from 'react';
import { View, ScrollView, Alert } from 'react-native';
import { Text, Button, Card, Checkbox, Divider, Badge } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../../../../features/auth/AuthContext';

const CATEGORY_ICONS = {
  MEDICATIONS: '💊',
  VITALS: '🩺',
  LABS: '🧪',
  ALLERGIES: '⚠️',
  EMERGENCY_RISKS: '🚨',
  DOCTOR_INSTRUCTIONS: '📋',
  PENDING_TASKS: '✅',
};

export default function HandoffScreen() {
  const { id: encounterId } = useLocalSearchParams();
  const { token, userId } = useAuth();
  const router = useRouter();
  const [session, setSession] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    initHandoff();
  }, []);

  const initHandoff = async () => {
    setLoading(true);
    try {
      // Initiate handoff session
      const res = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/v1/handoff/initiate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ encounter_id: encounterId }),
      });
      const data = await res.json();
      setSession(data.session);
      setItems(data.checklist_items);
    } finally {
      setLoading(false);
    }
  };

  const verifyItem = async (itemId, status) => {
    await fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/v1/handoff/${session.id}/checklist/${itemId}`,
      {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      }
    );
    setItems(prev => prev.map(i => i.id === itemId ? { ...i, status } : i));
  };

  const criticalUnresolved = items.filter(i => i.is_critical && i.status === 'PENDING');
  const allCriticalResolved = criticalUnresolved.length === 0;

  const groupedItems = items.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
      <Text variant="headlineSmall" style={{ marginBottom: 4 }}>Shift Handoff Checklist</Text>
      {!allCriticalResolved && (
        <Card style={{ backgroundColor: '#FFEBEE', marginBottom: 16 }}>
          <Card.Content>
            <Text style={{ color: '#C62828', fontWeight: 'bold' }}>
              🚨 {criticalUnresolved.length} critical item(s) must be resolved before handoff can be accepted.
            </Text>
          </Card.Content>
        </Card>
      )}

      {Object.entries(groupedItems).map(([category, categoryItems]) => (
        <View key={category} style={{ marginBottom: 16 }}>
          <Text variant="titleMedium" style={{ marginBottom: 8 }}>
            {CATEGORY_ICONS[category] || '•'} {category.replace(/_/g, ' ')}
          </Text>
          {categoryItems.map(item => (
            <Card key={item.id} style={{ marginBottom: 8,
              borderLeftWidth: 3,
              borderLeftColor: item.is_critical ? '#F44336' : '#FF9800' }}>
              <Card.Content>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                  <Text variant="bodyMedium" style={{ flex: 1 }}>{item.description}</Text>
                  {item.is_critical && <Badge style={{ backgroundColor: '#F44336' }}>CRITICAL</Badge>}
                </View>
              </Card.Content>
              <Card.Actions>
                <Button
                  mode={item.status === 'PASSED' ? 'contained' : 'outlined'}
                  onPress={() => verifyItem(item.id, 'PASSED')}
                  style={{ marginRight: 8 }}>
                  ✓ Resolved
                </Button>
                {item.is_critical && (
                  <Button
                    mode={item.status === 'ACKNOWLEDGED_WITH_RISK' ? 'contained' : 'outlined'}
                    buttonColor={item.status === 'ACKNOWLEDGED_WITH_RISK' ? '#FF9800' : undefined}
                    onPress={() => verifyItem(item.id, 'ACKNOWLEDGED_WITH_RISK')}>
                    Acknowledge Risk
                  </Button>
                )}
              </Card.Actions>
            </Card>
          ))}
          <Divider style={{ marginTop: 8 }} />
        </View>
      ))}

      <Button
        mode="contained"
        disabled={!allCriticalResolved || submitting}
        style={{ marginTop: 16, marginBottom: 32,
          backgroundColor: allCriticalResolved ? '#4CAF50' : '#9E9E9E' }}
        onPress={() => {
          Alert.alert(
            'Complete Handoff',
            'Are you sure all items have been reviewed and communicated to the incoming nurse?',
            [
              { text: 'Cancel', style: 'cancel' },
              { text: 'Complete Handoff', onPress: () => router.push('/(tabs)/dashboard') },
            ]
          );
        }}>
        {allCriticalResolved ? 'Complete Handoff' : `${criticalUnresolved.length} Items Remaining`}
      </Button>
    </ScrollView>
  );
}
```

---

## 20. CELERY TASK DEFINITIONS

### `backend/src/tasks/celery_app.py`

```python
from celery import Celery
from celery.schedules import crontab
from src.config.config import settings

celery = Celery(
    "hvs",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,       # Only ack after successful completion
    worker_prefetch_multiplier=1,  # Prevent one worker hoarding tasks
)

celery.conf.beat_schedule = {
    # Run every 5 minutes to catch overdue medication tasks
    "medication-escalation-monitor": {
        "task": "src.tasks.medication_tasks.escalate_overdue_medications",
        "schedule": crontab(minute="*/5"),
    },
    # Run every 30 minutes to check for stalled handoff sessions
    "handoff-escalation-monitor": {
        "task": "src.tasks.handoff_tasks.escalate_stalled_handoffs",
        "schedule": crontab(minute="*/30"),
    },
    # Run daily to verify audit log hash chain integrity
    "audit-integrity-check": {
        "task": "src.tasks.audit_tasks.verify_hash_chain_integrity",
        "schedule": crontab(hour=3, minute=0),  # 3 AM UTC
    },
}
```

### `backend/src/tasks/medication_tasks.py`

```python
from datetime import datetime, timedelta
from src.tasks.celery_app import celery
from src.db.session import SessionLocal
from src.modules.medication.models import MedicationTask

@celery.task(name="src.tasks.medication_tasks.escalate_overdue_medications",
             bind=True, max_retries=3)
def escalate_overdue_medications(self):
    """
    Idempotent task: scans all PENDING medication tasks past due_by
    and escalates them with appropriate notifications.
    """
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        overdue = db.query(MedicationTask).filter(
            MedicationTask.status.in_(["PENDING"]),
            MedicationTask.due_by < now,
        ).all()

        for task in overdue:
            minutes_overdue = (now - task.due_by).total_seconds() / 60

            if minutes_overdue < 30:
                _send_escalation(db, task, level=1, priority="MEDIUM",
                    title="Medication Reminder",
                    body=f"Medication due: {task.order.drug_name}")

            elif 30 <= minutes_overdue < 60:
                if task.escalation_level < 2:
                    _send_escalation(db, task, level=2, priority="HIGH",
                        title="⚠️ Medication Overdue",
                        body=f"{task.order.drug_name} is {int(minutes_overdue)} min overdue.")

            elif 60 <= minutes_overdue < 120:
                if task.escalation_level < 3:
                    _send_escalation(db, task, level=3, priority="HIGH",
                        title="🚨 Critical: Medication Severely Overdue",
                        body=f"{task.order.drug_name} overdue by {int(minutes_overdue)} min. Doctor notified.")

            else:
                if task.escalation_level < 4:
                    _send_escalation(db, task, level=4, priority="CRITICAL",
                        title="🆘 CRITICAL MEDICATION MISS",
                        body=f"{task.order.drug_name} overdue by {int(minutes_overdue)} min. IMMEDIATE ACTION REQUIRED.")
                    task.status = "ESCALATED"

            db.commit()

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()

def _send_escalation(db, task, level, priority, title, body):
    task.escalation_level = level
    from src.modules.notifications.service import create_notification
    if task.assigned_nurse_id:
        create_notification(db, recipient_id=task.assigned_nurse_id,
            type="MED_OVERDUE", priority=priority, title=title, body=body,
            related_entity_type="medication_task", related_entity_id=task.id)
```

---

## 21. TESTING STRATEGY

### 21.1 Test Coverage Requirements

| Module | Minimum Coverage | Test Types Required |
|---|---|---|
| Auth (login, refresh, RBAC) | 90% | Unit, Integration |
| Medication order + allergy check | 95% | Unit (safety-critical) |
| Medication task escalation | 90% | Unit + Celery task tests |
| Handoff checklist generation | 95% | Unit (safety-critical) |
| Handoff acceptance validation | 95% | Unit + Integration |
| Audit log hash chain | 100% | Unit |
| WebSocket dictation | 80% | Integration |
| Notification delivery | 80% | Unit + Mock FCM |

### 21.2 Safety Scenario Tests (Must Pass Before Any Clinical Deployment)

These are written as scenario descriptions for QA engineers and clinical reviewers:

**MED-SAFETY-001:** Create a medication order for a drug that matches a patient's known allergy. System must reject with `ALLERGY_CONFLICT` error. Physician override with reason must succeed and be logged in audit trail.

**MED-SAFETY-002:** Schedule a medication at T=0. At T=31 minutes, verify escalation_level is 2 and the assigned nurse has received an `HIGH` priority notification. At T=61 minutes, verify doctor has received notification.

**MED-SAFETY-003:** Attempt to mark the same medication task as `ADMINISTERED` twice. System must reject the second call with a clear error.

**HANDOFF-SAFETY-001:** Initiate a handoff for an encounter with 2 overdue medication tasks and a DNR risk flag. Verify that all 3 items appear as `CRITICAL` in the checklist. Attempt to accept the handoff without resolving them. System must block acceptance.

**HANDOFF-SAFETY-002:** Complete all checklist items. Accept handoff. Verify `encounter.attending_nurse_id` is updated to the incoming nurse. Verify `handoff_sessions` record is `ACCEPTED` and has both digital signatures.

**HANDOFF-SAFETY-003:** Initiate a handoff. Let 35 minutes pass without acceptance. Verify supervisor receives escalation notification. Let 65 minutes pass. Verify doctor receives notification and session status is `ESCALATED`.

**AUDIT-001:** Write 10 audit log records. Corrupt record 5's `hash_chain` field directly in the DB. Run the daily integrity checker. Verify it detects and reports the corruption.

**AUTH-001:** Attempt to register a new `ADMIN` account without providing a valid `ADMIN` JWT. Verify 403 is returned.

### 21.3 Backend Test Setup

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.db.base_class import Base
from src.db.session import get_db

TEST_DATABASE_URL = "postgresql://test_user:test@localhost:5432/hvs_test"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()   # rollback after each test — no persistent state
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def nurse_token(client):
    # Create a nurse and return their JWT
    client.post("/api/v1/auth/register", json={
        "username": "nurse_test", "password": "Test1234!", "role": "NURSE"
    })
    res = client.post("/api/v1/auth/token",
        data={"username": "nurse_test", "password": "Test1234!"})
    return res.json()["access_token"]
```

---

## 22. DEVELOPER HANDOVER NOTES

### 22.1 Where to Start (First Day Checklist)

1. Clone the repository and confirm both `backend` and `frontend` directories are present.
2. Copy `backend/.env.example` to `backend/.env` and fill in `DATABASE_URL`, `JWT_SECRET_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`.
3. Copy `frontend/.env.example` to `frontend/.env.development` and set `EXPO_PUBLIC_API_URL`.
4. Run Alembic: `alembic upgrade head` — confirm the three existing migrations apply cleanly.
5. Run `create_admin.py` to seed the initial admin account.
6. Start the backend: `uvicorn src.main:app --reload`.
7. Start the frontend: `npx expo start`.
8. Attempt login — confirm JWT is returned and dashboard loads.
9. Confirm the WebSocket dictation is still broken (it should be, until Phase 0 fix is applied). Document the error.
10. Apply Phase 0 fixes in order. Re-test dictation.

### 22.2 Critical Files — Do Not Modify Without Peer Review

| File | Reason |
|---|---|
| `alembic/versions/*.py` (all existing) | Applied to production schema. Any change risks data loss. |
| `backend/src/config/security.py` | JWT signing. Change breaks all active sessions. |
| `backend/src/modules/auth/models.py` | User table. Schema changes require migration. |
| `backend/src/modules/audit/service.py` (once created) | Hash chain integrity. Any bug invalidates audit trail. |
| `frontend/src/features/auth/AuthContext.js` | Token storage and session management. Bugs log out all users. |

### 22.3 Known Technical Debt (Do Not Ignore)

| Debt Item | Impact if Ignored | Resolution Phase |
|---|---|---|
| `Patient.id` as String PK | Performance degradation at scale | Phase 4 (with full migration plan) |
| In-memory WS connection manager | Breaks on multi-worker deployment | Phase 4 |
| `legacy_api.js` as single file | Unmaintainable, impossible to test | Phase 4 (incremental replacement) |
| No DB connection pool config | Potential pool exhaustion under load | Phase 1 |
| Async DB session in WebSocket handler | Memory leak on crash | Phase 0 (low-hanging fix) |

### 22.4 Dependency Management

**Backend — packages to add for new features:**
```
# Add to requirements.txt
celery[redis]==5.3.6
redis==5.0.1
cryptography==42.0.5        # for PHI encryption
firebase-admin==6.4.0       # for FCM push notifications
python-jose[cryptography]   # if not already present for JWT
```

**Frontend — packages to verify are installed:**
```
react-native-live-audio-stream   # must be properly linked for iOS/Android
@react-native-firebase/app       # FCM
@react-native-firebase/messaging # FCM
expo-local-authentication        # biometric for digital signature
```

### 22.5 Environment-Specific Behavior

| Behavior | Development | Production |
|---|---|---|
| CORS | Allow `localhost:8081` | Allow `app.hvs.hospital` only |
| JWT expiry | 120 minutes | 30 minutes |
| Audio WS protocol | `ws://` | `wss://` |
| API protocol | `http://` | `https://` |
| DB pool size | 5 connections | 20 connections |
| Celery workers | 1 | 4+ |
| FCM delivery | Mock/disabled | Live |

---

## 23. NOTIFICATION SERVICE — FULL IMPLEMENTATION

### 23.1 SQLAlchemy Model — `backend/src/modules/notifications/models.py`

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.db.base_class import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id                  = Column(Integer, primary_key=True, index=True)
    recipient_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_id           = Column(Integer, ForeignKey("users.id"), nullable=True)
    type                = Column(String(100), nullable=False)
    priority            = Column(String(20), default="MEDIUM", nullable=False)
    title               = Column(String(200), nullable=False)
    body                = Column(Text, nullable=False)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id   = Column(Integer, nullable=True)
    is_read             = Column(Boolean, default=False, nullable=False)
    is_delivered        = Column(Boolean, default=False, nullable=False)
    push_sent_at        = Column(DateTime, nullable=True)
    read_at             = Column(DateTime, nullable=True)
    expires_at          = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow, nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_id], backref="notifications")
    sender    = relationship("User", foreign_keys=[sender_id])
```

### 23.2 Schemas — `backend/src/modules/notifications/schemas.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationOut(BaseModel):
    id:                   int
    type:                 str
    priority:             str
    title:                str
    body:                 str
    related_entity_type:  Optional[str]
    related_entity_id:    Optional[int]
    is_read:              bool
    created_at:           datetime

    class Config:
        from_attributes = True

class NotificationListOut(BaseModel):
    items:        list[NotificationOut]
    total:        int
    unread_count: int
```

### 23.3 Service — `backend/src/modules/notifications/service.py`

```python
"""
Notification delivery service.
Handles: DB persistence → WebSocket push → FCM push.
All three are attempted independently; failure of one does not block others.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from src.modules.notifications.models import Notification

log = logging.getLogger(__name__)

# Priority → FCM Android notification priority mapping
FCM_PRIORITY_MAP = {
    "LOW":      "normal",
    "MEDIUM":   "normal",
    "HIGH":     "high",
    "CRITICAL": "high",
}

def create_notification(
    db: Session,
    recipient_id: int,
    type: str,
    priority: str,
    title: str,
    body: str,
    sender_id: int = None,
    related_entity_type: str = None,
    related_entity_id: int = None,
) -> Notification:
    notif = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=type,
        priority=priority,
        title=title,
        body=body,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Attempt WebSocket in-app push (non-blocking)
    try:
        _push_via_websocket(recipient_id, notif)
    except Exception as e:
        log.warning(f"[Notification] WS push failed for user {recipient_id}: {e}")

    # Attempt FCM push (non-blocking)
    try:
        _push_via_fcm(db, recipient_id, notif)
    except Exception as e:
        log.warning(f"[Notification] FCM push failed for user {recipient_id}: {e}")

    return notif

def _push_via_websocket(recipient_id: int, notif: Notification):
    """Push notification to any active WS /ws/alerts sessions for this user."""
    from src.websocket.connection_manager import manager
    import asyncio, json
    payload = json.dumps({
        "event": "NOTIFICATION",
        "data": {
            "id":       notif.id,
            "type":     notif.type,
            "priority": notif.priority,
            "title":    notif.title,
            "body":     notif.body,
        }
    })
    # Run coroutine in a thread-safe way if called from Celery (sync context)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.send_to_user(recipient_id, payload))
    except RuntimeError:
        # No running event loop (called from Celery worker)
        asyncio.run(manager.send_to_user(recipient_id, payload))

def _push_via_fcm(db: Session, recipient_id: int, notif: Notification):
    """Send FCM push notification to the user's registered device token."""
    from src.modules.auth.models import User
    user = db.query(User).filter(User.id == recipient_id).first()
    if not user or not user.device_token:
        return

    import firebase_admin
    from firebase_admin import messaging

    # firebase_admin app is initialized at startup in main.py
    message = messaging.Message(
        notification=messaging.Notification(
            title=notif.title,
            body=notif.body,
        ),
        android=messaging.AndroidConfig(
            priority=FCM_PRIORITY_MAP.get(notif.priority, "normal"),
            notification=messaging.AndroidNotification(
                sound="default" if notif.priority in ("HIGH", "CRITICAL") else None,
                channel_id="hvs_alerts",
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default" if notif.priority in ("HIGH", "CRITICAL") else None,
                    badge=1,
                )
            )
        ),
        token=user.device_token,
        data={
            "notification_id":    str(notif.id),
            "type":               notif.type,
            "priority":           notif.priority,
            "related_entity_type": notif.related_entity_type or "",
            "related_entity_id":   str(notif.related_entity_id or ""),
        }
    )
    response = messaging.send(message)
    log.info(f"[FCM] Sent to user {recipient_id}: {response}")
    notif.push_sent_at = datetime.utcnow()
    notif.is_delivered = True
    db.commit()

def mark_read(db: Session, notification_id: int, user_id: int) -> Notification:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == user_id,
    ).first()
    if not notif:
        return None
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.commit()
    return notif

def get_notifications(db: Session, user_id: int, page: int = 1,
                      limit: int = 20) -> dict:
    query = db.query(Notification).filter(
        Notification.recipient_id == user_id
    ).order_by(Notification.created_at.desc())
    total = query.count()
    unread = query.filter(Notification.is_read == False).count()
    items  = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": items, "total": total, "unread_count": unread}
```

### 23.4 Router — `backend/src/modules/notifications/router.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, get_db
from src.modules.notifications import service
from src.modules.notifications.schemas import NotificationOut, NotificationListOut

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("", response_model=NotificationListOut)
def list_notifications(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return service.get_notifications(db, current_user.id, page, limit)

@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    count = db.query(service.Notification).filter(
        service.Notification.recipient_id == current_user.id,
        service.Notification.is_read == False,
    ).count()
    return {"unread_count": count}

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    notif = service.mark_read(db, notification_id, current_user.id)
    if not notif:
        from fastapi import HTTPException
        raise HTTPException(404, "Notification not found")
    return notif

@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    db.query(service.Notification).filter(
        service.Notification.recipient_id == current_user.id,
        service.Notification.is_read == False,
    ).update({"is_read": True, "read_at": service.datetime.utcnow()})
    db.commit()
    return {"status": "ok"}
```

### 23.5 Firebase Initialization — add to `backend/src/main.py`

```python
# Add near the top of main.py, after imports
import firebase_admin
from firebase_admin import credentials
from src.config.config import settings

# Initialize Firebase Admin SDK (idempotent — safe to call on restart)
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
```

---

## 24. PHI ENCRYPTION MODULE

### 24.1 Purpose

Encrypts personally identifiable and clinically sensitive fields before they reach the database. Decrypts transparently on read. Applied to: `known_allergies`, `risk_flags`, clinical note content, vitals readings.

**This module is Phase 4 only.** Do not apply it to existing tables before a complete data migration is scripted and tested.

### 24.2 Encryption Utility — `backend/src/config/encryption.py`

```python
"""
AES-256-GCM field-level encryption for PHI.
Key is derived from settings.PHI_ENCRYPTION_KEY (32-byte hex string from env).
Each encrypted value is self-contained: base64(nonce + ciphertext + tag).
"""
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.config.config import settings

def _get_key() -> bytes:
    key_hex = settings.PHI_ENCRYPTION_KEY
    if not key_hex or len(bytes.fromhex(key_hex)) != 32:
        raise ValueError("PHI_ENCRYPTION_KEY must be a 64-character hex string (32 bytes).")
    return bytes.fromhex(key_hex)

def encrypt_phi(plaintext: str) -> str:
    """
    Encrypts a string and returns a base64-encoded ciphertext blob.
    Format: base64(12-byte nonce || ciphertext || 16-byte GCM tag)
    """
    if not plaintext:
        return plaintext
    key   = _get_key()
    aesgcm = AESGCM(key)
    nonce  = os.urandom(12)   # 96-bit nonce, unique per encryption
    ct     = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")

def decrypt_phi(ciphertext_b64: str) -> str:
    """Decrypts a base64-encoded ciphertext blob back to plaintext."""
    if not ciphertext_b64:
        return ciphertext_b64
    key   = _get_key()
    aesgcm = AESGCM(key)
    raw    = base64.b64decode(ciphertext_b64)
    nonce  = raw[:12]
    ct     = raw[12:]
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")

def encrypt_list(items: list[str]) -> list[str]:
    return [encrypt_phi(i) for i in (items or [])]

def decrypt_list(items: list[str]) -> list[str]:
    return [decrypt_phi(i) for i in (items or [])]
```

### 24.3 Usage Pattern in Services

```python
# When writing a patient's allergies to DB
from src.config.encryption import encrypt_list, decrypt_list

# Write (encrypt before DB)
patient.known_allergies = encrypt_list(incoming_allergies)

# Read (decrypt after DB fetch)
readable_allergies = decrypt_list(patient.known_allergies)
```

### 24.4 Key Rotation Strategy

When `PHI_ENCRYPTION_KEY` must be rotated (e.g., suspected compromise):

1. Set `PHI_ENCRYPTION_KEY_OLD` = current key in environment.
2. Set `PHI_ENCRYPTION_KEY` = new key.
3. Run a one-time migration script that reads each encrypted field with `KEY_OLD`, decrypts, re-encrypts with `KEY_NEW`, and writes back.
4. Remove `PHI_ENCRYPTION_KEY_OLD` from environment after migration completes.
5. Log key rotation event in audit trail with timestamp and actor.

**⚠️ Never store the plaintext key in source control. Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager) in production.**

---

## 25. REDIS-BACKED WEBSOCKET CONNECTION MANAGER

### 25.1 Why This Is Needed

The existing `connection_manager.py` stores active WebSocket connections in a Python dictionary in memory. This works for a single Uvicorn process but silently breaks when running multiple workers (e.g., `uvicorn --workers 4`): a user connected to Worker 1 will never receive a message broadcast from Worker 2.

**This is a Phase 4 change.** Do not attempt it until the system is stable on a single worker.

### 25.2 Updated `backend/src/websocket/connection_manager.py`

```python
"""
Redis pub/sub-backed WebSocket connection manager.
Supports multi-worker Uvicorn deployments.

Architecture:
  - Each WS connection is registered locally (in-process dict).
  - Broadcasts are published to a Redis channel.
  - Every worker subscribes to the Redis channel and forwards to local connections.
"""
import asyncio, json, logging
from typing import Dict, Set
from fastapi import WebSocket
import redis.asyncio as aioredis
from src.config.config import settings

log = logging.getLogger(__name__)

REDIS_CHANNEL = "hvs:ws:broadcast"

class ConnectionManager:
    def __init__(self):
        # local registry: user_id → set of WebSocket objects on THIS worker
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._redis: aioredis.Redis | None = None
        self._pubsub = None

    async def startup(self):
        """Call once at application startup."""
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(REDIS_CHANNEL)
        asyncio.create_task(self._listen())
        log.info("[WS Manager] Redis pub/sub listener started.")

    async def shutdown(self):
        if self._pubsub:
            await self._pubsub.unsubscribe(REDIS_CHANNEL)
        if self._redis:
            await self._redis.aclose()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        log.info(f"[WS] User {user_id} connected. Active: {len(self._connections[user_id])}")

    async def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: int, message: str):
        """
        Send to a specific user. Publishes to Redis so ALL workers attempt delivery.
        """
        if self._redis:
            await self._redis.publish(REDIS_CHANNEL, json.dumps({
                "target": "user",
                "user_id": user_id,
                "message": message,
            }))

    async def broadcast_to_ward(self, ward: str, message: str):
        """Broadcast to all users in a specific ward."""
        if self._redis:
            await self._redis.publish(REDIS_CHANNEL, json.dumps({
                "target": "ward",
                "ward": ward,
                "message": message,
            }))

    async def _listen(self):
        """Background task: consumes Redis pub/sub and delivers to local connections."""
        async for raw in self._pubsub.listen():
            if raw["type"] != "message":
                continue
            try:
                envelope = json.loads(raw["data"])
                if envelope["target"] == "user":
                    await self._deliver_to_user(
                        envelope["user_id"], envelope["message"]
                    )
                elif envelope["target"] == "ward":
                    await self._deliver_to_ward(
                        envelope["ward"], envelope["message"]
                    )
            except Exception as e:
                log.error(f"[WS Manager] Listener error: {e}")

    async def _deliver_to_user(self, user_id: int, message: str):
        sockets = self._connections.get(user_id, set()).copy()
        dead = set()
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)

    async def _deliver_to_ward(self, ward: str, message: str):
        # Requires ward→user_id lookup; simplified here
        # In production, maintain a ward→user_id mapping in Redis
        pass

manager = ConnectionManager()
```

### 25.3 Register Lifecycle Events in `main.py`

```python
from src.websocket.connection_manager import manager

@app.on_event("startup")
async def on_startup():
    await manager.startup()

@app.on_event("shutdown")
async def on_shutdown():
    await manager.shutdown()
```

### 25.4 Real-time Alerts WebSocket Endpoint

```python
# backend/src/modules/notifications/ws_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.config.security import decode_access_token
from src.websocket.connection_manager import manager

router = APIRouter()

@router.websocket("/ws/alerts")
async def alerts_ws(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    user_id = payload.get("user_id")
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep alive — client may send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
```

---

## 26. REPLACEMENT API CLIENT — `frontend/src/services/api.js`

This replaces `legacy_api.js` incrementally. Import from this file in all new screens. Old screens continue using `legacy_api.js` until migrated one by one.

```javascript
/**
 * api.js — Unified API client for HVS-APP
 *
 * Replaces legacy_api.js. Uses EXPO_PUBLIC_API_URL from environment.
 * Handles: JWT attachment, token refresh, error normalisation.
 *
 * Usage:
 *   import api from '../services/api';
 *   const patient = await api.get('/patients/search/?name=John');
 *   await api.post('/encounters/', { patient_id: '...' });
 */

const BASE_URL = process.env.EXPO_PUBLIC_API_URL
  ? `https://${process.env.EXPO_PUBLIC_API_URL}`
  : 'http://localhost:8000';

const WS_BASE_URL = process.env.EXPO_PUBLIC_API_URL
  ? `wss://${process.env.EXPO_PUBLIC_API_URL}`
  : 'ws://localhost:8000';

// Token storage (replace with SecureStore in production)
let _accessToken  = null;
let _refreshToken = null;

export const setTokens = (access, refresh) => {
  _accessToken  = access;
  _refreshToken = refresh;
};

export const clearTokens = () => {
  _accessToken  = null;
  _refreshToken = null;
};

// ─── Core fetch wrapper ────────────────────────────────────────────────────

async function request(method, path, body = null, retry = true) {
  const headers = {
    'Content-Type': 'application/json',
    ..._accessToken ? { Authorization: `Bearer ${_accessToken}` } : {},
  };

  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Auto-refresh on 401
  if (res.status === 401 && retry && _refreshToken) {
    const refreshed = await _attemptRefresh();
    if (refreshed) {
      return request(method, path, body, false);  // retry once
    }
    throw new ApiError(401, 'Session expired. Please log in again.');
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(res.status, data.detail || 'An error occurred.', data);
  }

  return data;
}

async function _attemptRefresh() {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: _refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    _accessToken  = data.access_token;
    _refreshToken = data.refresh_token;
    return true;
  } catch {
    return false;
  }
}

export class ApiError extends Error {
  constructor(status, message, detail = null) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

// ─── HTTP convenience methods ──────────────────────────────────────────────

const api = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  put:    (path, body)   => request('PUT',    path, body),
  patch:  (path, body)   => request('PATCH',  path, body),
  delete: (path)         => request('DELETE', path),
};

export default api;

// ─── Auth helpers ──────────────────────────────────────────────────────────

export const login = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${BASE_URL}/api/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail || 'Login failed.');
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
};

export const logout = async () => {
  try {
    await api.post('/auth/logout', { refresh_token: _refreshToken });
  } finally {
    clearTokens();
  }
};

export const registerDeviceToken = async (deviceToken) => {
  return api.put('/auth/device-token', { device_token: deviceToken });
};

// ─── WebSocket factory ─────────────────────────────────────────────────────

export const createWebSocket = (path) => {
  if (!_accessToken) throw new Error('Not authenticated.');
  const sep = path.includes('?') ? '&' : '?';
  return new WebSocket(`${WS_BASE_URL}${path}${sep}token=${_accessToken}`);
};

export const createAlertsSocket = (handlers = {}) => {
  const ws = createWebSocket('/ws/alerts');

  ws.onopen    = ()      => { handlers.onOpen?.();  };
  ws.onclose   = (e)     => { handlers.onClose?.(e); };
  ws.onerror   = (e)     => { handlers.onError?.(e); };
  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.event === 'NOTIFICATION') {
        handlers.onNotification?.(payload.data);
      }
    } catch { /* ignore malformed frames */ }
  };

  // Heartbeat: send ping every 30s to prevent proxy timeout
  const heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send('ping');
  }, 30000);

  ws.addEventListener('close', () => clearInterval(heartbeat));
  return ws;
};
```

---

## 27. EXTENDED AUTH CONTEXT — `frontend/src/features/auth/AuthContext.js`

```javascript
/**
 * AuthContext.js — Extended with:
 *  - Refresh token support
 *  - FCM device token registration
 *  - Role-based permission helper
 *  - Real-time alerts WebSocket lifecycle
 */
import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import * as SecureStore from 'expo-secure-store';
import { login as apiLogin, logout as apiLogout,
         setTokens, clearTokens, registerDeviceToken,
         createAlertsSocket } from '../services/api';

const AuthContext = createContext(null);

// ─── Permission matrix ─────────────────────────────────────────────────────
const PERMISSIONS = {
  ADMIN:        ['view_patients', 'manage_users', 'view_audit_logs',
                 'view_all_encounters', 'administer_medication'],
  DOCTOR:       ['view_patients', 'create_medication_order', 'view_all_encounters',
                 'create_encounter', 'update_encounter', 'override_allergy'],
  NURSE:        ['view_patients', 'view_own_encounter', 'administer_medication',
                 'record_vitals', 'initiate_handoff', 'accept_handoff',
                 'update_task'],
  RECEPTIONIST: ['view_patients', 'create_patient', 'create_encounter'],
  LAB_TECHNICIAN: ['update_lab_status'],
  PHARMACIST:   ['view_medication_orders', 'override_allergy'],
};

export function AuthProvider({ children }) {
  const [user, setUser]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const alertsWs                = useRef(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount]     = useState(0);

  // Restore session on app launch
  useEffect(() => {
    (async () => {
      try {
        const stored = await SecureStore.getItemAsync('hvs_auth');
        if (stored) {
          const { user: u, accessToken, refreshToken } = JSON.parse(stored);
          setTokens(accessToken, refreshToken);
          setUser(u);
          _connectAlertsSocket(u.id);
        }
      } catch { /* corrupted storage — force re-login */ }
      finally { setLoading(false); }
    })();
    return () => alertsWs.current?.close();
  }, []);

  const _connectAlertsSocket = (userId) => {
    if (alertsWs.current) alertsWs.current.close();
    const ws = createAlertsSocket({
      onNotification: (notif) => {
        setNotifications(prev => [notif, ...prev]);
        setUnreadCount(prev => prev + 1);
      },
      onClose: (e) => {
        // Reconnect after 5 seconds unless intentional close
        if (e.code !== 1000) {
          setTimeout(() => _connectAlertsSocket(userId), 5000);
        }
      },
    });
    alertsWs.current = ws;
  };

  const signIn = async (username, password) => {
    const data = await apiLogin(username, password);
    const userData = {
      id:       data.user_id,
      username: data.username,
      role:     data.role,
    };
    await SecureStore.setItemAsync('hvs_auth', JSON.stringify({
      user:         userData,
      accessToken:  data.access_token,
      refreshToken: data.refresh_token,
    }));
    setUser(userData);
    _connectAlertsSocket(userData.id);

    // Register FCM token if available
    try {
      const { getToken } = await import('@react-native-firebase/messaging');
      const fcmToken = await getToken();
      if (fcmToken) await registerDeviceToken(fcmToken);
    } catch { /* FCM optional */ }

    return userData;
  };

  const signOut = async () => {
    alertsWs.current?.close(1000, 'User logged out');
    await apiLogout().catch(() => {});
    await SecureStore.deleteItemAsync('hvs_auth');
    clearTokens();
    setUser(null);
    setNotifications([]);
    setUnreadCount(0);
  };

  /**
   * Check if the current user has a specific permission.
   * Usage: can('administer_medication')
   */
  const can = (permission) => {
    if (!user?.role) return false;
    return PERMISSIONS[user.role]?.includes(permission) ?? false;
  };

  const markNotificationRead = (notifId) => {
    setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true } : n));
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      signIn,
      signOut,
      can,
      notifications,
      unreadCount,
      markNotificationRead,
      isAuthenticated: !!user,
      userId:   user?.id,
      userRole: user?.role,
      token:    null,   // tokens are managed internally by api.js; don't expose
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
```

---

## 28. DATABASE CONNECTION POOL HARDENING

### 28.1 Updated `backend/src/db/session.py`

```python
"""
Database session with properly configured connection pool.
Prevents pool exhaustion under concurrent WebSocket + Celery load.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.config.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,            # Steady-state connections kept open
    max_overflow=20,         # Burst connections allowed above pool_size
    pool_timeout=30,         # Seconds to wait for a connection before raising
    pool_recycle=1800,       # Recycle connections every 30 min (prevents stale TCP)
    pool_pre_ping=True,      # Test connection health before use (handles DB restarts)
    echo=False,              # Set True only for debugging — very verbose
)

# Enforce connection timeout at the PostgreSQL level
@event.listens_for(engine, "connect")
def set_pg_timeout(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET statement_timeout = '30s'")  # kill runaway queries
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 28.2 WebSocket DB Session Fix

The existing `process_dictation_and_save_note` opens a raw `SessionLocal()` inside an async function. If the coroutine raises before `finally`, the session leaks. Fix with a context manager:

```python
# In backend/src/modules/transcription/service.py
# Replace the manual SessionLocal() pattern with:

from contextlib import contextmanager
from src.db.session import SessionLocal

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Usage inside process_dictation_and_save_note:
async def _save_note_thread(encounter_id, transcript, authored_by):
    with get_db_session() as db:
        note = ClinicalNote(
            encounter_id=encounter_id,
            content=transcript,
            authored_by=authored_by,
        )
        db.add(note)
        # commit happens in context manager __exit__
```

---

## 29. DOCKER AND DEPLOYMENT CONFIGURATION

### 29.1 `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user for security
RUN useradd -m hvs && chown -R hvs:hvs /app
USER hvs

EXPOSE 8000

CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info"]
```

### 29.2 `docker-compose.yml` (Development)

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER:     hvs_user
      POSTGRES_PASSWORD: hvs_dev_pass
      POSTGRES_DB:       hvs_db
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "hvs_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes   # persistence enabled
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  backend:
    build: ./backend
    env_file: ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app          # hot-reload in dev only
    command: >
      uvicorn src.main:app
      --host 0.0.0.0
      --port 8000
      --reload

  celery_worker:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      - redis
      - db
    command: >
      celery -A src.tasks.celery_app.celery worker
      --loglevel=info
      --concurrency=4

  celery_beat:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      - redis
      - db
    command: >
      celery -A src.tasks.celery_app.celery beat
      --loglevel=info
      --scheduler celery.beat.PersistentScheduler

volumes:
  pg_data:
  redis_data:
```

### 29.3 `backend/.env.example`

```bash
# Database
DATABASE_URL=postgresql://hvs_user:hvs_dev_pass@db:5432/hvs_db

# JWT
JWT_SECRET_KEY=change_me_to_a_64_char_hex_random_string_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Cloud Speech
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-speech.json

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# Firebase
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-adminsdk.json

# PHI Encryption (32-byte hex = 64 chars)
PHI_ENCRYPTION_KEY=0000000000000000000000000000000000000000000000000000000000000000

# CORS
CORS_ALLOWED_ORIGINS=["http://localhost:8081","http://localhost:19006"]
```

### 29.4 Nginx Configuration (Production)

```nginx
# /etc/nginx/sites-available/hvs

upstream backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 443 ssl http2;
    server_name api.hvs.hospital;

    ssl_certificate     /etc/ssl/hvs/fullchain.pem;
    ssl_certificate_key /etc/ssl/hvs/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m  rate=100r/m;

    # REST API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass         http://backend;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # Auth endpoints — stricter rate limit
    location /api/v1/auth/token {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://backend;
    }

    # WebSocket — disable buffering and increase timeouts
    location /ws/ {
        proxy_pass         http://backend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_read_timeout 3600s;   # 1 hour for long dictation sessions
        proxy_send_timeout 3600s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.hvs.hospital;
    return 301 https://$host$request_uri;
}
```

---

## 30. CLINICAL SIGN-OFF CHECKLIST

This checklist must be completed by a senior clinician (registered nurse or physician) and a senior engineer before any patient data is ever entered into the system. It is not optional. Print and physically sign.

---

### SECTION A — Clinical Safety Review

| # | Requirement | Verified By | Date |
|---|---|---|---|
| A1 | The handoff checklist correctly surfaces ALL overdue medications | | |
| A2 | The handoff cannot be accepted with unacknowledged DNR flags | | |
| A3 | Medication allergy cross-check blocks conflicting orders | | |
| A4 | Physician override of allergy block requires written reason and is logged | | |
| A5 | The two-step medication administration confirmation is present in the UI | | |
| A6 | Controlled substances require witness ID before task closure | | |
| A7 | Patient identity (name, DOB, bed) is displayed on medication admin screen | | |
| A8 | Escalation chain for overdue medications reaches the attending doctor within 2 hours | | |
| A9 | A nurse cannot accept a handoff for a patient not in their ward | | |
| A10 | Digital signatures are stored and cannot be modified post-acceptance | | |

---

### SECTION B — Security Review

| # | Requirement | Verified By | Date |
|---|---|---|---|
| B1 | All API endpoints require authentication except `/auth/token` and `/auth/register` | | |
| B2 | ADMIN accounts can only be created by an existing ADMIN | | |
| B3 | JWT access tokens expire in ≤ 30 minutes in production | | |
| B4 | HTTPS is enforced on all API traffic | | |
| B5 | PHI fields are encrypted at rest | | |
| B6 | Audit log hash chain integrity check passes | | |
| B7 | CORS is restricted to the known app origin | | |
| B8 | Rate limiting on auth endpoints is active | | |
| B9 | Patient data is not present in application logs | | |
| B10 | Penetration test completed with no high/critical findings unresolved | | |

---

### SECTION C — Infrastructure Review

| # | Requirement | Verified By | Date |
|---|---|---|---|
| C1 | Staging environment confirmed as schema-identical to production | | |
| C2 | DB backup tested: restore completed successfully in < 1 hour | | |
| C3 | Celery Beat monitoring alert configured (fires if scheduler silent > 5 min) | | |
| C4 | DB connection pool exhaustion test passed (100 concurrent users) | | |
| C5 | WebSocket reconnection tested (server restart while client connected) | | |
| C6 | Alembic `downgrade` tested for every migration applied to staging | | |
| C7 | Redis persistence (`appendonly yes`) confirmed active | | |
| C8 | Firebase credentials stored in secrets manager, not in codebase | | |
| C9 | `PHI_ENCRYPTION_KEY` stored in secrets manager, not in codebase | | |
| C10 | Health check endpoint returns `200 OK` with all subsystems healthy | | |

---

### SECTION D — Regulatory Acknowledgements

| # | Statement | Acknowledged By | Date |
|---|---|---|---|
| D1 | This system has been reviewed for compliance with applicable local health data regulations (HIPAA / DISHA / equivalent) | | |
| D2 | Audit logs are retained for a minimum of [N] years per local regulation | | |
| D3 | A Data Processing Agreement (DPA) is in place with all third-party vendors (Google Cloud, Firebase) | | |
| D4 | Staff have received training on this system before live use | | |
| D5 | An incident response plan exists for data breach scenarios | | |

---

**Sign-off:**

| Role | Name | Signature | Date |
|---|---|---|---|
| Lead Engineer | | | |
| Senior Nurse / Clinical Lead | | | |
| Information Security Officer | | | |
| Project Owner | | | |

---

*End of Implementation Plan — Version 1.0 (Complete)*

*Document length: 30 sections.*  
*Revision history must be maintained in the repository alongside this file.*  
*Next mandatory review: after Phase 0 completion and after Phase 3 clinical walkthrough.*  
*This document is a living specification — update section versions on each revision.*


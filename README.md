# 🏥 HVS-App — Hospital Handoff Validation System

> **⚠️ SAFETY-CRITICAL HEALTHCARE SYSTEM**
> This application is designed for clinical use. Every feature prioritises **patient safety over development velocity**. No feature should be deployed without passing the clinical validation checkpoints defined in the implementation plan.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Features](#features)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running with Docker](#running-with-docker)
- [Development Roadmap](#development-roadmap)
- [Known Issues & Bugs](#known-issues--bugs)
- [Security Model](#security-model)
- [Safety Mechanisms](#safety-mechanisms)
- [Clinical Sign-Off Requirements](#clinical-sign-off-requirements)
- [Contributing](#contributing)

---

## Overview

**HVS-App** is a safety-critical mobile + backend system designed to streamline and validate nurse-to-nurse **clinical handoffs** in hospital settings. It ensures that when a nurse ends their shift, the incoming nurse cannot assume care of a patient without explicitly acknowledging every critical checklist item — including pending medications, outstanding lab results, allergy flags, vitals, and doctor instructions.

The system combines:
- Real-time **voice dictation** for clinical notes (ASR via Google Cloud Speech)
- A **medication task engine** with automated escalation
- A **structured handoff validation workflow** with digital signatures
- **Smart push notifications** for critical clinical alerts
- A tamper-proof **audit trail** for regulatory compliance

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Mobile Frontend** | React Native (Expo) |
| **Frontend UI** | React Native Paper |
| **Frontend Routing** | Expo Router (file-based) |
| **Backend** | Python 3, FastAPI, Uvicorn |
| **Database** | PostgreSQL via SQLAlchemy ORM |
| **Migrations** | Alembic |
| **Authentication** | OAuth2 + JWT Bearer Tokens |
| **ASR (Voice Dictation)** | Google Cloud Speech-to-Text (`medical_dictation` model) |
| **Real-time Communication** | WebSockets (FastAPI native) |
| **Task Queue** | Celery + Redis |
| **Push Notifications** | Firebase Cloud Messaging (FCM) |
| **State Management** | React Context API |
| **Containerisation** | Docker + Docker Compose |
| **Reverse Proxy** | Nginx (production) |

---

## Repository Structure

```
HVSapp/
├── backend/
│   ├── alembic/                    # Database migration versions
│   ├── src/
│   │   ├── config/
│   │   │   ├── config.py           # App settings (env vars, URLs)
│   │   │   └── security.py         # JWT issuance, bcrypt, refresh tokens
│   │   ├── db/
│   │   │   ├── base_class.py       # SQLAlchemy base
│   │   │   └── session.py          # DB connection pool
│   │   ├── middleware/
│   │   │   ├── audit_middleware.py # Logs all state-changing requests
│   │   │   └── rate_limit.py       # Auth endpoint rate limiting
│   │   ├── modules/
│   │   │   ├── auth/               # Login, registration, JWT
│   │   │   ├── patients/           # Patient records, encounters, notes
│   │   │   ├── transcription/      # WebSocket ASR dictation
│   │   │   ├── medication/         # Medication orders + task engine
│   │   │   ├── handoff/            # Handoff sessions + checklist
│   │   │   ├── notifications/      # Push + in-app notification engine
│   │   │   ├── validation/         # Clinical safety rule engine
│   │   │   └── audit/              # Tamper-proof audit logs
│   │   ├── tasks/
│   │   │   └── celery_app.py       # Celery async task queue
│   │   └── main.py                 # FastAPI app entrypoint
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   └── login.js        # Login screen
│   │   │   ├── (tabs)/
│   │   │   │   ├── dashboard.js    # Role-aware dashboard
│   │   │   │   ├── patients.js     # Patient list
│   │   │   │   ├── handoff/        # Handoff screens
│   │   │   │   └── notifications.js
│   │   │   └── patient/[id]/
│   │   │       ├── dictation.js    # Voice dictation screen
│   │   │       ├── medications.js  # Medication task view
│   │   │       ├── vitals.js       # Vitals recording
│   │   │       ├── handoff.js      # Initiate/accept handoff
│   │   │       ├── history.js
│   │   │       ├── notes.js
│   │   │       └── tasks.js
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   └── AuthContext.js  # JWT context + role permissions
│   │   │   ├── handoff/
│   │   │   │   ├── audioStream.js  # Native audio streaming
│   │   │   │   └── HandoffContext.js
│   │   │   ├── medications/
│   │   │   ├── notifications/      # FCM integration
│   │   │   └── validation/         # Client-side safety checks
│   │   └── services/
│   │       ├── api.js              # Environment-based API client
│   │       ├── websocket.js        # Unified WebSocket manager
│   │       └── legacy_api.js       # Deprecated — migration in progress
│   ├── app.json
│   └── package.json
│
└── .gitignore
```

---

## Features

### ✅ Currently Working

- User login with JWT authentication
- Role-based routing (Doctor / Nurse / Admin)
- Patient registration and search
- Encounter creation and lifecycle state transitions (`PENDING_TRIAGE → ACTIVE → DISCHARGED`)
- Lab status update endpoints
- Critical alerts aggregation endpoint
- Clinical note model + save on dictation end (backend)
- WebSocket connection management (in-memory)
- Google ASR backend integration (streaming generator)

### ⚠️ Partially Implemented

| Feature | Status | Blocker |
|---|---|---|
| Live voice dictation (ASR) | Backend ready; frontend broken | WebSocket auth mismatch + missing audio streaming wiring |
| Medication module | DB schema exists; service stub only | No router, no scheduler, no task engine |
| Handoff validation | Service stub only | No logic, no models |
| Audit logging | Directory exists | Completely unimplemented |

### 🔜 Planned (Not Yet Implemented)

| Feature | Priority |
|---|---|
| Handoff validation workflow | CRITICAL |
| Medication task scheduler (Celery) | CRITICAL |
| Smart notification engine (FCM + WebSocket) | HIGH |
| Push notifications for critical alerts | HIGH |
| JWT refresh token mechanism | HIGH |
| Vitals tracking | HIGH |
| Allergy and risk factor management | HIGH |
| Digital signature for handoffs | HIGH |
| Lab report file attachments | MEDIUM |
| Ward/ICU transfer tracking | MEDIUM |
| Pharmacist and Lab Technician roles | MEDIUM |
| Tamper-proof audit trail (hash chain) | HIGH |
| PHI encryption at rest (AES-256) | HIGH |

---

## Architecture

### Backend Module Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                       │
│                                                             │
│  /api/v1/auth/      → Auth module (JWT, roles, refresh)     │
│  /api/v1/patients/  → Patient + Encounter + Notes           │
│  /api/v1/handoff/   → Handoff sessions + checklists         │
│  /api/v1/medication-tasks/ → Medication task engine         │
│  /api/v1/notifications/    → Notification inbox             │
│                                                             │
│  /ws/dictation/{id}   → Live ASR via Google Speech          │
│  /ws/alerts           → Real-time critical alert broadcast  │
│  /ws/handoff/{id}     → Live handoff progress sync          │
│                                                             │
│  Celery Beat (every 5 min) → Medication monitor cron        │
│  Celery Beat (daily)       → Audit hash chain integrity     │
└─────────────────────────────────────────────────────────────┘
              │                        │
       PostgreSQL DB              Redis (broker)
```

### Medication Escalation Flow

| Time Past Due | Action | Level |
|---|---|---|
| 0–30 min | Reminder → assigned nurse | 1 |
| 31–60 min | Overdue alert → nurse + charge nurse | 2 |
| 61–120 min | Critical escalation → attending doctor | 3 |
| 120+ min | Page doctor + log `CRITICAL_MISS` | 4 |

### Handoff Workflow (6 Steps)

```
1. INITIATION      → Nurse A calls /handoff/initiate; system auto-generates checklist
2. IN-PROGRESS     → Nurse A reviews and annotates each checklist item
3. TRANSFER REQUEST→ Nurse A selects Nurse B; push notification sent
4. INCOMING REVIEW → Nurse B reviews all items and Nurse A's notes
5. DIGITAL ACCEPT  → Nurse B provides biometric/PIN + digital signature
6. AUDIT TRAIL     → Full session hashed and stored immutably in audit_logs
```

---

## Database Schema

### Core Tables

| Table | Purpose |
|---|---|
| `users` | Staff accounts with roles: `DOCTOR`, `NURSE`, `ADMIN`, `RECEPTIONIST`, `LAB_TECHNICIAN`, `PHARMACIST` |
| `patients` | Patient demographics, allergies, risk flags, bed assignment |
| `encounters` | Admission episodes with lifecycle state and handoff status |
| `vitals` | BP, HR, SpO₂, temperature, GCS, pain score per encounter |
| `clinical_notes` | ASR-transcribed or manually entered notes |
| `medication_orders` | Prescriptions from doctors (drug, dose, route, frequency) |
| `medication_tasks` | Individual scheduled administration tasks generated from orders |
| `handoff_sessions` | Shift handoff records with checklist snapshots and signatures |
| `handoff_checklist_items` | Per-item status within a handoff session |
| `notifications` | In-app and push notification inbox |
| `audit_logs` | Append-only tamper-evident log with SHA-256 hash chain |

---

## API Reference

### Auth

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/token` | POST | Login — returns access + refresh token |
| `/api/v1/auth/refresh` | POST | Refresh JWT using refresh token |
| `/api/v1/auth/logout` | POST | Invalidate refresh token |
| `/api/v1/auth/device-token` | PUT | Register FCM device token |

### Patients

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/patients/` | POST | Create patient |
| `/api/v1/patients/` | GET | List / search patients |
| `/api/v1/patients/{id}/vitals` | POST | Record vitals |
| `/api/v1/patients/{id}/vitals/latest` | GET | Latest vitals |
| `/api/v1/patients/{id}/allergies` | PUT | Update allergy list (DOCTOR only) |
| `/api/v1/patients/{id}/risk-flags` | PUT | Update risk flags |

### Medications

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/encounters/{id}/medications` | POST | Create medication order (DOCTOR) |
| `/api/v1/encounters/{id}/medications` | GET | List active orders |
| `/api/v1/medication-tasks/my-tasks` | GET | Nurse's tasks for current shift |
| `/api/v1/medication-tasks/{id}/administer` | POST | Mark administered |
| `/api/v1/medication-tasks/{id}/skip` | POST | Skip with reason + supervisor alert |
| `/api/v1/medication-tasks/overdue` | GET | All overdue tasks (ADMIN, DOCTOR) |

### Handoff

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/handoff/initiate` | POST | Start handoff for an encounter |
| `/api/v1/handoff/{session_id}` | GET | Fetch session + checklist |
| `/api/v1/handoff/{session_id}/checklist/{item_id}` | PATCH | Verify a checklist item |
| `/api/v1/handoff/{session_id}/accept` | POST | Accept with digital signature |
| `/api/v1/handoff/{session_id}/reject` | POST | Reject with reason |
| `/api/v1/handoff/{session_id}/escalate` | POST | Escalate to supervisor |
| `/api/v1/handoff/pending` | GET | Pending handoffs awaiting acceptance |

### Notifications

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/notifications` | GET | Notification inbox (paginated) |
| `/api/v1/notifications/{id}/read` | PATCH | Mark as read |
| `/api/v1/notifications/unread-count` | GET | Badge count |

### WebSocket Channels

| Endpoint | Description |
|---|---|
| `/ws/dictation/{encounter_id}` | Live ASR dictation stream |
| `/ws/alerts` | Real-time critical alert broadcast |
| `/ws/handoff/{session_id}` | Live handoff progress sync |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm / Expo CLI
- PostgreSQL 14+
- Redis 7+
- Google Cloud credentials with Speech-to-Text API enabled
- Firebase project with Cloud Messaging enabled

### Backend Setup

```bash
cd backend

# Create and activate virtualenv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo 'EXPO_PUBLIC_API_URL=http://localhost:8000' > .env

# Start Expo dev server
npx expo start
```

### Start Celery Workers (for medication scheduling)

```bash
cd backend

# Worker
celery -A src.tasks.celery_app.celery worker --loglevel=info --concurrency=4

# Beat scheduler (separate terminal)
celery -A src.tasks.celery_app.celery beat --loglevel=info
```

---

## Environment Variables

Create `backend/.env` using `backend/.env.example` as a template:

```bash
# Database
DATABASE_URL=postgresql://hvs_user:hvs_dev_pass@localhost:5432/hvs_db

# JWT
JWT_SECRET_KEY=<64-char-hex-random-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Cloud Speech
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-speech.json

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Firebase Cloud Messaging
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-adminsdk.json

# PHI Encryption (32-byte hex = 64 chars)
PHI_ENCRYPTION_KEY=<64-char-hex>

# CORS
CORS_ALLOWED_ORIGINS=["http://localhost:8081","http://localhost:19006"]
```

Frontend `.env`:

```bash
EXPO_PUBLIC_API_URL=http://localhost:8000
```

> **⚠️ Never commit `.env` files or credential files to source control.**

---

## Running with Docker

```bash
# Build and start all services (backend, frontend, db, redis, celery)
docker compose up --build

# Run migrations inside the backend container
docker compose exec backend alembic upgrade head
```

Services started:
- **Backend API**: `http://localhost:8000`
- **Frontend (Expo)**: `http://localhost:8081`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## Safety Mechanisms

### Medication Safety

- **Hard block:** Allergy cross-check on order creation — API returns `409 CONFLICT`; physician override requires a written reason and creates an audit record.
- **Hard block:** Duplicate active order for the same drug in the same encounter is rejected.
- **Hard block:** Dose outside normal range (validated against drug reference).
- **Soft warning:** Controlled substances (opioids, insulin) require a witness nurse ID before the task can be closed.
- **Forced confirmation:** High-alert medications (insulin, heparin, chemotherapy) use a two-step UI with drug-name repeat-back.
- Every medication administration screen displays the patient's **name, DOB, bed number, and known allergies** before the nurse can confirm.


## Clinical Sign-Off Requirements

Before any real patient data is entered into this system, the following sign-off checklist must be completed and **physically signed** by the lead engineer, a senior clinician (RN or physician), the information security officer, and the project owner.

**Section A — Clinical Safety:** Handoff checklist correctness, DNR flag handling, allergy cross-check, medication confirmation UI, controlled substance witness flow, patient identity display, escalation chains, and digital signature immutability.

**Section B — Security:** All endpoints authenticated, ADMIN account creation guarded, HTTPS enforced, PHI encrypted at rest, audit log integrity verified, CORS restricted, rate limiting active, PHI absent from logs, penetration test passed.

**Section C — Infrastructure:** Staging mirrors production, DB backups tested, Celery monitoring configured, connection pool tested at 100 concurrent users, Alembic downgrade tested, Redis persistence confirmed.

**Section D — Regulatory:** Local health data regulation compliance reviewed (HIPAA / DISHA / equivalent), audit log retention period confirmed, Data Processing Agreements with Google Cloud and Firebase in place, staff training completed, incident response plan documented.

---


## Languages

![Python](https://img.shields.io/badge/Python-46.6%25-3776AB?logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-47.0%25-F7DF1E?logo=javascript&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-6.1%25-3178C6?logo=typescript&logoColor=white)

---

> **Document Version:** 1.0 — Generated from Implementation Plan v1.0
> **Classification:** Internal — Safety-Critical Healthcare System
> *Next mandatory review: after Phase 0 completion and after Phase 3 clinical walkthrough.*

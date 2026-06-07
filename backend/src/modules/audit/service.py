import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.modules.audit.models import AuditLog


PHI_DENYLIST = {
    "allergies",
    "known_allergies",
    "risk_flags",
    "emergency_contact",
    "phone_number",
    "date_of_birth",
    "name",
    "full_name",
}


def sanitize_audit_details(details: dict | None) -> dict | None:
    if details is None:
        return None

    sanitized: dict[str, object] = {}
    for key, value in details.items():
        normalized_key = key.lower()
        if normalized_key in PHI_DENYLIST:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_details(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_audit_details(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


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

    for field_name in ("request_payload", "old_value", "new_value"):
        field_value = kwargs.get(field_name)
        if isinstance(field_value, dict):
            kwargs[field_name] = sanitize_audit_details(field_value)

    log = AuditLog(
        **kwargs,
        timestamp=datetime.utcnow(),
        hash_chain=current_hash,
    )
    db.add(log)
    db.commit()
    return log


def create_audit_log(db: Session, **kwargs) -> AuditLog:
    return write_audit_log(db, **kwargs)

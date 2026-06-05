import hashlib
import json
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

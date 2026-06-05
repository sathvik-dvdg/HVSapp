"""
Audit middleware: automatically logs every state-changing request to audit_logs.
Reads user identity from JWT without raising exceptions (silent fail on anon requests).
"""
import json
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
                user_id = token_data.get("sub")
                if user_id and user_id.isdigit():
                    user_id = int(user_id)

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
    for part in parts:
        if part.isdigit():
            return part
    return None

from sqlalchemy import Column, BigInteger, String, DateTime, Integer, JSON, Text, ForeignKey, func
from src.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(200))
    patient_id = Column(String(100), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_payload = Column(JSON)
    response_status = Column(Integer)
    old_value = Column(JSON)
    new_value = Column(JSON)
    session_id = Column(String(200))
    hash_chain = Column(String(256))

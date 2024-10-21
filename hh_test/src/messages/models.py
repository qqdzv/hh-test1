from datetime import datetime,timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean,ForeignKey
from src.database import Base

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("user.id"))
    receiver_id = Column(Integer, ForeignKey("user.id"))
    content = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc).replace(tzinfo=None))
    
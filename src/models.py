import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    task = Column(Text, nullable=False)
    owner = Column(String(255), nullable=True)
    due_date = Column(String(100), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)

    meeting = relationship("Meeting", back_populates="action_items")
    embedding = relationship("Embedding", back_populates="action_item", uselist=False, cascade="all, delete-orphan")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action_item_id = Column(Integer, ForeignKey("action_items.id", ondelete="CASCADE"), nullable=False)
    text_chunk = Column(Text, nullable=False)
    vector_json = Column(Text, nullable=False)  # JSON-encoded array of floats

    action_item = relationship("ActionItem", back_populates="embedding")

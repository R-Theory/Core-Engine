from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"))
    external_id = Column(String(255), index=True)  # Canvas assignment ID
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True))
    points_possible = Column(Numeric(10, 2))
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="assignments")
    topic = relationship("Topic", back_populates="assignments")
    resources = relationship("Resource", back_populates="assignment")
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, title={self.title})>"
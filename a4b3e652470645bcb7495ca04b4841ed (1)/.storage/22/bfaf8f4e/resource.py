from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"))
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"))
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="SET NULL"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    resource_type = Column(String(50), nullable=False)  # 'file', 'link', 'repo', 'note'
    url = Column(String(500))
    file_path = Column(String(500))
    content = Column(Text)  # For notes
    metadata = Column(JSONB)
    tags = Column(ARRAY(String))
    ai_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="resources")
    course = relationship("Course", back_populates="resources")
    topic = relationship("Topic", back_populates="resources")
    assignment = relationship("Assignment", back_populates="resources")
    
    def __repr__(self):
        return f"<Resource(id={self.id}, title={self.title}, type={self.resource_type})>"
from sqlalchemy import Column, String, Integer, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255), index=True)  # Canvas course ID
    name = Column(String(255), nullable=False)
    code = Column(String(50))
    semester = Column(String(50))
    year = Column(Integer)
    instructor = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="courses")
    topics = relationship("Topic", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="course")
    
    def __repr__(self):
        return f"<Course(id={self.id}, name={self.name}, code={self.code})>"

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    parent_topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="topics")
    parent_topic = relationship("Topic", remote_side=[id])
    assignments = relationship("Assignment", back_populates="topic")
    resources = relationship("Resource", back_populates="topic")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name})>"
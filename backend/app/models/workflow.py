from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    definition = Column(JSONB, nullable=False)  # Workflow steps and configuration
    is_active = Column(Boolean, default=True)
    schedule_cron = Column(String(100))  # Cron expression for scheduled execution
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name})>"

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    execution_log = Column(JSONB)
    result = Column(JSONB)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, status={self.status})>"
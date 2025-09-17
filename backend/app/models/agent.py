from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class AIAgent(Base):
    __tablename__ = "ai_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    agent_type = Column(String(50), nullable=False)  # 'metagpt', 'claude', 'perplexity'
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    interactions = relationship("AgentInteraction", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AIAgent(id={self.id}, name={self.name}, type={self.agent_type})>"

class AgentInteraction(Base):
    __tablename__ = "agent_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False)
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="SET NULL"))
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    tokens_used = Column(Integer)
    cost = Column(Numeric(10, 4))
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="agent_interactions")
    agent = relationship("AIAgent", back_populates="interactions")
    
    def __repr__(self):
        return f"<AgentInteraction(id={self.id}, agent={self.agent.name})>"

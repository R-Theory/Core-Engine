from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Plugin(Base):
    __tablename__ = "plugins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    manifest = Column(JSONB, nullable=False)
    status = Column(String(50), default="inactive")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_configs = relationship("UserPluginConfig", back_populates="plugin", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Plugin(id={self.id}, name={self.name}, version={self.version})>"

class UserPluginConfig(Base):
    __tablename__ = "user_plugin_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    config = Column(JSONB, nullable=False)
    credentials = Column(JSONB)  # Encrypted OAuth tokens
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="plugin_configs")
    plugin = relationship("Plugin", back_populates="user_configs")
    
    def __repr__(self):
        return f"<UserPluginConfig(user_id={self.user_id}, plugin_id={self.plugin_id})>"
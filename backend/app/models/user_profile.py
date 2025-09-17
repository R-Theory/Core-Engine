from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class UserProfile(Base):
    """Extended user profile information for academic and personal context"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Academic Information
    university = Column(String(255))
    student_id = Column(String(100))
    academic_year = Column(String(50))  # Freshman, Sophomore, etc.
    major = Column(String(255))
    
    # AI Context Information
    personal_bio = Column(Text)
    current_courses = Column(Text)
    learning_style = Column(String(100))  # Visual, Hands-on, Theoretical, Mixed
    experience_level = Column(String(50))  # Beginner, Intermediate, Advanced, Expert
    
    # Additional context (JSON for flexibility)
    additional_context = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    context_documents = relationship("UserProfileDocument", back_populates="profile", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, university={self.university})>"


class UserProfileDocument(Base):
    """Documents uploaded by users to provide AI context"""
    __tablename__ = "user_profile_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Document Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(String(50))
    mime_type = Column(String(100))
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    extracted_text = Column(Text)  # Extracted text content for AI context
    processing_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="context_documents")
    
    def __repr__(self):
        return f"<UserProfileDocument(filename={self.filename}, processed={self.is_processed})>"


class UserIntegration(Base):
    """User's external service integrations and API connections"""
    __tablename__ = "user_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Integration Information
    service_name = Column(String(100), nullable=False)  # openai, anthropic, github, etc.
    service_type = Column(String(50), nullable=False)   # ai_model, code_repo, lms, storage
    display_name = Column(String(255))
    description = Column(Text)
    
    # Connection Status
    is_active = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True))
    connection_error = Column(Text)
    
    # Configuration (encrypted sensitive data)
    config_data = Column(JSON, default={})  # Non-sensitive config
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="integrations")
    credentials = relationship("UserCredential", back_populates="integration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserIntegration(service={self.service_name}, connected={self.is_connected})>"


class UserCredential(Base):
    """Encrypted storage for user API keys and sensitive credentials"""
    __tablename__ = "user_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("user_integrations.id"), nullable=False)
    
    # Credential Information
    credential_type = Column(String(50), nullable=False)  # api_key, token, oauth, etc.
    credential_name = Column(String(100), nullable=False)  # Display name
    
    # Encrypted Data (will be encrypted using app's secret key)
    encrypted_value = Column(Text, nullable=False)
    encryption_method = Column(String(50), default="AES256")
    
    # Metadata
    expires_at = Column(DateTime(timezone=True))
    last_used = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    integration = relationship("UserIntegration", back_populates="credentials")
    
    def __repr__(self):
        return f"<UserCredential(type={self.credential_type}, active={self.is_active})>"


class UserPreference(Base):
    """User preferences and application settings"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # UI Preferences
    theme = Column(String(50), default="system")  # light, dark, system
    language = Column(String(10), default="en")
    timezone = Column(String(100))
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    workflow_notifications = Column(Boolean, default=True)
    assignment_reminders = Column(Boolean, default=True)
    
    # AI Preferences
    default_ai_model = Column(String(100))
    ai_response_style = Column(String(50), default="balanced")  # concise, balanced, detailed
    
    # Privacy Settings
    data_sharing_analytics = Column(Boolean, default=False)
    public_profile = Column(Boolean, default=False)
    
    # Additional preferences (JSON for flexibility)
    additional_preferences = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, theme={self.theme})>"
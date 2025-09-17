"""
AI Context Models - Store and manage user context for personalized AI interactions

These models store rich context about users that enables AI systems to provide
personalized, relevant assistance based on learning style, background, and current projects.
"""

from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base

class UserAIContext(Base):
    """
    User AI Context - Core personalization data for AI interactions
    
    Stores comprehensive user information that helps AI assistants provide
    more relevant and personalized responses.
    """
    __tablename__ = "user_ai_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal Information
    bio = Column(Text, nullable=True, doc="User's personal bio and background")
    academic_background = Column(JSON, nullable=True, doc="Academic history, degrees, institutions")
    current_role = Column(String(100), nullable=True, doc="Current academic/professional role")
    
    # Learning Preferences
    learning_style = Column(String(50), nullable=True, doc="Preferred learning style")
    experience_level = Column(String(50), nullable=True, doc="Overall experience level")
    preferred_explanation_style = Column(String(50), nullable=True, doc="How they like explanations")
    communication_style = Column(String(50), nullable=True, doc="Formal, casual, technical, etc.")
    
    # Current Context
    current_courses = Column(JSON, nullable=True, doc="Currently enrolled courses")
    current_projects = Column(JSON, nullable=True, doc="Active projects and research")
    goals_and_objectives = Column(JSON, nullable=True, doc="Short and long-term goals")
    areas_of_interest = Column(JSON, nullable=True, doc="Subject areas of particular interest")
    
    # AI Interaction Preferences
    ai_personality_preference = Column(String(50), nullable=True, doc="Preferred AI assistant personality")
    response_length_preference = Column(String(20), nullable=True, doc="Brief, detailed, comprehensive")
    use_examples = Column(Boolean, default=True, doc="Whether to include examples in responses")
    use_analogies = Column(Boolean, default=True, doc="Whether to use analogies")
    
    # Technical Preferences
    preferred_programming_languages = Column(JSON, nullable=True, doc="Languages user works with")
    technical_expertise = Column(JSON, nullable=True, doc="Areas of technical knowledge")
    tools_and_platforms = Column(JSON, nullable=True, doc="Familiar tools and platforms")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_ai_interaction = Column(DateTime, nullable=True)
    total_interactions = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="ai_context")
    context_documents = relationship("UserContextDocument", back_populates="ai_context", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="user_context", cascade="all, delete-orphan")

class UserContextDocument(Base):
    """
    Context Documents - User-uploaded documents that provide additional context
    
    Stores documents like resumes, research papers, project descriptions that
    help AI understand the user's background and expertise.
    """
    __tablename__ = "user_context_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_context_id = Column(UUID(as_uuid=True), ForeignKey("user_ai_contexts.id"), nullable=False)
    
    # Document Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Content and Processing
    content = Column(Text, nullable=True, doc="Extracted text content")
    summary = Column(Text, nullable=True, doc="AI-generated summary")
    key_points = Column(JSON, nullable=True, doc="Extracted key information")
    embeddings = Column(JSON, nullable=True, doc="Vector embeddings for semantic search")
    
    # Classification
    document_type = Column(String(50), nullable=True, doc="resume, research_paper, project_description, etc.")
    relevance_score = Column(Integer, default=5, doc="How relevant this doc is to user context (1-10)")
    tags = Column(JSON, nullable=True, doc="Auto-generated and user tags")
    
    # Processing Status
    processing_status = Column(String(20), default="pending", doc="pending, processing, completed, failed")
    processing_error = Column(Text, nullable=True)
    
    # Storage
    storage_path = Column(String(500), nullable=True, doc="Path to stored file")
    storage_metadata = Column(JSON, nullable=True, doc="Storage-specific metadata")
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, nullable=True)
    
    # Relationships
    ai_context = relationship("UserAIContext", back_populates="context_documents")

class AIConversation(Base):
    """
    AI Conversations - Track AI interactions for learning and improvement
    
    Stores conversation history to improve future interactions and understand
    user preferences and patterns.
    """
    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_context_id = Column(UUID(as_uuid=True), ForeignKey("user_ai_contexts.id"), nullable=False)
    
    # Conversation Metadata
    title = Column(String(200), nullable=True, doc="Auto-generated conversation title")
    ai_provider = Column(String(50), nullable=False, doc="openai, anthropic, etc.")
    ai_model = Column(String(50), nullable=False, doc="gpt-4, claude-3, etc.")
    
    # Context Used
    context_used = Column(JSON, nullable=True, doc="Which context elements were used")
    documents_referenced = Column(JSON, nullable=True, doc="IDs of documents referenced")
    
    # Conversation Data
    messages = Column(JSON, nullable=False, doc="Array of conversation messages")
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Quality and Feedback
    user_rating = Column(Integer, nullable=True, doc="1-5 star rating from user")
    user_feedback = Column(Text, nullable=True, doc="Written feedback from user")
    
    # Classification
    conversation_type = Column(String(50), nullable=True, doc="academic_help, coding, research, etc.")
    topics = Column(JSON, nullable=True, doc="Auto-detected topics discussed")
    
    # Metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_context = relationship("UserAIContext", back_populates="ai_conversations")

class AIContextTemplate(Base):
    """
    Context Templates - Predefined context templates for different user types
    
    Provides starting templates for different types of users (CS student, researcher, etc.)
    to help them get started with meaningful AI context.
    """
    __tablename__ = "ai_context_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template Information
    name = Column(String(100), nullable=False, doc="Template name (e.g., 'CS Undergraduate')")
    description = Column(Text, nullable=False, doc="Description of what this template is for")
    category = Column(String(50), nullable=False, doc="undergraduate, graduate, researcher, professional")
    
    # Template Data
    template_data = Column(JSON, nullable=False, doc="Default values for UserAIContext fields")
    suggested_documents = Column(JSON, nullable=True, doc="Types of documents to upload")
    suggested_settings = Column(JSON, nullable=True, doc="Recommended AI interaction settings")
    
    # Usage
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

class ContextProcessingJob(Base):
    """
    Context Processing Jobs - Track background processing of context documents
    
    Manages the async processing of uploaded documents for context extraction,
    summarization, and embedding generation.
    """
    __tablename__ = "context_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("user_context_documents.id"), nullable=False)
    
    # Job Information
    job_type = Column(String(50), nullable=False, doc="extract_text, generate_summary, create_embeddings")
    status = Column(String(20), default="pending", doc="pending, processing, completed, failed")
    
    # Processing Details
    processor_used = Column(String(50), nullable=True, doc="Which processor/AI model was used")
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Results
    result_data = Column(JSON, nullable=True, doc="Processing results")
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
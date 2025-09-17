"""
AI Context Service - Manages user context for personalized AI interactions

This service handles the creation, updating, and retrieval of user AI context,
processes context documents, and provides personalized prompts for AI models.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.ai_context import (
    UserAIContext, UserContextDocument, AIConversation, 
    AIContextTemplate, ContextProcessingJob
)
from app.models.user_profile import UserProfile
from app.core.plugin_interface import PluginResult
import logging

logger = logging.getLogger(__name__)

class AIContextService:
    """
    Service for managing user AI context and personalized interactions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_or_create_user_context(self, db: Session, user_id: str) -> UserAIContext:
        """
        Get existing user AI context or create a new one
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            UserAIContext: User's AI context
        """
        # Check if context already exists
        context = db.query(UserAIContext).filter(
            UserAIContext.user_id == user_id
        ).first()
        
        if context:
            return context
        
        # Create new context with defaults
        context = UserAIContext(
            user_id=user_id,
            learning_style="mixed",
            experience_level="intermediate",
            preferred_explanation_style="detailed",
            communication_style="friendly",
            response_length_preference="detailed",
            use_examples=True,
            use_analogies=True,
            current_courses=[],
            current_projects=[],
            goals_and_objectives=[],
            areas_of_interest=[],
            preferred_programming_languages=[],
            technical_expertise=[],
            tools_and_platforms=[]
        )
        
        db.add(context)
        db.commit()
        db.refresh(context)
        
        self.logger.info(f"Created new AI context for user {user_id}")
        return context

    async def update_user_context(
        self, 
        db: Session, 
        user_id: str, 
        context_data: Dict[str, Any]
    ) -> UserAIContext:
        """
        Update user AI context with new data
        
        Args:
            db: Database session
            user_id: User ID
            context_data: Dictionary of context updates
            
        Returns:
            UserAIContext: Updated context
        """
        context = await self.get_or_create_user_context(db, user_id)
        
        # Update fields
        for field, value in context_data.items():
            if hasattr(context, field):
                setattr(context, field, value)
        
        context.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(context)
        
        self.logger.info(f"Updated AI context for user {user_id}")
        return context

    async def add_context_document(
        self,
        db: Session,
        user_id: str,
        filename: str,
        content: str,
        file_type: str,
        file_size: int,
        document_type: Optional[str] = None
    ) -> UserContextDocument:
        """
        Add a context document for the user
        
        Args:
            db: Database session
            user_id: User ID
            filename: Original filename
            content: Extracted text content
            file_type: File type/extension
            file_size: File size in bytes
            document_type: Type of document (resume, research_paper, etc.)
            
        Returns:
            UserContextDocument: Created document
        """
        context = await self.get_or_create_user_context(db, user_id)
        
        document = UserContextDocument(
            ai_context_id=context.id,
            filename=filename,
            original_filename=filename,
            file_type=file_type,
            file_size=file_size,
            content=content,
            document_type=document_type,
            processing_status="completed"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Queue background processing for summary and embeddings
        await self._queue_document_processing(db, document.id)
        
        self.logger.info(f"Added context document {filename} for user {user_id}")
        return document

    async def _queue_document_processing(self, db: Session, document_id: str):
        """Queue background processing jobs for a document"""
        processing_jobs = [
            ContextProcessingJob(
                document_id=document_id,
                job_type="generate_summary",
                status="pending"
            ),
            ContextProcessingJob(
                document_id=document_id,
                job_type="extract_key_points",
                status="pending"
            ),
            ContextProcessingJob(
                document_id=document_id,
                job_type="generate_embeddings",
                status="pending"
            )
        ]
        
        for job in processing_jobs:
            db.add(job)
        
        db.commit()

    async def get_personalized_context(self, db: Session, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive personalized context for AI interactions
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict containing all relevant context for AI interactions
        """
        context = await self.get_or_create_user_context(db, user_id)
        
        # Get context documents
        documents = db.query(UserContextDocument).filter(
            UserContextDocument.ai_context_id == context.id,
            UserContextDocument.processing_status == "completed"
        ).limit(10).all()
        
        # Get recent conversations for patterns
        recent_conversations = db.query(AIConversation).filter(
            AIConversation.user_context_id == context.id
        ).order_by(AIConversation.last_message_at.desc()).limit(5).all()
        
        # Build comprehensive context
        personalized_context = {
            "user_profile": {
                "bio": context.bio,
                "academic_background": context.academic_background,
                "current_role": context.current_role,
                "learning_style": context.learning_style,
                "experience_level": context.experience_level,
                "communication_style": context.communication_style
            },
            "current_context": {
                "courses": context.current_courses or [],
                "projects": context.current_projects or [],
                "goals": context.goals_and_objectives or [],
                "interests": context.areas_of_interest or []
            },
            "technical_profile": {
                "programming_languages": context.preferred_programming_languages or [],
                "expertise": context.technical_expertise or [],
                "tools": context.tools_and_platforms or []
            },
            "ai_preferences": {
                "personality": context.ai_personality_preference,
                "response_length": context.response_length_preference,
                "use_examples": context.use_examples,
                "use_analogies": context.use_analogies,
                "explanation_style": context.preferred_explanation_style
            },
            "context_documents": [
                {
                    "filename": doc.filename,
                    "type": doc.document_type,
                    "summary": doc.summary,
                    "key_points": doc.key_points,
                    "relevance": doc.relevance_score
                }
                for doc in documents
            ],
            "interaction_history": {
                "total_interactions": context.total_interactions,
                "last_interaction": context.last_ai_interaction,
                "recent_topics": self._extract_recent_topics(recent_conversations)
            }
        }
        
        return personalized_context

    def _extract_recent_topics(self, conversations: List[AIConversation]) -> List[str]:
        """Extract topics from recent conversations"""
        topics = []
        for conv in conversations:
            if conv.topics:
                topics.extend(conv.topics)
        
        # Return unique topics, limited to most recent
        return list(set(topics))[:10]

    async def build_personalized_prompt(
        self, 
        db: Session, 
        user_id: str, 
        user_query: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> str:
        """
        Build a personalized prompt for AI models based on user context
        
        Args:
            db: Database session
            user_id: User ID
            user_query: User's current question/request
            conversation_context: Previous conversation messages
            
        Returns:
            Personalized prompt string
        """
        context = await self.get_personalized_context(db, user_id)
        
        # Build system prompt with personalization
        prompt_parts = [
            "You are an AI assistant helping a student/researcher. Here's what you know about them:\n"
        ]
        
        # Add user profile
        profile = context["user_profile"]
        if profile.get("bio"):
            prompt_parts.append(f"BACKGROUND: {profile['bio']}\n")
        
        if profile.get("current_role"):
            prompt_parts.append(f"CURRENT ROLE: {profile['current_role']}\n")
        
        # Add learning preferences
        if profile.get("learning_style"):
            prompt_parts.append(f"LEARNING STYLE: {profile['learning_style']}\n")
        
        if profile.get("experience_level"):
            prompt_parts.append(f"EXPERIENCE LEVEL: {profile['experience_level']}\n")
        
        # Add current context
        current = context["current_context"]
        if current.get("courses"):
            prompt_parts.append(f"CURRENT COURSES: {', '.join(current['courses'])}\n")
        
        if current.get("projects"):
            prompt_parts.append(f"CURRENT PROJECTS: {', '.join(current['projects'])}\n")
        
        # Add technical profile
        technical = context["technical_profile"]
        if technical.get("programming_languages"):
            prompt_parts.append(f"PROGRAMMING LANGUAGES: {', '.join(technical['programming_languages'])}\n")
        
        # Add AI preferences
        prefs = context["ai_preferences"]
        response_style = []
        
        if prefs.get("response_length") == "brief":
            response_style.append("Keep responses concise and to-the-point")
        elif prefs.get("response_length") == "comprehensive":
            response_style.append("Provide comprehensive, detailed explanations")
        
        if prefs.get("use_examples"):
            response_style.append("Include practical examples")
        
        if prefs.get("use_analogies"):
            response_style.append("Use analogies to explain complex concepts")
        
        if prefs.get("communication_style") == "casual":
            response_style.append("Use a friendly, casual tone")
        elif prefs.get("communication_style") == "formal":
            response_style.append("Maintain a professional, formal tone")
        
        if response_style:
            prompt_parts.append(f"RESPONSE STYLE: {'; '.join(response_style)}\n")
        
        # Add relevant document context
        docs = context["context_documents"]
        if docs:
            prompt_parts.append("\nRELEVANT CONTEXT DOCUMENTS:")
            for doc in docs[:3]:  # Include top 3 most relevant
                if doc.get("summary"):
                    prompt_parts.append(f"- {doc['filename']}: {doc['summary']}")
            prompt_parts.append("")
        
        # Add conversation history if provided
        if conversation_context:
            prompt_parts.append("CONVERSATION HISTORY:")
            for msg in conversation_context[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:200]  # Truncate long messages
                prompt_parts.append(f"{role.upper()}: {content}")
            prompt_parts.append("")
        
        # Add the current query
        prompt_parts.append(f"CURRENT QUESTION: {user_query}\n")
        
        # Instructions
        prompt_parts.append(
            "Please provide a helpful response based on this context. "
            "Tailor your explanation to their background, learning style, and current situation."
        )
        
        return "\n".join(prompt_parts)

    async def save_conversation(
        self,
        db: Session,
        user_id: str,
        messages: List[Dict[str, Any]],
        ai_provider: str,
        ai_model: str,
        conversation_type: Optional[str] = None
    ) -> AIConversation:
        """
        Save an AI conversation for learning and improvement
        
        Args:
            db: Database session
            user_id: User ID
            messages: List of conversation messages
            ai_provider: AI provider used (openai, anthropic, etc.)
            ai_model: Specific model used
            conversation_type: Type of conversation
            
        Returns:
            AIConversation: Saved conversation
        """
        context = await self.get_or_create_user_context(db, user_id)
        
        # Generate conversation title from first user message
        title = "AI Conversation"
        if messages:
            first_user_msg = next((msg for msg in messages if msg.get("role") == "user"), None)
            if first_user_msg:
                content = first_user_msg.get("content", "")
                title = content[:100] + "..." if len(content) > 100 else content
        
        conversation = AIConversation(
            user_context_id=context.id,
            title=title,
            ai_provider=ai_provider,
            ai_model=ai_model,
            messages=messages,
            total_messages=len(messages),
            conversation_type=conversation_type,
            last_message_at=datetime.utcnow()
        )
        
        db.add(conversation)
        
        # Update user context stats
        context.total_interactions += 1
        context.last_ai_interaction = datetime.utcnow()
        
        db.commit()
        db.refresh(conversation)
        
        self.logger.info(f"Saved AI conversation for user {user_id}")
        return conversation

    async def get_context_templates(self, db: Session) -> List[AIContextTemplate]:
        """Get available context templates"""
        return db.query(AIContextTemplate).filter(
            AIContextTemplate.is_active == True
        ).all()

    async def apply_context_template(
        self, 
        db: Session, 
        user_id: str, 
        template_id: str
    ) -> UserAIContext:
        """Apply a context template to a user's AI context"""
        template = db.query(AIContextTemplate).filter(
            AIContextTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        context = await self.get_or_create_user_context(db, user_id)
        
        # Apply template data
        template_data = template.template_data
        for field, value in template_data.items():
            if hasattr(context, field):
                setattr(context, field, value)
        
        # Update usage count
        template.usage_count += 1
        
        db.commit()
        db.refresh(context)
        
        self.logger.info(f"Applied template {template.name} to user {user_id}")
        return context

# Global service instance
ai_context_service = AIContextService()
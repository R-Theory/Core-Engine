"""
AI Context API - Endpoints for managing user AI context and personalized interactions

This module provides REST API endpoints for the AI context system, enabling
users to manage their personal context and interact with AI assistants.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_context_service import ai_context_service
from app.services.ai_provider_service import ai_provider_service
from app.core.document_engine import document_engine

router = APIRouter()

# Request/Response models
class AIContextUpdateRequest(BaseModel):
    """Request model for updating AI context"""
    bio: Optional[str] = None
    academic_background: Optional[Dict[str, Any]] = None
    current_role: Optional[str] = None
    learning_style: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_explanation_style: Optional[str] = None
    communication_style: Optional[str] = None
    current_courses: Optional[List[str]] = None
    current_projects: Optional[List[str]] = None
    goals_and_objectives: Optional[List[str]] = None
    areas_of_interest: Optional[List[str]] = None
    ai_personality_preference: Optional[str] = None
    response_length_preference: Optional[str] = None
    use_examples: Optional[bool] = None
    use_analogies: Optional[bool] = None
    preferred_programming_languages: Optional[List[str]] = None
    technical_expertise: Optional[List[str]] = None
    tools_and_platforms: Optional[List[str]] = None

class AIContextResponse(BaseModel):
    """Response model for AI context"""
    success: bool
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    """Request model for AI chat"""
    message: str
    conversation_id: Optional[str] = None
    ai_provider: str = "openai"
    ai_model: str = "gpt-4"
    include_context: bool = True

class ChatResponse(BaseModel):
    """Response model for AI chat"""
    success: bool
    response: str
    conversation_id: str
    context_used: Dict[str, Any]
    metadata: Dict[str, Any] = {}

class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    success: bool
    conversations: List[Dict[str, Any]]
    total_count: int

@router.get("/context", response_model=AIContextResponse)
async def get_user_context(
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Get user's AI context
    
    Args:
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        User's complete AI context
    """
    try:
        context = await ai_context_service.get_personalized_context(db, user_id)
        
        return AIContextResponse(
            success=True,
            message="AI context retrieved successfully",
            context=context
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.put("/context", response_model=AIContextResponse)
async def update_user_context(
    request: AIContextUpdateRequest,
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Update user's AI context
    
    Args:
        request: Context update data
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        Updated context confirmation
    """
    try:
        # Convert request to dict, excluding None values
        context_data = {
            k: v for k, v in request.dict().items() 
            if v is not None
        }
        
        context = await ai_context_service.update_user_context(
            db, user_id, context_data
        )
        
        return AIContextResponse(
            success=True,
            message="AI context updated successfully",
            context={
                "updated_fields": list(context_data.keys()),
                "last_updated": context.updated_at.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update context: {str(e)}")

@router.post("/context/documents", response_model=AIContextResponse)
async def upload_context_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(default=None),
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Upload a context document for AI personalization
    
    Args:
        file: Uploaded file
        document_type: Type of document (resume, research_paper, etc.)
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        Upload confirmation
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Process the document using our document engine
        import tempfile
        import os
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        try:
            # Process with document engine
            result = await document_engine.process_file(temp_file.name)
            
            if result.success:
                document_data = result.data.get("document", {})
                
                # Add to user's AI context
                context_doc = await ai_context_service.add_context_document(
                    db=db,
                    user_id=user_id,
                    filename=file.filename,
                    content=document_data.get("content", ""),
                    file_type=document_data.get("file_type", "unknown"),
                    file_size=len(content),
                    document_type=document_type
                )
                
                return AIContextResponse(
                    success=True,
                    message="Context document uploaded and processed successfully",
                    context={
                        "document_id": str(context_doc.id),
                        "filename": context_doc.filename,
                        "processing_status": context_doc.processing_status
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Document processing failed: {result.error_message}"
                )
        
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/context/documents")
async def get_context_documents(
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Get user's context documents
    
    Args:
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        List of user's context documents
    """
    try:
        from app.models.ai_context import UserAIContext, UserContextDocument
        
        # Get user context
        context = await ai_context_service.get_or_create_user_context(db, user_id)
        
        # Get documents
        documents = db.query(UserContextDocument).filter(
            UserContextDocument.ai_context_id == context.id
        ).all()
        
        doc_list = [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type,
                "file_size": doc.file_size,
                "processing_status": doc.processing_status,
                "relevance_score": doc.relevance_score,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "summary": doc.summary
            }
            for doc in documents
        ]
        
        return {
            "success": True,
            "documents": doc_list,
            "total_count": len(doc_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Chat with AI using personalized context
    
    Args:
        request: Chat request
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        AI response with context
    """
    try:
        # Build personalized prompt
        if request.include_context:
            personalized_prompt = await ai_context_service.build_personalized_prompt(
                db=db,
                user_id=user_id,
                user_query=request.message
            )
        else:
            personalized_prompt = f"You are a helpful AI assistant. Please respond to: {request.message}"
        
        # Get conversation history if this is part of an ongoing conversation
        conversation_history = []
        if request.conversation_id:
            # Get previous messages from the conversation
            # This would require querying the conversation by ID
            pass
        
        # Generate AI response using the provider service
        ai_response = await ai_provider_service.generate_contextual_response(
            provider_name=request.ai_provider,
            model=request.ai_model,
            user_message=request.message,
            personalized_prompt=personalized_prompt,
            conversation_history=conversation_history
        )
        
        if not ai_response["success"]:
            raise HTTPException(status_code=500, detail=ai_response.get("error", "AI response generation failed"))
        
        # Save conversation
        messages = [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": ai_response["response"]}
        ]
        
        conversation = await ai_context_service.save_conversation(
            db=db,
            user_id=user_id,
            messages=messages,
            ai_provider=request.ai_provider,
            ai_model=request.ai_model
        )
        
        # Get context used for the response
        context_used = await ai_context_service.get_personalized_context(db, user_id)
        
        return ChatResponse(
            success=True,
            response=ai_response["response"],
            conversation_id=str(conversation.id),
            context_used={
                "profile_used": bool(context_used["user_profile"].get("bio")),
                "documents_referenced": len(context_used["context_documents"]),
                "technical_context": bool(context_used["technical_profile"]["programming_languages"]),
                "current_context": bool(context_used["current_context"]["courses"])
            },
            metadata={
                "ai_provider": request.ai_provider,
                "ai_model": request.ai_model,
                "prompt_length": len(personalized_prompt),
                "usage": ai_response.get("usage", {}),
                "context_elements_used": len([
                    k for k, v in context_used.items() 
                    if v and (isinstance(v, dict) and any(v.values()) or isinstance(v, list) and v)
                ])
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/conversations", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    limit: int = 20,
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Get user's conversation history
    
    Args:
        limit: Number of conversations to return
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        List of recent conversations
    """
    try:
        from app.models.ai_context import UserAIContext, AIConversation
        
        # Get user context
        context = await ai_context_service.get_or_create_user_context(db, user_id)
        
        # Get conversations
        conversations = db.query(AIConversation).filter(
            AIConversation.user_context_id == context.id
        ).order_by(AIConversation.last_message_at.desc()).limit(limit).all()
        
        conv_list = [
            {
                "id": str(conv.id),
                "title": conv.title,
                "ai_provider": conv.ai_provider,
                "ai_model": conv.ai_model,
                "total_messages": conv.total_messages,
                "conversation_type": conv.conversation_type,
                "started_at": conv.started_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat(),
                "user_rating": conv.user_rating
            }
            for conv in conversations
        ]
        
        return ConversationHistoryResponse(
            success=True,
            conversations=conv_list,
            total_count=len(conv_list)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/templates")
async def get_context_templates(db: Session = Depends(get_db)):
    """
    Get available AI context templates
    
    Args:
        db: Database session
        
    Returns:
        List of available templates
    """
    try:
        templates = await ai_context_service.get_context_templates(db)
        
        template_list = [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "usage_count": template.usage_count
            }
            for template in templates
        ]
        
        return {
            "success": True,
            "templates": template_list,
            "total_count": len(template_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.post("/templates/{template_id}/apply")
async def apply_context_template(
    template_id: str,
    user_id: str = "default_user",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """
    Apply a context template to user's AI context
    
    Args:
        template_id: Template ID to apply
        user_id: User ID (from auth)
        db: Database session
        
    Returns:
        Application confirmation
    """
    try:
        context = await ai_context_service.apply_context_template(
            db=db,
            user_id=user_id,
            template_id=template_id
        )
        
        return {
            "success": True,
            "message": "Template applied successfully",
            "context_updated": context.updated_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")

@router.get("/providers")
async def get_ai_providers():
    """
    Get available AI providers and their configuration status
    
    Returns:
        Information about available AI providers, models, and configuration status
    """
    try:
        provider_status = ai_provider_service.get_provider_status()
        
        return {
            "success": True,
            "providers": provider_status,
            "total_providers": len(provider_status),
            "configured_providers": len([p for p in provider_status.values() if p["configured"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")

@router.get("/providers/{provider_name}/models")
async def get_provider_models(provider_name: str):
    """
    Get available models for a specific AI provider
    
    Args:
        provider_name: Name of the AI provider
        
    Returns:
        List of available models for the provider
    """
    try:
        models = ai_provider_service.get_available_models(provider_name)
        
        if not models:
            raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
        
        return {
            "success": True,
            "provider": provider_name,
            "models": models,
            "total_models": len(models)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for AI context system
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "ai_context",
        "features": [
            "personalized_context",
            "document_processing", 
            "conversation_history",
            "context_templates"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
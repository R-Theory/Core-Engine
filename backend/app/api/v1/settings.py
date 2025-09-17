from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, UserProfile, UserIntegration, UserCredential, UserPreference, UserProfileDocument
from app.integrations import integration_engine

router = APIRouter()

# Pydantic models for request/response
class UserProfileResponse(BaseModel):
    id: str
    university: Optional[str] = None
    student_id: Optional[str] = None
    academic_year: Optional[str] = None
    major: Optional[str] = None
    personal_bio: Optional[str] = None
    current_courses: Optional[str] = None
    learning_style: Optional[str] = None
    experience_level: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    university: Optional[str] = None
    student_id: Optional[str] = None
    academic_year: Optional[str] = None
    major: Optional[str] = None
    personal_bio: Optional[str] = None
    current_courses: Optional[str] = None
    learning_style: Optional[str] = None
    experience_level: Optional[str] = None

class UserIntegrationResponse(BaseModel):
    id: str
    service_name: str
    service_type: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    is_connected: bool
    last_sync: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserIntegrationCreate(BaseModel):
    service_name: str
    service_type: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    config_data: Optional[dict] = {}

class UserPreferenceResponse(BaseModel):
    id: str
    theme: str
    language: str
    timezone: Optional[str] = None
    email_notifications: bool
    push_notifications: bool
    workflow_notifications: bool
    assignment_reminders: bool
    default_ai_model: Optional[str] = None
    ai_response_style: str
    data_sharing_analytics: bool
    public_profile: bool
    
    class Config:
        from_attributes = True

class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    workflow_notifications: Optional[bool] = None
    assignment_reminders: Optional[bool] = None
    default_ai_model: Optional[str] = None
    ai_response_style: Optional[str] = None
    data_sharing_analytics: Optional[bool] = None
    public_profile: Optional[bool] = None

class ContextDocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: Optional[str] = None
    mime_type: Optional[str] = None
    is_processed: bool
    created_at: str
    
    class Config:
        from_attributes = True

# User Profile Endpoints
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile information"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        # Create default profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update fields that are provided
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile

# User Preferences Endpoints
@router.get("/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences and settings"""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreference(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

@router.put("/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    preferences_data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences and settings"""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.add(preferences)
    
    # Update fields that are provided
    for field, value in preferences_data.dict(exclude_unset=True).items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    return preferences

# Integration Endpoints
@router.get("/integrations", response_model=List[UserIntegrationResponse])
async def get_user_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user integrations"""
    integrations = db.query(UserIntegration).filter(UserIntegration.user_id == current_user.id).all()
    return integrations

@router.post("/integrations", response_model=UserIntegrationResponse)
async def create_user_integration(
    integration_data: UserIntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new integration"""
    integration = UserIntegration(
        user_id=current_user.id,
        **integration_data.dict()
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration

@router.put("/integrations/{integration_id}/toggle")
async def toggle_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle integration active status"""
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration.is_active = not integration.is_active
    db.commit()
    
    return {"status": "success", "is_active": integration.is_active}

@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an integration"""
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    db.delete(integration)
    db.commit()
    
    return {"status": "success", "message": "Integration deleted"}

# Context Documents Endpoints
@router.get("/context-documents", response_model=List[ContextDocumentResponse])
async def get_context_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user context documents"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return []
    
    documents = db.query(UserProfileDocument).filter(UserProfileDocument.profile_id == profile.id).all()
    return documents

@router.post("/context-documents/upload")
async def upload_context_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a context document for AI personalization"""
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    filename = f"{file_id}.{file_extension}" if file_extension else file_id
    
    # TODO: Implement actual file storage (S3, local filesystem, etc.)
    file_path = f"/app/storage/context_documents/{filename}"
    
    # Save file metadata
    document = UserProfileDocument(
        profile_id=profile.id,
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=str(file.size) if file.size else None,
        mime_type=file.content_type
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # TODO: Process document for text extraction in background task
    
    return {"status": "success", "document_id": str(document.id), "message": "Document uploaded successfully"}

@router.delete("/context-documents/{document_id}")
async def delete_context_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a context document"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    document = db.query(UserProfileDocument).filter(
        UserProfileDocument.id == document_id,
        UserProfileDocument.profile_id == profile.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # TODO: Delete actual file from storage
    
    db.delete(document)
    db.commit()
    
    return {"status": "success", "message": "Document deleted"}

# Account endpoints
@router.get("/account")
async def get_account_info(
    current_user: User = Depends(get_current_user)
):
    """Get basic account information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

@router.put("/account")
async def update_account_info(
    account_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update basic account information"""
    allowed_fields = ['first_name', 'last_name', 'username']
    
    for field, value in account_data.items():
        if field in allowed_fields:
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {"status": "success", "message": "Account updated successfully"}

# Integration Management Endpoints
@router.get("/integrations/available")
async def get_available_integrations():
    """Get all available integration types"""
    available = integration_engine.registry.get_available_integrations()
    
    # Add user-friendly metadata
    integrations_info = {}
    for key, info in available.items():
        integrations_info[key] = {
            "service_name": info["service_name"],
            "integration_type": info["integration_type"],
            "capabilities": info["capabilities"],
            "description": {
                "canvas": "Sync courses, assignments, and grades from Canvas LMS",
                "github": "Connect code repositories, issues, and pull requests",
                "notion": "Sync pages and databases for knowledge management"
            }.get(key, f"Integration with {info['service_name']}")
        }
    
    return integrations_info

@router.post("/integrations/{service_key}/test")
async def test_integration_connection(
    service_key: str,
    config_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Test an integration configuration before saving"""
    try:
        success = await integration_engine.test_integration(service_key, config_data)
        return {
            "status": "success" if success else "failed",
            "message": "Connection successful" if success else "Connection failed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/integrations/{service_key}/setup")
async def setup_new_integration(
    service_key: str,
    config_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set up a new integration"""
    try:
        # Test connection first
        success = await integration_engine.test_integration(service_key, config_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to connect to service")
        
        # Get service info
        available = integration_engine.registry.get_available_integrations()
        if service_key not in available:
            raise HTTPException(status_code=404, detail="Unknown integration type")
        
        service_info = available[service_key]
        
        # Create integration record
        integration = UserIntegration(
            user_id=current_user.id,
            service_name=service_key,
            service_type=service_info["integration_type"],
            display_name=service_info["service_name"],
            description={
                "canvas": "Canvas LMS - Courses and assignments",
                "github": "GitHub - Code repositories and issues", 
                "notion": "Notion - Knowledge management and notes"
            }.get(service_key, service_info["service_name"]),
            is_active=True,
            is_connected=True,
            config_data=config_data
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "status": "success",
            "integration_id": str(integration.id),
            "message": f"{service_info['service_name']} integration set up successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/{integration_id}/sync")
async def trigger_integration_sync(
    integration_id: str,
    full_sync: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger manual sync for an integration"""
    try:
        # Verify integration belongs to user
        integration = db.query(UserIntegration).filter(
            UserIntegration.id == integration_id,
            UserIntegration.user_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Trigger sync
        results = await integration_engine.sync_user_integrations(
            db, str(current_user.id), [integration_id]
        )
        
        sync_result = results.get(integration_id)
        if sync_result:
            return {
                "status": sync_result.status,
                "items_processed": sync_result.items_processed,
                "items_created": sync_result.items_created,
                "items_updated": sync_result.items_updated,
                "items_failed": sync_result.items_failed,
                "error_message": sync_result.error_message
            }
        else:
            raise HTTPException(status_code=500, detail="Sync failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/sync-status")
async def get_integration_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync status for all user integrations"""
    integrations = db.query(UserIntegration).filter(
        UserIntegration.user_id == current_user.id
    ).all()
    
    status_info = []
    for integration in integrations:
        status_info.append({
            "integration_id": str(integration.id),
            "service_name": integration.service_name,
            "display_name": integration.display_name,
            "is_active": integration.is_active,
            "is_connected": integration.is_connected,
            "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
            "connection_error": integration.connection_error
        })
    
    return status_info
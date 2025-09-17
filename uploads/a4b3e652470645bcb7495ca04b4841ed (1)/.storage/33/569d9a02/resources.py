from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pydantic import BaseModel
from typing import List, Optional
import os
import aiofiles
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.resource import Resource

router = APIRouter()

class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: str  # 'file', 'link', 'repo', 'note'
    url: Optional[str] = None
    content: Optional[str] = None  # For notes
    course_id: Optional[str] = None
    topic_id: Optional[str] = None
    assignment_id: Optional[str] = None
    tags: Optional[List[str]] = []

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class ResourceResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    resource_type: str
    url: Optional[str]
    file_path: Optional[str]
    content: Optional[str]
    course_id: Optional[str]
    topic_id: Optional[str]
    assignment_id: Optional[str]
    tags: List[str]
    ai_summary: Optional[str]
    created_at: str
    updated_at: str
    last_accessed: str

@router.get("/", response_model=List[ResourceResponse])
async def get_resources(
    resource_type: Optional[str] = None,
    course_id: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Resource).where(Resource.user_id == current_user.id)
    
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)
    
    if course_id:
        query = query.where(Resource.course_id == course_id)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query = query.where(Resource.tags.overlap(tag_list))
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Resource.title.ilike(search_term),
                Resource.description.ilike(search_term),
                Resource.content.ilike(search_term)
            )
        )
    
    result = await db.execute(query.order_by(Resource.updated_at.desc()))
    resources = result.scalars().all()
    
    return [
        ResourceResponse(
            id=str(resource.id),
            title=resource.title,
            description=resource.description,
            resource_type=resource.resource_type,
            url=resource.url,
            file_path=resource.file_path,
            content=resource.content,
            course_id=str(resource.course_id) if resource.course_id else None,
            topic_id=str(resource.topic_id) if resource.topic_id else None,
            assignment_id=str(resource.assignment_id) if resource.assignment_id else None,
            tags=resource.tags or [],
            ai_summary=resource.ai_summary,
            created_at=resource.created_at.isoformat(),
            updated_at=resource.updated_at.isoformat(),
            last_accessed=resource.last_accessed.isoformat()
        )
        for resource in resources
    ]

@router.post("/", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource = Resource(
        user_id=current_user.id,
        title=resource_data.title,
        description=resource_data.description,
        resource_type=resource_data.resource_type,
        url=resource_data.url,
        content=resource_data.content,
        course_id=resource_data.course_id,
        topic_id=resource_data.topic_id,
        assignment_id=resource_data.assignment_id,
        tags=resource_data.tags or []
    )
    
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    
    return ResourceResponse(
        id=str(resource.id),
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        url=resource.url,
        file_path=resource.file_path,
        content=resource.content,
        course_id=str(resource.course_id) if resource.course_id else None,
        topic_id=str(resource.topic_id) if resource.topic_id else None,
        assignment_id=str(resource.assignment_id) if resource.assignment_id else None,
        tags=resource.tags or [],
        ai_summary=resource.ai_summary,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat(),
        last_accessed=resource.last_accessed.isoformat()
    )

@router.post("/upload", response_model=ResourceResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    course_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create resource record
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
    
    resource = Resource(
        user_id=current_user.id,
        title=title or file.filename,
        description=description,
        resource_type="file",
        file_path=file_path,
        course_id=course_id,
        topic_id=topic_id,
        assignment_id=assignment_id,
        tags=tag_list,
        metadata={"original_filename": file.filename, "content_type": file.content_type}
    )
    
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    
    return ResourceResponse(
        id=str(resource.id),
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        url=resource.url,
        file_path=resource.file_path,
        content=resource.content,
        course_id=str(resource.course_id) if resource.course_id else None,
        topic_id=str(resource.topic_id) if resource.topic_id else None,
        assignment_id=str(resource.assignment_id) if resource.assignment_id else None,
        tags=resource.tags or [],
        ai_summary=resource.ai_summary,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat(),
        last_accessed=resource.last_accessed.isoformat()
    )

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.user_id == current_user.id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Update last accessed time
    resource.last_accessed = resource.updated_at
    await db.commit()
    
    return ResourceResponse(
        id=str(resource.id),
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        url=resource.url,
        file_path=resource.file_path,
        content=resource.content,
        course_id=str(resource.course_id) if resource.course_id else None,
        topic_id=str(resource.topic_id) if resource.topic_id else None,
        assignment_id=str(resource.assignment_id) if resource.assignment_id else None,
        tags=resource.tags or [],
        ai_summary=resource.ai_summary,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat(),
        last_accessed=resource.last_accessed.isoformat()
    )

@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    resource_data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.user_id == current_user.id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Update fields
    update_data = resource_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    await db.commit()
    await db.refresh(resource)
    
    return ResourceResponse(
        id=str(resource.id),
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        url=resource.url,
        file_path=resource.file_path,
        content=resource.content,
        course_id=str(resource.course_id) if resource.course_id else None,
        topic_id=str(resource.topic_id) if resource.topic_id else None,
        assignment_id=str(resource.assignment_id) if resource.assignment_id else None,
        tags=resource.tags or [],
        ai_summary=resource.ai_summary,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat(),
        last_accessed=resource.last_accessed.isoformat()
    )

@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.user_id == current_user.id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Delete file if it exists
    if resource.file_path and os.path.exists(resource.file_path):
        os.remove(resource.file_path)
    
    await db.delete(resource)
    await db.commit()
    
    return {"message": "Resource deleted successfully"}

@router.get("/search/fulltext")
async def search_resources(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full-text search across resources"""
    search_term = f"%{q}%"
    
    result = await db.execute(
        select(Resource)
        .where(
            and_(
                Resource.user_id == current_user.id,
                or_(
                    Resource.title.ilike(search_term),
                    Resource.description.ilike(search_term),
                    Resource.content.ilike(search_term),
                    Resource.ai_summary.ilike(search_term)
                )
            )
        )
        .order_by(Resource.updated_at.desc())
        .limit(20)
    )
    resources = result.scalars().all()
    
    return [
        {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description,
            "resource_type": resource.resource_type,
            "tags": resource.tags or [],
            "relevance_score": 1.0  # Placeholder for actual relevance scoring
        }
        for resource in resources
    ]
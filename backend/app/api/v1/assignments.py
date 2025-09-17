from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.assignment import Assignment
from app.models.course import Course

router = APIRouter()

class AssignmentCreate(BaseModel):
    course_id: str
    topic_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    points_possible: Optional[float] = None

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    points_possible: Optional[float] = None
    status: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: str
    course_id: str
    topic_id: Optional[str]
    title: str
    description: Optional[str]
    due_date: Optional[str]
    points_possible: Optional[float]
    status: str
    created_at: str
    updated_at: str

@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(
    course_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Build query
    query = select(Assignment).join(Course).where(Course.user_id == current_user.id)
    
    if course_id:
        query = query.where(Assignment.course_id == course_id)
    
    if status:
        query = query.where(Assignment.status == status)
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    
    return [
        AssignmentResponse(
            id=str(assignment.id),
            course_id=str(assignment.course_id),
            topic_id=str(assignment.topic_id) if assignment.topic_id else None,
            title=assignment.title,
            description=assignment.description,
            due_date=assignment.due_date.isoformat() if assignment.due_date else None,
            points_possible=float(assignment.points_possible) if assignment.points_possible else None,
            status=assignment.status,
            created_at=assignment.created_at.isoformat(),
            updated_at=assignment.updated_at.isoformat()
        )
        for assignment in assignments
    ]

@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify course belongs to user
    result = await db.execute(
        select(Course).where(Course.id == assignment_data.course_id, Course.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    assignment = Assignment(
        course_id=assignment_data.course_id,
        topic_id=assignment_data.topic_id,
        title=assignment_data.title,
        description=assignment_data.description,
        due_date=assignment_data.due_date,
        points_possible=assignment_data.points_possible
    )
    
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentResponse(
        id=str(assignment.id),
        course_id=str(assignment.course_id),
        topic_id=str(assignment.topic_id) if assignment.topic_id else None,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        points_possible=float(assignment.points_possible) if assignment.points_possible else None,
        status=assignment.status,
        created_at=assignment.created_at.isoformat(),
        updated_at=assignment.updated_at.isoformat()
    )

@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Assignment)
        .join(Course)
        .where(Assignment.id == assignment_id, Course.user_id == current_user.id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return AssignmentResponse(
        id=str(assignment.id),
        course_id=str(assignment.course_id),
        topic_id=str(assignment.topic_id) if assignment.topic_id else None,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        points_possible=float(assignment.points_possible) if assignment.points_possible else None,
        status=assignment.status,
        created_at=assignment.created_at.isoformat(),
        updated_at=assignment.updated_at.isoformat()
    )

@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Assignment)
        .join(Course)
        .where(Assignment.id == assignment_id, Course.user_id == current_user.id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Update fields
    update_data = assignment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentResponse(
        id=str(assignment.id),
        course_id=str(assignment.course_id),
        topic_id=str(assignment.topic_id) if assignment.topic_id else None,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date.isoformat() if assignment.due_date else None,
        points_possible=float(assignment.points_possible) if assignment.points_possible else None,
        status=assignment.status,
        created_at=assignment.created_at.isoformat(),
        updated_at=assignment.updated_at.isoformat()
    )

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Assignment)
        .join(Course)
        .where(Assignment.id == assignment_id, Course.user_id == current_user.id)
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    await db.delete(assignment)
    await db.commit()
    
    return {"message": "Assignment deleted successfully"}
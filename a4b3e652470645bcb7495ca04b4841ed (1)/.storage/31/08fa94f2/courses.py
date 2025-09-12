from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.course import Course, Topic
from app.models.assignment import Assignment
from app.models.resource import Resource

router = APIRouter()

class CourseCreate(BaseModel):
    name: str
    code: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None
    instructor: Optional[str] = None
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None
    instructor: Optional[str] = None
    description: Optional[str] = None

class TopicResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    order_index: int

class AssignmentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    due_date: Optional[str]
    status: str

class CourseResponse(BaseModel):
    id: str
    name: str
    code: Optional[str]
    semester: Optional[str]
    year: Optional[int]
    instructor: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str

class CourseDetailResponse(CourseResponse):
    topics: List[TopicResponse]
    assignments: List[AssignmentResponse]

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course).where(Course.user_id == current_user.id)
    )
    courses = result.scalars().all()
    
    return [
        CourseResponse(
            id=str(course.id),
            name=course.name,
            code=course.code,
            semester=course.semester,
            year=course.year,
            instructor=course.instructor,
            description=course.description,
            created_at=course.created_at.isoformat(),
            updated_at=course.updated_at.isoformat()
        )
        for course in courses
    ]

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = Course(
        user_id=current_user.id,
        name=course_data.name,
        code=course_data.code,
        semester=course_data.semester,
        year=course_data.year,
        instructor=course_data.instructor,
        description=course_data.description
    )
    
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    return CourseResponse(
        id=str(course.id),
        name=course.name,
        code=course.code,
        semester=course.semester,
        year=course.year,
        instructor=course.instructor,
        description=course.description,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat()
    )

@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.topics),
            selectinload(Course.assignments)
        )
        .where(Course.id == course_id, Course.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return CourseDetailResponse(
        id=str(course.id),
        name=course.name,
        code=course.code,
        semester=course.semester,
        year=course.year,
        instructor=course.instructor,
        description=course.description,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat(),
        topics=[
            TopicResponse(
                id=str(topic.id),
                name=topic.name,
                description=topic.description,
                order_index=topic.order_index
            )
            for topic in course.topics
        ],
        assignments=[
            AssignmentResponse(
                id=str(assignment.id),
                title=assignment.title,
                description=assignment.description,
                due_date=assignment.due_date.isoformat() if assignment.due_date else None,
                status=assignment.status
            )
            for assignment in course.assignments
        ]
    )

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Update fields
    update_data = course_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    await db.commit()
    await db.refresh(course)
    
    return CourseResponse(
        id=str(course.id),
        name=course.name,
        code=course.code,
        semester=course.semester,
        year=course.year,
        instructor=course.instructor,
        description=course.description,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat()
    )

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    await db.delete(course)
    await db.commit()
    
    return {"message": "Course deleted successfully"}

@router.get("/{course_id}/live-map")
async def get_course_live_map(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get live map data for course visualization"""
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.topics),
            selectinload(Course.assignments),
            selectinload(Course.resources)
        )
        .where(Course.id == course_id, Course.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Build live map structure
    live_map = {
        "course": {
            "id": str(course.id),
            "name": course.name,
            "code": course.code
        },
        "topics": [
            {
                "id": str(topic.id),
                "name": topic.name,
                "description": topic.description,
                "order_index": topic.order_index
            }
            for topic in course.topics
        ],
        "assignments": [
            {
                "id": str(assignment.id),
                "title": assignment.title,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "status": assignment.status,
                "topic_id": str(assignment.topic_id) if assignment.topic_id else None
            }
            for assignment in course.assignments
        ],
        "resources": [
            {
                "id": str(resource.id),
                "title": resource.title,
                "type": resource.resource_type,
                "tags": resource.tags or [],
                "topic_id": str(resource.topic_id) if resource.topic_id else None,
                "assignment_id": str(resource.assignment_id) if resource.assignment_id else None
            }
            for resource in course.resources
        ]
    }
    
    return live_map
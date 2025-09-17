"""
Canvas LMS Integration
Syncs courses, assignments, grades, announcements, and discussions
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.integration_engine import (
    BaseIntegration, IntegrationType, IntegrationCapability, 
    SyncResult, SyncStatus, IntegrationMetadata, register_integration
)
from app.models import Course, Assignment

class CanvasConfig(BaseModel):
    """Canvas API configuration"""
    api_url: str  # e.g., "https://university.instructure.com/api/v1"
    access_token: str
    user_id: Optional[str] = None

class CanvasCourse(BaseModel):
    """Canvas course data"""
    id: int
    name: str
    course_code: str
    workflow_state: str
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    enrollments: List[Dict[str, Any]] = []

class CanvasAssignment(BaseModel):
    """Canvas assignment data"""
    id: int
    name: str
    description: Optional[str]
    due_at: Optional[datetime]
    points_possible: Optional[float]
    course_id: int
    html_url: str
    submission_types: List[str] = []
    workflow_state: str

@register_integration
class CanvasIntegration(BaseIntegration[CanvasCourse]):
    """
    Canvas LMS integration for academic workflow management
    """
    
    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.LMS
    
    @property
    def supported_capabilities(self) -> List[IntegrationCapability]:
        return [
            IntegrationCapability.READ,
            IntegrationCapability.SEARCH,
            IntegrationCapability.GRAPH,  # Courses -> Assignments relationships
        ]
    
    @property
    def service_name(self) -> str:
        return "Canvas LMS"
    
    def __init__(self, integration_id: str, config: Dict[str, Any]):
        super().__init__(integration_id, config)
        if config:  # Only validate config if it's provided
            self.canvas_config = CanvasConfig(**config)
        else:
            self.canvas_config = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.canvas_config.access_token}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make Canvas API request"""
        session = await self._get_session()
        url = f"{self.canvas_config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with session.get(url, params=params or {}) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"Canvas API request failed: {str(e)}")
            raise
    
    async def _get_paginated_data(self, endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all pages of data from Canvas API"""
        all_data = []
        page_params = (params or {}).copy()
        page_params.update({"per_page": 100})
        
        while True:
            try:
                data = await self._make_request(endpoint, page_params)
                if isinstance(data, list):
                    all_data.extend(data)
                    if len(data) < 100:  # Last page
                        break
                    # Canvas uses page-based pagination
                    current_page = page_params.get("page", 1)
                    page_params["page"] = current_page + 1
                else:
                    all_data.append(data)
                    break
            except Exception as e:
                self.logger.error(f"Error fetching paginated data: {str(e)}")
                break
        
        return all_data
    
    async def authenticate(self) -> bool:
        """Test Canvas API authentication"""
        try:
            await self._make_request("/users/self")
            return True
        except Exception as e:
            self.logger.error(f"Canvas authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Canvas connection"""
        return await self.authenticate()
    
    async def get_courses(self) -> List[CanvasCourse]:
        """Get all courses for the user"""
        try:
            courses_data = await self._get_paginated_data(
                "/courses",
                {
                    "enrollment_state": "active",
                    "include": ["enrollments", "term"]
                }
            )
            
            courses = []
            for course_data in courses_data:
                try:
                    # Parse dates
                    start_at = None
                    end_at = None
                    if course_data.get("start_at"):
                        start_at = datetime.fromisoformat(course_data["start_at"].replace('Z', '+00:00'))
                    if course_data.get("end_at"):
                        end_at = datetime.fromisoformat(course_data["end_at"].replace('Z', '+00:00'))
                    
                    course = CanvasCourse(
                        id=course_data["id"],
                        name=course_data["name"],
                        course_code=course_data.get("course_code", ""),
                        workflow_state=course_data.get("workflow_state", "available"),
                        start_at=start_at,
                        end_at=end_at,
                        enrollments=course_data.get("enrollments", [])
                    )
                    courses.append(course)
                except Exception as e:
                    self.logger.warning(f"Failed to parse course {course_data.get('id', 'unknown')}: {str(e)}")
            
            return courses
        except Exception as e:
            self.logger.error(f"Failed to fetch courses: {str(e)}")
            return []
    
    async def get_assignments(self, course_id: int) -> List[CanvasAssignment]:
        """Get assignments for a specific course"""
        try:
            assignments_data = await self._get_paginated_data(
                f"/courses/{course_id}/assignments"
            )
            
            assignments = []
            for assignment_data in assignments_data:
                try:
                    # Parse due date
                    due_at = None
                    if assignment_data.get("due_at"):
                        due_at = datetime.fromisoformat(assignment_data["due_at"].replace('Z', '+00:00'))
                    
                    assignment = CanvasAssignment(
                        id=assignment_data["id"],
                        name=assignment_data["name"],
                        description=assignment_data.get("description"),
                        due_at=due_at,
                        points_possible=assignment_data.get("points_possible"),
                        course_id=course_id,
                        html_url=assignment_data.get("html_url", ""),
                        submission_types=assignment_data.get("submission_types", []),
                        workflow_state=assignment_data.get("workflow_state", "published")
                    )
                    assignments.append(assignment)
                except Exception as e:
                    self.logger.warning(f"Failed to parse assignment {assignment_data.get('id', 'unknown')}: {str(e)}")
            
            return assignments
        except Exception as e:
            self.logger.error(f"Failed to fetch assignments for course {course_id}: {str(e)}")
            return []
    
    async def sync_data(self, db: Session, user_id: str, full_sync: bool = False) -> SyncResult:
        """Sync Canvas data to local database"""
        try:
            result = SyncResult(status=SyncStatus.IN_PROGRESS)
            
            # Fetch courses
            self.logger.info(f"Syncing Canvas courses for user {user_id}")
            canvas_courses = await self.get_courses()
            
            for canvas_course in canvas_courses:
                try:
                    # Check if course exists
                    existing_course = db.query(Course).filter(
                        Course.user_id == user_id,
                        Course.external_id == str(canvas_course.id)
                    ).first()
                    
                    if existing_course:
                        # Update existing course
                        existing_course.name = canvas_course.name
                        existing_course.course_code = canvas_course.course_code
                        existing_course.start_date = canvas_course.start_at
                        existing_course.end_date = canvas_course.end_at
                        existing_course.is_active = canvas_course.workflow_state == "available"
                        result.items_updated += 1
                    else:
                        # Create new course
                        new_course = Course(
                            user_id=user_id,
                            name=canvas_course.name,
                            course_code=canvas_course.course_code,
                            description=f"Synced from Canvas LMS",
                            start_date=canvas_course.start_at,
                            end_date=canvas_course.end_at,
                            is_active=canvas_course.workflow_state == "available",
                            external_id=str(canvas_course.id),
                            external_source="canvas"
                        )
                        db.add(new_course)
                        result.items_created += 1
                    
                    db.flush()  # Get the course ID
                    course_obj = existing_course or new_course
                    
                    # Sync assignments for this course
                    self.logger.info(f"Syncing assignments for course {canvas_course.name}")
                    canvas_assignments = await self.get_assignments(canvas_course.id)
                    
                    for canvas_assignment in canvas_assignments:
                        try:
                            existing_assignment = db.query(Assignment).filter(
                                Assignment.course_id == course_obj.id,
                                Assignment.external_id == str(canvas_assignment.id)
                            ).first()
                            
                            if existing_assignment:
                                # Update existing assignment
                                existing_assignment.title = canvas_assignment.name
                                existing_assignment.description = canvas_assignment.description or ""
                                existing_assignment.due_date = canvas_assignment.due_at
                                existing_assignment.points_possible = canvas_assignment.points_possible
                                existing_assignment.is_active = canvas_assignment.workflow_state == "published"
                                result.items_updated += 1
                            else:
                                # Create new assignment
                                new_assignment = Assignment(
                                    course_id=course_obj.id,
                                    title=canvas_assignment.name,
                                    description=canvas_assignment.description or "",
                                    due_date=canvas_assignment.due_at,
                                    points_possible=canvas_assignment.points_possible,
                                    is_active=canvas_assignment.workflow_state == "published",
                                    external_id=str(canvas_assignment.id),
                                    external_source="canvas",
                                    external_url=canvas_assignment.html_url
                                )
                                db.add(new_assignment)
                                result.items_created += 1
                            
                            result.items_processed += 1
                            
                        except Exception as e:
                            self.logger.error(f"Failed to sync assignment {canvas_assignment.id}: {str(e)}")
                            result.items_failed += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to sync course {canvas_course.id}: {str(e)}")
                    result.items_failed += 1
            
            db.commit()
            
            if result.items_failed > 0:
                result.status = SyncStatus.PARTIAL
            else:
                result.status = SyncStatus.SUCCESS
            
            self.logger.info(f"Canvas sync completed: {result.items_created} created, {result.items_updated} updated, {result.items_failed} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"Canvas sync failed: {str(e)}")
            db.rollback()
            return SyncResult(
                status=SyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_relationships(self, item_id: str) -> List[str]:
        """Get related items for knowledge graph"""
        # For Canvas: courses relate to assignments, assignments relate to submissions
        # This supports your knowledge graph vision
        relationships = []
        
        try:
            # If it's a course, get its assignments
            if item_id.startswith("course_"):
                course_id = item_id.replace("course_", "")
                assignments = await self.get_assignments(int(course_id))
                relationships.extend([f"assignment_{a.id}" for a in assignments])
        except Exception as e:
            self.logger.error(f"Failed to get relationships for {item_id}: {str(e)}")
        
        return relationships
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[CanvasCourse]:
        """Search Canvas courses and content"""
        try:
            courses = await self.get_courses()
            
            # Simple text search for now
            query_lower = query.lower()
            matching_courses = [
                course for course in courses 
                if query_lower in course.name.lower() or 
                   query_lower in course.course_code.lower()
            ]
            
            return matching_courses
        except Exception as e:
            self.logger.error(f"Canvas search failed: {str(e)}")
            return []
    
    def extract_metadata(self, item: Any) -> IntegrationMetadata:
        """Extract metadata for knowledge graph"""
        if isinstance(item, CanvasCourse):
            return IntegrationMetadata(
                source_id=f"course_{item.id}",
                source_type="course",
                source_url=f"{self.canvas_config.api_url.replace('/api/v1', '')}/courses/{item.id}",
                last_modified=datetime.now(timezone.utc),
                relationships=[],  # Will be populated by get_relationships
                tags=["canvas", "course", item.course_code],
                additional_data={
                    "course_code": item.course_code,
                    "workflow_state": item.workflow_state,
                    "start_at": item.start_at.isoformat() if item.start_at else None,
                    "end_at": item.end_at.isoformat() if item.end_at else None
                }
            )
        elif isinstance(item, CanvasAssignment):
            return IntegrationMetadata(
                source_id=f"assignment_{item.id}",
                source_type="assignment",
                source_url=item.html_url,
                last_modified=datetime.now(timezone.utc),
                relationships=[f"course_{item.course_id}"],
                tags=["canvas", "assignment"] + item.submission_types,
                additional_data={
                    "due_at": item.due_at.isoformat() if item.due_at else None,
                    "points_possible": item.points_possible,
                    "submission_types": item.submission_types
                }
            )
        
        return super().extract_metadata(item)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
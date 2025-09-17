import asyncio
import aiohttp
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PluginClass:
    """Canvas LMS Integration Plugin"""
    
    def __init__(self):
        self.name = "canvas-integration"
        self.version = "1.0.0"
        self.session = None
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the plugin with configuration"""
        self.config = config
        self.canvas_url = config.get("canvas_url", "").rstrip("/")
        self.access_token = config.get("access_token")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """Check if Canvas API is accessible"""
        try:
            if not self.session:
                return False
                
            async with self.session.get(f"{self.canvas_url}/api/v1/users/self") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Canvas health check failed: {e}")
            return False
    
    async def sync_courses(self, user_id: str) -> Dict[str, Any]:
        """Synchronize courses from Canvas"""
        try:
            courses = []
            url = f"{self.canvas_url}/api/v1/courses"
            
            async with self.session.get(url, params={"enrollment_state": "active"}) as response:
                if response.status == 200:
                    canvas_courses = await response.json()
                    
                    for course_data in canvas_courses:
                        course = {
                            "external_id": str(course_data.get("id")),
                            "name": course_data.get("name", ""),
                            "code": course_data.get("course_code", ""),
                            "semester": self._extract_semester(course_data),
                            "instructor": await self._get_course_instructor(course_data.get("id")),
                            "description": course_data.get("public_description", ""),
                            "canvas_url": course_data.get("html_url", "")
                        }
                        courses.append(course)
                    
                    logger.info(f"Synced {len(courses)} courses from Canvas")
                    return {
                        "success": True,
                        "courses": courses,
                        "sync_count": len(courses)
                    }
                else:
                    logger.error(f"Failed to fetch courses: {response.status}")
                    return {
                        "success": False,
                        "error": f"Canvas API error: {response.status}",
                        "courses": [],
                        "sync_count": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing courses: {e}")
            return {
                "success": False,
                "error": str(e),
                "courses": [],
                "sync_count": 0
            }
    
    async def sync_assignments(self, course_id: str, user_id: str) -> Dict[str, Any]:
        """Synchronize assignments for a specific course"""
        try:
            assignments = []
            url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignments"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    canvas_assignments = await response.json()
                    
                    for assignment_data in canvas_assignments:
                        assignment = {
                            "external_id": str(assignment_data.get("id")),
                            "title": assignment_data.get("name", ""),
                            "description": assignment_data.get("description", ""),
                            "due_date": self._parse_canvas_date(assignment_data.get("due_at")),
                            "points_possible": assignment_data.get("points_possible"),
                            "status": "active" if not assignment_data.get("locked_for_user") else "locked",
                            "canvas_url": assignment_data.get("html_url", ""),
                            "submission_types": assignment_data.get("submission_types", [])
                        }
                        assignments.append(assignment)
                    
                    logger.info(f"Synced {len(assignments)} assignments for course {course_id}")
                    return {
                        "success": True,
                        "assignments": assignments,
                        "sync_count": len(assignments)
                    }
                else:
                    logger.error(f"Failed to fetch assignments: {response.status}")
                    return {
                        "success": False,
                        "error": f"Canvas API error: {response.status}",
                        "assignments": [],
                        "sync_count": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing assignments: {e}")
            return {
                "success": False,
                "error": str(e),
                "assignments": [],
                "sync_count": 0
            }
    
    async def get_grades(self, course_id: str, user_id: str) -> Dict[str, Any]:
        """Fetch grades for assignments in a course"""
        try:
            grades = []
            url = f"{self.canvas_url}/api/v1/courses/{course_id}/assignments"
            
            # Get assignments with submissions
            params = {"include": ["submission"], "per_page": 100}
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    assignments = await response.json()
                    
                    for assignment in assignments:
                        submission = assignment.get("submission")
                        if submission:
                            grade_info = {
                                "assignment_id": str(assignment.get("id")),
                                "assignment_name": assignment.get("name"),
                                "score": submission.get("score"),
                                "grade": submission.get("grade"),
                                "points_possible": assignment.get("points_possible"),
                                "graded_at": self._parse_canvas_date(submission.get("graded_at")),
                                "submitted_at": self._parse_canvas_date(submission.get("submitted_at")),
                                "workflow_state": submission.get("workflow_state")
                            }
                            grades.append(grade_info)
                    
                    return {
                        "success": True,
                        "grades": grades
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Canvas API error: {response.status}",
                        "grades": []
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching grades: {e}")
            return {
                "success": False,
                "error": str(e),
                "grades": []
            }
    
    def _extract_semester(self, course_data: Dict[str, Any]) -> str:
        """Extract semester information from course data"""
        term = course_data.get("enrollment_term_id")
        start_date = course_data.get("start_at")
        
        if start_date:
            date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            month = date.month
            year = date.year
            
            if month >= 8:  # Fall semester
                return f"Fall {year}"
            elif month >= 5:  # Summer semester
                return f"Summer {year}"
            else:  # Spring semester
                return f"Spring {year}"
        
        return "Unknown"
    
    async def _get_course_instructor(self, course_id: str) -> str:
        """Get the primary instructor for a course"""
        try:
            url = f"{self.canvas_url}/api/v1/courses/{course_id}/users"
            params = {"enrollment_type": ["teacher"], "per_page": 1}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    users = await response.json()
                    if users:
                        user = users[0]
                        return user.get("name", "Unknown Instructor")
        except Exception as e:
            logger.error(f"Error fetching instructor for course {course_id}: {e}")
        
        return "Unknown Instructor"
    
    def _parse_canvas_date(self, date_str: str) -> str:
        """Parse Canvas date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Canvas dates are in ISO format with Z suffix
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.isoformat()
        except (ValueError, TypeError):
            return None
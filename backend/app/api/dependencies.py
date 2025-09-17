"""
Common dependencies for API endpoints
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

# Re-export for convenience
__all__ = ["get_db", "get_current_user"]
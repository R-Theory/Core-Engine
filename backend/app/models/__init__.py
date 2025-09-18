# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .course import Course, Topic
from .assignment import Assignment
from .resource import Resource
from .plugin import Plugin, UserPluginConfig
from .workflow import Workflow, WorkflowExecution
from .agent import AIAgent, AgentInteraction
from .user_profile import UserProfile, UserProfileDocument, UserIntegration, UserCredential, UserPreference
from .ai_context import UserAIContext, UserContextDocument, AIConversation, AIContextTemplate

__all__ = [
    "User",
    "Course",
    "Topic",
    "Assignment",
    "Resource",
    "Plugin",
    "UserPluginConfig",
    "Workflow",
    "WorkflowExecution",
    "AIAgent",
    "AgentInteraction",
    "UserProfile",
    "UserProfileDocument",
    "UserIntegration",
    "UserCredential",
    "UserPreference",
    "UserAIContext",
    "UserContextDocument",
    "AIConversation",
    "AIContextTemplate"
]
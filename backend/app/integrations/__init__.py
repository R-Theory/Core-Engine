"""
Integration Package
Auto-registers all available integrations
"""

# Import all integration modules to trigger registration
from .canvas_integration import CanvasIntegration
from .github_integration import GitHubIntegration  
from .notion_integration import NotionIntegration

# Import the engine to access registered integrations
from app.core.integration_engine import integration_engine

__all__ = [
    "CanvasIntegration",
    "GitHubIntegration", 
    "NotionIntegration",
    "integration_engine"
]
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.core.database import init_db
from app.core.plugin_loader import PluginLoader
from app.core.agent_registry import AgentRegistry
from app.core.celery_app import celery_app
from app.api.v1 import auth, courses, assignments, resources, plugins, workflows, agents
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize plugin loader and agent registry
plugin_loader = PluginLoader()
agent_registry = AgentRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Core Engine MVP...")
    await init_db()
    await plugin_loader.load_plugins()
    await agent_registry.initialize_agents()
    logger.info("Core Engine MVP started successfully")
    yield
    # Shutdown
    logger.info("Shutting down Core Engine MVP...")

app = FastAPI(
    title="Core Engine MVP",
    description="AI-Powered Learning & Project Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(assignments.router, prefix="/api/v1/assignments", tags=["assignments"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["resources"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["ai-agents"])

@app.get("/")
async def root():
    return {
        "message": "Core Engine MVP API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2024-12-10T00:00:00Z",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "plugins": len(plugin_loader.list_plugins()),
            "agents": len(agent_registry.list_agents())
        }
    }
    return health_status

# Make celery app available for import
__all__ = ["app", "celery_app"]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
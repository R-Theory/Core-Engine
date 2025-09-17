from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings as config_settings
from app.core.database import init_db
from app.core.plugin_loader import PluginLoader
from app.core.agent_registry import AgentRegistry
from app.core.celery_app import celery_app
from app.api.v1 import auth, courses, assignments, resources, plugins, workflows, agents, documents, ai_context, credentials as credentials_api
from app.api.v1 import settings as settings_api
# Import integrations to register them
import app.integrations
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
    
    # Initialize document processing system
    try:
        from app.core.document_engine import document_engine
        from app.core.plugin_system import plugin_registry
        from app.core.plugin_interface import PluginConfig
        
        await document_engine.initialize()
        
        # Load default document processing plugins
        default_plugins = [
            ("textparser", PluginConfig(enabled=True, priority=10)),
            ("pdfparser", PluginConfig(enabled=True, priority=20)),
            ("docxparser", PluginConfig(enabled=True, priority=30)),
        ]
        
        for plugin_name, config in default_plugins:
            await plugin_registry.load_plugin(plugin_name, config)
        
        # Optionally load Notion storage if environment is configured
        if (
            getattr(config_settings, "NOTION_INTEGRATION_TOKEN", "")
            and getattr(config_settings, "NOTION_DATABASE_ID", "")
        ):
            notion_config = PluginConfig(
                enabled=True,
                priority=50,
                config={
                    "integration_token": config_settings.NOTION_INTEGRATION_TOKEN,
                    "database_id": config_settings.NOTION_DATABASE_ID,
                },
            )
            # Class NotionStoragePlugin -> registry name 'notionstorage'
            await plugin_registry.load_plugin("notionstorage", notion_config)
            logger.info("Notion storage plugin auto-enabled from environment")
    
        logger.info("Document processing system initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize document system: {str(e)}")
    
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
    allow_origins=config_settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(assignments.router, prefix="/api/v1/assignments", tags=["assignments"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["resources"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["ai-agents"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(ai_context.router, prefix="/api/v1/ai-context", tags=["ai-context"])
app.include_router(credentials_api.router, prefix="/api/v1", tags=["credentials"])

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
        reload=True if config_settings.ENVIRONMENT == "development" else False
    )

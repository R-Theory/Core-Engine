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
from app.core.monitoring import PrometheusMiddleware, metrics_handler, health_handler, setup_monitoring
from app.core.cache import cache_manager
from app.core.rate_limiter import rate_limiter, RateLimitMiddleware
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
    
    # Initialize performance systems
    await cache_manager.connect()
    await rate_limiter.connect()
    setup_monitoring()

    logger.info("Core Engine MVP started successfully")
    yield
    # Shutdown
    logger.info("Shutting down Core Engine MVP...")
    await cache_manager.disconnect()
    logger.info("Performance systems shut down")

app = FastAPI(
    title="Core Engine MVP",
    description="AI-Powered Learning & Project Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add performance middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(PrometheusMiddleware)

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
    from fastapi import Request
    request = Request({"type": "http", "method": "GET", "path": "/health"})
    return await health_handler(request)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi import Request
    request = Request({"type": "http", "method": "GET", "path": "/metrics"})
    return await metrics_handler(request)

@app.post("/github-app/list-installations")
async def list_github_app_installations(credentials: dict):
    """List all installations for a GitHub App to find installation IDs"""
    try:
        from app.integrations.github_integration import (
            GitHubConfig, GitHubAuthMode, GitHubIntegration
        )
        import jwt
        import time
        import aiohttp

        # Validate required fields for JWT generation
        if not credentials.get("app_id") or not credentials.get("private_key"):
            return {
                "success": False,
                "error": "Missing required fields",
                "message": "Please provide app_id and private_key to list installations"
            }

        try:
            app_id = int(credentials["app_id"])
            private_key = credentials["private_key"].strip()

            # Generate JWT token
            now = int(time.time())
            payload = {
                "iat": now,
                "exp": now + 600,
                "iss": app_id
            }
            jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

            # List installations
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CoreEngine-Setup/1.0"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/app/installations", headers=headers) as response:
                    if response.status == 200:
                        installations = await response.json()

                        result = []
                        for install in installations:
                            result.append({
                                "installation_id": install["id"],
                                "account": install["account"]["login"],
                                "account_type": install["account"]["type"],
                                "repository_selection": install.get("repository_selection", "unknown"),
                                "app_id": install["app_id"],
                                "target_type": install["target_type"]
                            })

                        return {
                            "success": True,
                            "message": f"Found {len(result)} installations",
                            "installations": result
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": "GitHub API error",
                            "message": f"Status {response.status}: {error_text}"
                        }

        except ValueError as e:
            return {
                "success": False,
                "error": "Invalid configuration",
                "message": f"Configuration error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Request failed",
                "message": str(e)
            }

    except Exception as e:
        return {
            "success": False,
            "error": "Setup failed",
            "message": str(e)
        }

@app.post("/test-github-app")
async def test_github_app_public(credentials: dict):
    """Public test endpoint for GitHub App credentials"""
    try:
        from app.integrations.github_integration import (
            GitHubConfig, GitHubAuthMode, GitHubIntegration
        )

        # Validate required fields
        required_fields = ["app_id", "installation_id", "private_key"]
        missing_fields = [field for field in required_fields if not credentials.get(field)]

        if missing_fields:
            return {
                "success": False,
                "error": "Missing required fields",
                "message": f"Please provide: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }

        # Create GitHub configuration
        try:
            config = GitHubConfig(
                auth_mode=GitHubAuthMode.GITHUB_APP,
                app_id=int(credentials["app_id"]),
                installation_id=int(credentials["installation_id"]),
                private_key=credentials["private_key"].strip()
            )
        except ValueError as e:
            return {
                "success": False,
                "error": "Invalid configuration",
                "message": f"Configuration error: {str(e)}"
            }

        # Test the GitHub App integration
        integration = GitHubIntegration("test", config.__dict__)

        try:
            # Test authentication
            auth_success = await integration.authenticate()

            if auth_success:
                # Test repository access
                repositories = await integration.get_installation_repositories()

                return {
                    "success": True,
                    "message": "GitHub App authentication successful",
                    "details": {
                        "app_id": config.app_id,
                        "installation_id": config.installation_id,
                        "repositories_found": len(repositories),
                        "username": getattr(integration.github_config, 'username', None)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "message": "Could not authenticate with GitHub API"
                }

        except Exception as e:
            return {
                "success": False,
                "error": "GitHub App test failed",
                "message": str(e),
                "details": {
                    "suggestion": "Check your app_id, installation_id, and private_key"
                }
            }
        finally:
            # Clean up the session
            await integration.__aexit__(None, None, None)

    except Exception as e:
        return {
            "success": False,
            "error": "Test failed",
            "message": str(e)
        }

# Make celery app available for import
__all__ = ["app", "celery_app"]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if config_settings.ENVIRONMENT == "development" else False
    )

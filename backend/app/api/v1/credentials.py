from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.plugin import Plugin as PluginModel, UserPluginConfig
from app.core.crypto import encrypt_dict, decrypt_dict
from app.core.config import settings

router = APIRouter()

# Define supported credential providers
CREDENTIAL_PROVIDERS = {
    "notion": {
        "name": "Notion",
        "description": "Document storage and knowledge management",
        "plugin_name": "notion-storage",
        "fields": ["integration_token", "database_id"],
        "test_endpoint": True
    },
    "openai": {
        "name": "OpenAI",
        "description": "GPT models for AI assistance", 
        "plugin_name": "openai-provider",
        "fields": ["api_key"],
        "test_endpoint": True
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "description": "Claude AI models for advanced reasoning",
        "plugin_name": "anthropic-provider", 
        "fields": ["api_key"],
        "test_endpoint": True
    },
    "github": {
        "name": "GitHub",
        "description": "Code repository and version control (OAuth mode)",
        "plugin_name": "github-provider",
        "fields": ["access_token"],
        "test_endpoint": True,
        "auth_mode": "oauth"
    },
    "github_app": {
        "name": "GitHub App",
        "description": "GitHub App with installation-based permissions",
        "plugin_name": "github-provider", 
        "fields": ["app_id", "private_key", "installation_id"],
        "test_endpoint": True,
        "auth_mode": "app"
    },
    "canvas": {
        "name": "Canvas LMS", 
        "description": "Learning management system integration",
        "plugin_name": "canvas-provider",
        "fields": ["api_key", "base_url"],
        "test_endpoint": False
    }
}

class CredentialsRequest(BaseModel):
    credentials: Dict[str, str] = {}

class CredentialsResponse(BaseModel):
    configured: bool
    plugin_id: Optional[str] = None
    last_updated: Optional[str] = None
    provider: Optional[str] = None

# Legacy models for backward compatibility
class NotionCredentialsRequest(BaseModel):
    integration_token: str
    database_id: str

class NotionCredentialsResponse(BaseModel):
    configured: bool
    plugin_id: Optional[str] = None
    last_updated: Optional[str] = None

async def _ensure_notion_plugin(db: AsyncSession) -> PluginModel:
    notion_plugin_name = "notion-storage"
    result = await db.execute(select(PluginModel).where(PluginModel.name == notion_plugin_name))
    plugin = result.scalar_one_or_none()
    if not plugin:
        plugin = PluginModel(
            name=notion_plugin_name,
            version="1.0.0",
            manifest={
                "name": "Notion Storage",
                "version": "1.0.0",
                "description": "Store documents as pages in Notion",
                "category": "storage",
                "capabilities": ["store", "read", "search"],
            },
            status="active",
        )
        db.add(plugin)
        await db.commit()
        await db.refresh(plugin)
    return plugin

@router.get("/credentials/notion", response_model=NotionCredentialsResponse)
async def get_notion_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PluginModel).where(PluginModel.name == "notion-storage"))
    plugin = result.scalar_one_or_none()
    if not plugin:
        return NotionCredentialsResponse(configured=False)

    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id,
        )
    )
    user_config = result.scalar_one_or_none()
    if not user_config or not user_config.credentials:
        return NotionCredentialsResponse(configured=False, plugin_id=str(plugin.id))

    return NotionCredentialsResponse(
        configured=True,
        plugin_id=str(plugin.id),
        last_updated=str(user_config.updated_at) if user_config.updated_at else None,
    )

@router.post("/credentials/notion", response_model=NotionCredentialsResponse)
async def set_notion_credentials(
    payload: NotionCredentialsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plugin = await _ensure_notion_plugin(db)

    # Get or create user config
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id,
        )
    )
    user_cfg = result.scalar_one_or_none()

    encrypted = encrypt_dict(
        {
            "integration_token": payload.integration_token,
            "database_id": payload.database_id,
        },
        settings.SECRET_KEY,
    )

    if user_cfg:
        user_cfg.credentials = encrypted
        user_cfg.is_active = True
    else:
        user_cfg = UserPluginConfig(
            user_id=current_user.id,
            plugin_id=plugin.id,
            config={},
            credentials=encrypted,
            is_active=True,
        )
        db.add(user_cfg)

    await db.commit()
    await db.refresh(user_cfg)

    return NotionCredentialsResponse(configured=True, plugin_id=str(plugin.id), last_updated=str(user_cfg.updated_at) if user_cfg.updated_at else None)

# Generic credential endpoints for modular provider system

async def _ensure_provider_plugin(db: AsyncSession, provider_id: str) -> PluginModel:
    """Ensure a plugin exists for the given provider"""
    provider_config = CREDENTIAL_PROVIDERS.get(provider_id)
    if not provider_config:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not supported")
    
    plugin_name = provider_config["plugin_name"]
    result = await db.execute(select(PluginModel).where(PluginModel.name == plugin_name))
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        plugin = PluginModel(
            name=plugin_name,
            version="1.0.0",
            manifest={
                "name": provider_config["name"],
                "version": "1.0.0", 
                "description": provider_config["description"],
                "category": "credential-provider",
                "capabilities": ["authenticate"],
            },
            status="active",
        )
        db.add(plugin)
        await db.commit()
        await db.refresh(plugin)
    
    return plugin

@router.get("/credentials/{provider_id}", response_model=CredentialsResponse)
async def get_provider_credentials(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get credentials for a specific provider"""
    if provider_id not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not supported")
    
    try:
        plugin = await _ensure_provider_plugin(db, provider_id)
        
        result = await db.execute(
            select(UserPluginConfig).where(
                UserPluginConfig.user_id == current_user.id,
                UserPluginConfig.plugin_id == plugin.id,
            )
        )
        user_config = result.scalar_one_or_none()
        
        if not user_config or not user_config.credentials:
            return CredentialsResponse(
                configured=False,
                plugin_id=str(plugin.id),
                provider=provider_id
            )

        return CredentialsResponse(
            configured=True,
            plugin_id=str(plugin.id),
            last_updated=str(user_config.updated_at) if user_config.updated_at else None,
            provider=provider_id
        )
    except Exception as e:
        # Return unconfigured status for providers that don't have backend support yet
        return CredentialsResponse(
            configured=False,
            provider=provider_id
        )

@router.post("/credentials/{provider_id}", response_model=CredentialsResponse)
async def set_provider_credentials(
    provider_id: str,
    credentials: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set credentials for a specific provider"""
    if provider_id not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not supported")
    
    provider_config = CREDENTIAL_PROVIDERS[provider_id]
    
    # Validate required fields
    for field in provider_config["fields"]:
        if field not in credentials:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required field: {field}"
            )
    
    try:
        plugin = await _ensure_provider_plugin(db, provider_id)
        
        # Get or create user config
        result = await db.execute(
            select(UserPluginConfig).where(
                UserPluginConfig.user_id == current_user.id,
                UserPluginConfig.plugin_id == plugin.id,
            )
        )
        user_cfg = result.scalar_one_or_none()

        # Encrypt credentials
        encrypted = encrypt_dict(credentials, settings.SECRET_KEY)

        if user_cfg:
            user_cfg.credentials = encrypted
            user_cfg.is_active = True
        else:
            user_cfg = UserPluginConfig(
                user_id=current_user.id,
                plugin_id=plugin.id,
                config={},
                credentials=encrypted,
                is_active=True,
            )
            db.add(user_cfg)

        await db.commit()
        await db.refresh(user_cfg)

        return CredentialsResponse(
            configured=True,
            plugin_id=str(plugin.id),
            last_updated=str(user_cfg.updated_at) if user_cfg.updated_at else None,
            provider=provider_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save credentials: {str(e)}")

@router.delete("/credentials/{provider_id}")
async def delete_provider_credentials(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete credentials for a specific provider"""
    if provider_id not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not supported")
    
    try:
        plugin = await _ensure_provider_plugin(db, provider_id)
        
        result = await db.execute(
            select(UserPluginConfig).where(
                UserPluginConfig.user_id == current_user.id,
                UserPluginConfig.plugin_id == plugin.id,
            )
        )
        user_cfg = result.scalar_one_or_none()
        
        if user_cfg:
            await db.delete(user_cfg)
            await db.commit()
        
        return {"success": True, "message": f"{provider_id} credentials removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete credentials: {str(e)}")

@router.post("/credentials/{provider_id}/test")
async def test_provider_credentials(
    provider_id: str,
    credentials: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test credentials for a specific provider"""
    if provider_id not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not supported")

    provider_config = CREDENTIAL_PROVIDERS[provider_id]

    if not provider_config.get("test_endpoint", False):
        raise HTTPException(
            status_code=501,
            detail=f"Connection testing not implemented for {provider_id}"
        )

    # Handle GitHub App specifically
    if provider_id == "github_app":
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
                            "username": integration.github_config.username
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

    # Handle GitHub OAuth
    elif provider_id == "github":
        try:
            from app.integrations.github_integration import (
                GitHubConfig, GitHubAuthMode, GitHubIntegration
            )

            if not credentials.get("access_token"):
                return {
                    "success": False,
                    "error": "Missing access token",
                    "message": "Please provide a GitHub access token"
                }

            config = GitHubConfig(
                auth_mode=GitHubAuthMode.OAUTH,
                access_token=credentials["access_token"]
            )

            integration = GitHubIntegration("test", config.__dict__)

            try:
                auth_success = await integration.authenticate()

                if auth_success:
                    repositories = await integration.get_repositories()

                    return {
                        "success": True,
                        "message": "GitHub OAuth authentication successful",
                        "details": {
                            "username": integration.github_config.username,
                            "repositories_found": len(repositories)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Authentication failed",
                        "message": "Invalid GitHub access token"
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": "GitHub test failed",
                    "message": str(e)
                }
            finally:
                await integration.__aexit__(None, None, None)

        except Exception as e:
            return {
                "success": False,
                "error": "Test failed",
                "message": str(e)
            }

    # For other providers, return mock success for now
    return {
        "success": True,
        "message": f"Connection test for {provider_id} successful (mock)",
        "provider": provider_id
    }

@router.get("/providers")
async def get_available_providers():
    """Get list of all available credential providers"""
    return {
        "providers": CREDENTIAL_PROVIDERS,
        "total": len(CREDENTIAL_PROVIDERS)
    }

@router.post("/credentials/test-github-app")
async def test_github_app_no_auth(
    credentials: Dict[str, Any]
):
    """Test GitHub App credentials without authentication - for development only"""
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
            # Test JWT generation
            jwt_token = integration._generate_jwt_token()
            
            # Test installation token retrieval
            installation_token = await integration._get_installation_token()
            
            # Test repository access
            repositories = await integration.get_installation_repositories()
            
            return {
                "success": True,
                "message": "GitHub App authentication successful",
                "details": {
                    "app_id": config.app_id,
                    "installation_id": config.installation_id,
                    "repositories_found": len(repositories),
                    "jwt_generated": bool(jwt_token),
                    "installation_token_obtained": bool(installation_token)
                }
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
            
    except Exception as e:
        return {
            "success": False,
            "error": "Test failed",
            "message": str(e)
        }


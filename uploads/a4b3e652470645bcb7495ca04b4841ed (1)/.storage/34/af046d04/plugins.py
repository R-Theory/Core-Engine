from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.plugin_loader import PluginLoader
from app.models.user import User
from app.models.plugin import Plugin, UserPluginConfig

router = APIRouter()

# Initialize plugin loader
plugin_loader = PluginLoader()

class PluginInstallRequest(BaseModel):
    manifest: Dict[str, Any]
    config: Dict[str, Any]

class PluginConfigUpdate(BaseModel):
    config: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None

class PluginResponse(BaseModel):
    id: str
    name: str
    version: str
    description: str
    category: str
    capabilities: List[str]
    is_active: bool
    config: Dict[str, Any]
    status: str

class PluginExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any]

@router.get("/", response_model=List[PluginResponse])
async def get_plugins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all plugins with user configurations"""
    # Get installed plugins
    result = await db.execute(select(Plugin))
    plugins = result.scalars().all()
    
    # Get user configurations
    result = await db.execute(
        select(UserPluginConfig).where(UserPluginConfig.user_id == current_user.id)
    )
    user_configs = {config.plugin_id: config for config in result.scalars().all()}
    
    plugin_responses = []
    for plugin in plugins:
        user_config = user_configs.get(plugin.id)
        
        plugin_responses.append(PluginResponse(
            id=str(plugin.id),
            name=plugin.name,
            version=plugin.version,
            description=plugin.manifest.get("description", ""),
            category=plugin.manifest.get("category", "general"),
            capabilities=plugin.manifest.get("capabilities", []),
            is_active=user_config.is_active if user_config else False,
            config=user_config.config if user_config else {},
            status=plugin.status
        ))
    
    return plugin_responses

@router.post("/", response_model=PluginResponse)
async def install_plugin(
    plugin_data: PluginInstallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Install a new plugin"""
    manifest = plugin_data.manifest
    
    # Validate manifest
    required_fields = ["name", "version", "description", "capabilities"]
    for field in required_fields:
        if field not in manifest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Check if plugin already exists
    result = await db.execute(select(Plugin).where(Plugin.name == manifest["name"]))
    existing_plugin = result.scalar_one_or_none()
    
    if existing_plugin:
        # Update existing plugin
        existing_plugin.version = manifest["version"]
        existing_plugin.manifest = manifest
        plugin = existing_plugin
    else:
        # Create new plugin
        plugin = Plugin(
            name=manifest["name"],
            version=manifest["version"],
            manifest=manifest,
            status="active"
        )
        db.add(plugin)
    
    await db.commit()
    await db.refresh(plugin)
    
    # Create or update user configuration
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id
        )
    )
    user_config = result.scalar_one_or_none()
    
    if user_config:
        user_config.config = plugin_data.config
        user_config.is_active = True
    else:
        user_config = UserPluginConfig(
            user_id=current_user.id,
            plugin_id=plugin.id,
            config=plugin_data.config,
            is_active=True
        )
        db.add(user_config)
    
    await db.commit()
    
    return PluginResponse(
        id=str(plugin.id),
        name=plugin.name,
        version=plugin.version,
        description=manifest.get("description", ""),
        category=manifest.get("category", "general"),
        capabilities=manifest.get("capabilities", []),
        is_active=True,
        config=plugin_data.config,
        status=plugin.status
    )

@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get plugin details"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found"
        )
    
    # Get user configuration
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id
        )
    )
    user_config = result.scalar_one_or_none()
    
    return PluginResponse(
        id=str(plugin.id),
        name=plugin.name,
        version=plugin.version,
        description=plugin.manifest.get("description", ""),
        category=plugin.manifest.get("category", "general"),
        capabilities=plugin.manifest.get("capabilities", []),
        is_active=user_config.is_active if user_config else False,
        config=user_config.config if user_config else {},
        status=plugin.status
    )

@router.put("/{plugin_id}/config", response_model=PluginResponse)
async def update_plugin_config(
    plugin_id: str,
    config_data: PluginConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update plugin configuration"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found"
        )
    
    # Get or create user configuration
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id
        )
    )
    user_config = result.scalar_one_or_none()
    
    if user_config:
        user_config.config = config_data.config
        if config_data.credentials:
            user_config.credentials = config_data.credentials
    else:
        user_config = UserPluginConfig(
            user_id=current_user.id,
            plugin_id=plugin.id,
            config=config_data.config,
            credentials=config_data.credentials,
            is_active=False
        )
        db.add(user_config)
    
    await db.commit()
    await db.refresh(user_config)
    
    return PluginResponse(
        id=str(plugin.id),
        name=plugin.name,
        version=plugin.version,
        description=plugin.manifest.get("description", ""),
        category=plugin.manifest.get("category", "general"),
        capabilities=plugin.manifest.get("capabilities", []),
        is_active=user_config.is_active,
        config=user_config.config,
        status=plugin.status
    )

@router.post("/{plugin_id}/activate")
async def activate_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate plugin for user"""
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin_id
        )
    )
    user_config = result.scalar_one_or_none()
    
    if not user_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin configuration not found"
        )
    
    user_config.is_active = True
    await db.commit()
    
    return {"message": "Plugin activated successfully"}

@router.post("/{plugin_id}/deactivate")
async def deactivate_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate plugin for user"""
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin_id
        )
    )
    user_config = result.scalar_one_or_none()
    
    if not user_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin configuration not found"
        )
    
    user_config.is_active = False
    await db.commit()
    
    return {"message": "Plugin deactivated successfully"}

@router.post("/{plugin_id}/execute")
async def execute_plugin_action(
    plugin_id: str,
    execute_data: PluginExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a plugin action"""
    # Get plugin
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin not found"
        )
    
    # Check if plugin is active for user
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin.id,
            UserPluginConfig.is_active == True
        )
    )
    user_config = result.scalar_one_or_none()
    
    if not user_config:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plugin not activated for user"
        )
    
    # Execute plugin action
    try:
        result = await plugin_loader.execute_plugin_action(
            plugin.name,
            execute_data.action,
            execute_data.params
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plugin execution failed: {str(e)}"
        )

@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uninstall plugin (remove user configuration)"""
    result = await db.execute(
        select(UserPluginConfig).where(
            UserPluginConfig.user_id == current_user.id,
            UserPluginConfig.plugin_id == plugin_id
        )
    )
    user_config = result.scalar_one_or_none()
    
    if user_config:
        await db.delete(user_config)
        await db.commit()
    
    return {"message": "Plugin uninstalled successfully"}
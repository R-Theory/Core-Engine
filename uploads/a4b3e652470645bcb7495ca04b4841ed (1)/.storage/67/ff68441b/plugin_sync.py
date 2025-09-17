from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.plugin import UserPluginConfig
from app.core.plugin_loader import PluginLoader
import logging
import asyncio

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def sync_all_canvas_data(self):
    """Sync Canvas data for all active users"""
    return asyncio.run(_sync_all_canvas_data())

@shared_task(bind=True)
def sync_all_github_data(self):
    """Sync GitHub data for all active users"""
    return asyncio.run(_sync_all_github_data())

async def _sync_all_canvas_data():
    """Async implementation of Canvas sync"""
    plugin_loader = PluginLoader()
    results = {"success": 0, "errors": 0}
    
    async with AsyncSessionLocal() as db:
        # Get all active Canvas plugin configurations
        result = await db.execute(
            select(UserPluginConfig)
            .join(UserPluginConfig.plugin)
            .where(
                UserPluginConfig.is_active == True,
                UserPluginConfig.plugin.has(name="canvas-integration")
            )
        )
        configs = result.scalars().all()
        
        for config in configs:
            try:
                # Execute Canvas sync
                plugin_result = await plugin_loader.execute_plugin_action(
                    "canvas-integration",
                    "sync_courses",
                    {"user_id": str(config.user_id)}
                )
                
                if plugin_result.get("success"):
                    results["success"] += 1
                    logger.info(f"Canvas sync successful for user {config.user_id}")
                else:
                    results["errors"] += 1
                    logger.error(f"Canvas sync failed for user {config.user_id}: {plugin_result.get('error')}")
                    
            except Exception as e:
                results["errors"] += 1
                logger.error(f"Canvas sync error for user {config.user_id}: {e}")
    
    return results

async def _sync_all_github_data():
    """Async implementation of GitHub sync"""
    plugin_loader = PluginLoader()
    results = {"success": 0, "errors": 0}
    
    async with AsyncSessionLocal() as db:
        # Get all active GitHub plugin configurations
        result = await db.execute(
            select(UserPluginConfig)
            .join(UserPluginConfig.plugin)
            .where(
                UserPluginConfig.is_active == True,
                UserPluginConfig.plugin.has(name="github-integration")
            )
        )
        configs = result.scalars().all()
        
        for config in configs:
            try:
                # Execute GitHub sync
                plugin_result = await plugin_loader.execute_plugin_action(
                    "github-integration",
                    "sync_repositories",
                    {
                        "user_id": str(config.user_id),
                        "include_private": config.config.get("include_private", False)
                    }
                )
                
                if plugin_result.get("success"):
                    results["success"] += 1
                    logger.info(f"GitHub sync successful for user {config.user_id}")
                else:
                    results["errors"] += 1
                    logger.error(f"GitHub sync failed for user {config.user_id}: {plugin_result.get('error')}")
                    
            except Exception as e:
                results["errors"] += 1
                logger.error(f"GitHub sync error for user {config.user_id}: {e}")
    
    return results
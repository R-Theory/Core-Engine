"""
Documents API - Endpoints for document processing and management

This module provides REST API endpoints for the document processing system,
including file upload, processing status, search, and plugin management.
"""

import os
import tempfile
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.document_engine import document_engine
from app.core.plugin_system import plugin_registry
from app.core.plugin_interface import PluginConfig
from app.core.config import settings
from app.core.security import get_current_user
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.plugin import Plugin as PluginModel, UserPluginConfig
from app.models.user import User
from app.core.crypto import decrypt_dict
from app.plugins.storage.notion_storage import NotionStoragePlugin

router = APIRouter()

# Request/Response models
class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    success: bool
    message: str
    document_id: Optional[str] = None
    task_id: Optional[str] = None
    processing_async: bool = False
    metadata: Dict[str, Any] = {}

class DocumentSearchRequest(BaseModel):
    """Request model for document search"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 50

class PluginConfigRequest(BaseModel):
    """Request model for plugin configuration"""
    plugin_name: str
    enabled: bool
    config: Dict[str, Any] = {}
    priority: int = 100

class ProcessingStatusResponse(BaseModel):
    """Response model for processing status"""
    queue_size: int
    worker_running: bool
    enabled_plugins: Dict[str, int]
    supported_file_types: List[Dict[str, Any]]

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    process_async: bool = Form(default=False),
    metadata: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process a document
    
    Args:
        file: The uploaded file
        process_async: Whether to process asynchronously
        metadata: Optional JSON metadata string
        
    Returns:
        DocumentUploadResponse: Upload result
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        file_size = 0
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        
        try:
            # Save uploaded file
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(status_code=413, detail="File too large (max 100MB)")
                temp_file.write(chunk)
            
            temp_file.close()
            
            # Parse metadata if provided
            doc_metadata = {}
            if metadata:
                try:
                    import json
                    doc_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid metadata JSON")
            
            # Add upload metadata
            doc_metadata.update({
                "original_filename": file.filename,
                "file_size": file_size,
                "upload_time": datetime.utcnow().isoformat(),
                "content_type": file.content_type
            })
            
            # Build user-scoped storage plugins if credentials exist
            user_storages = []
            try:
                # Find Notion plugin record
                result = await db.execute(select(PluginModel).where(PluginModel.name == "notion-storage"))
                notion_plugin = result.scalar_one_or_none()
                if notion_plugin:
                    result = await db.execute(
                        select(UserPluginConfig).where(
                            UserPluginConfig.user_id == current_user.id,
                            UserPluginConfig.plugin_id == notion_plugin.id,
                            UserPluginConfig.is_active == True,
                        )
                    )
                    user_cfg = result.scalar_one_or_none()
                    if user_cfg and user_cfg.credentials:
                        creds = decrypt_dict(user_cfg.credentials, settings.SECRET_KEY)
                        notion_config = PluginConfig(
                            enabled=True,
                            config={
                                "integration_token": creds.get("integration_token"),
                                "database_id": creds.get("database_id"),
                            },
                            priority=50,
                        )
                        notion_storage = NotionStoragePlugin(notion_config)
                        if await notion_storage.initialize():
                            user_storages.append(notion_storage)
            except Exception:
                # Non-fatal: continue without storage if any error
                pass

            if process_async:
                # Process asynchronously
                task_id = await document_engine.process_file_async(
                    temp_file.name,
                    doc_metadata
                )
                
                return DocumentUploadResponse(
                    success=True,
                    message="File queued for processing",
                    task_id=task_id,
                    processing_async=True,
                    metadata={"file_size": file_size, "filename": file.filename}
                )
            else:
                # Process synchronously
                result = await document_engine.process_file(
                    temp_file.name,
                    doc_metadata,
                    storage_plugins=user_storages if user_storages else None,
                )
                
                if result.success:
                    document_data = result.data.get("document", {})
                    return DocumentUploadResponse(
                        success=True,
                        message="Document processed successfully",
                        document_id=document_data.get("id"),
                        processing_async=False,
                        metadata=result.metadata
                    )
                else:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Processing failed: {result.error_message}"
                    )
        
        finally:
            # Cleanup temporary file
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/search")
async def search_documents(request: DocumentSearchRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Search across all stored documents
    
    Args:
        request: Search request parameters
        
    Returns:
        Search results
    """
    try:
        # Build user-scoped storage plugins if credentials exist
        user_storages = []
        try:
            result_plugin = await db.execute(select(PluginModel).where(PluginModel.name == "notion-storage"))
            notion_plugin = result_plugin.scalar_one_or_none()
            if notion_plugin:
                result_cfg = await db.execute(
                    select(UserPluginConfig).where(
                        UserPluginConfig.user_id == current_user.id,
                        UserPluginConfig.plugin_id == notion_plugin.id,
                        UserPluginConfig.is_active == True,
                    )
                )
                user_cfg = result_cfg.scalar_one_or_none()
                if user_cfg and user_cfg.credentials:
                    creds = decrypt_dict(user_cfg.credentials, settings.SECRET_KEY)
                    notion_config = PluginConfig(
                        enabled=True,
                        config={
                            "integration_token": creds.get("integration_token"),
                            "database_id": creds.get("database_id"),
                        },
                        priority=50,
                    )
                    notion_storage = NotionStoragePlugin(notion_config)
                    if await notion_storage.initialize():
                        user_storages.append(notion_storage)
        except Exception:
            pass

        result = await document_engine.search_documents(
            request.query,
            request.filters,
            storage_plugins=user_storages if user_storages else None,
        )
        
        if result.success:
            # Limit results if requested
            results = result.data
            if request.limit and len(results) > request.limit:
                results = results[:request.limit]
            
            return {
                "success": True,
                "results": results,
                "total_found": len(result.data),
                "returned": len(results),
                "metadata": result.metadata
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {result.error_message}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status():
    """
    Get current document processing status
    
    Returns:
        ProcessingStatusResponse: Current status
    """
    try:
        status = await document_engine.get_processing_status()
        supported_types = await document_engine.get_supported_file_types()
        
        return ProcessingStatusResponse(
            queue_size=status["queue_size"],
            worker_running=status["worker_running"],
            enabled_plugins=status["enabled_plugins"],
            supported_file_types=supported_types
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

@router.get("/plugins")
async def get_plugin_info():
    """
    Get information about all available plugins
    
    Returns:
        Plugin information including status and metadata
    """
    try:
        plugin_info = plugin_registry.get_all_plugin_info()
        health_status = await plugin_registry.health_check()
        
        # Add health status to plugin info
        for name, info in plugin_info.items():
            info["healthy"] = health_status.get(name, False)
        
        return {
            "success": True,
            "plugins": plugin_info,
            "total_plugins": len(plugin_info),
            "enabled_plugins": len([p for p in plugin_info.values() if p.get("enabled", False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin info error: {str(e)}")

@router.post("/plugins/configure")
async def configure_plugin(request: PluginConfigRequest):
    """
    Configure a plugin
    
    Args:
        request: Plugin configuration request
        
    Returns:
        Configuration result
    """
    try:
        config = PluginConfig(
            enabled=request.enabled,
            config=request.config,
            priority=request.priority
        )
        
        # Load or reload the plugin
        success = await plugin_registry.load_plugin(request.plugin_name, config)
        
        if success:
            return {
                "success": True,
                "message": f"Plugin {request.plugin_name} configured successfully",
                "plugin_name": request.plugin_name,
                "enabled": request.enabled
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to configure plugin: {request.plugin_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@router.post("/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """
    Enable a plugin
    
    Args:
        plugin_name: Name of the plugin to enable
        
    Returns:
        Enable result
    """
    try:
        success = await plugin_registry.enable_plugin(plugin_name)
        
        if success:
            return {
                "success": True,
                "message": f"Plugin {plugin_name} enabled successfully",
                "plugin_name": plugin_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to enable plugin: {plugin_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enable error: {str(e)}")

@router.post("/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """
    Disable a plugin
    
    Args:
        plugin_name: Name of the plugin to disable
        
    Returns:
        Disable result
    """
    try:
        success = await plugin_registry.disable_plugin(plugin_name)
        
        if success:
            return {
                "success": True,
                "message": f"Plugin {plugin_name} disabled successfully",
                "plugin_name": plugin_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to disable plugin: {plugin_name}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disable error: {str(e)}")

@router.get("/supported-types")
async def get_supported_file_types():
    """
    Get all supported file types
    
    Returns:
        List of supported file types with extensions and MIME types
    """
    try:
        supported_types = await document_engine.get_supported_file_types()
        
        # Aggregate all extensions and MIME types
        all_extensions = set()
        all_mime_types = set()
        
        for parser_info in supported_types:
            all_extensions.update(parser_info.get("extensions", []))
            all_mime_types.update(parser_info.get("mime_types", []))
        
        return {
            "success": True,
            "parsers": supported_types,
            "summary": {
                "total_extensions": len(all_extensions),
                "total_mime_types": len(all_mime_types),
                "extensions": sorted(list(all_extensions)),
                "mime_types": sorted(list(all_mime_types))
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supported types error: {str(e)}")

# Initialize document engine and plugins on startup
@router.on_event("startup")
async def startup_event():
    """Initialize document engine and discover plugins"""
    try:
        await document_engine.initialize()
        
        # Load default plugins with basic configuration
        default_plugins = [
            ("textparser", PluginConfig(enabled=True, priority=10)),
            ("pdfparser", PluginConfig(enabled=True, priority=20)),
            ("docxparser", PluginConfig(enabled=True, priority=30)),
        ]
        
        for plugin_name, config in default_plugins:
            await plugin_registry.load_plugin(plugin_name, config)
            
    except Exception as e:
        print(f"Failed to initialize document system: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for document processing system
    
    Returns:
        Health status
    """
    try:
        plugin_health = await plugin_registry.health_check()
        engine_status = await document_engine.get_processing_status()
        
        return {
            "status": "healthy",
            "plugins": plugin_health,
            "engine": engine_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

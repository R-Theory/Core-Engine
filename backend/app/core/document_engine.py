"""
Document Engine - Main document processing system

This module provides the core document processing functionality that coordinates
plugins to parse, process, and store documents.
"""

import os
import mimetypes
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path
import asyncio
import logging
from datetime import datetime

from .plugin_system import plugin_registry
from .plugin_interface import (
    Document, PluginResult, PluginType,
    StoragePlugin, ParserPlugin, ProcessorPlugin,
    PluginException, PluginProcessingError
)

logger = logging.getLogger(__name__)

class DocumentEngine:
    """
    Main document processing engine
    
    Coordinates plugins to handle the complete document lifecycle:
    1. File type detection
    2. Content parsing
    3. Content processing/enrichment
    4. Storage across configured backends
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._processing_queue = asyncio.Queue()
        self._worker_task = None

    async def initialize(self):
        """Initialize the document engine"""
        try:
            # Discover and load plugins
            await plugin_registry.discover_plugins()
            self.logger.info("Document engine initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize document engine: {str(e)}")
            return False

    async def process_file(self, file_path: str, metadata: Dict[str, Any] = None, storage_plugins: Optional[List[StoragePlugin]] = None) -> PluginResult:
        """
        Process a file through the complete pipeline
        
        Args:
            file_path: Path to the file to process
            metadata: Optional additional metadata
            
        Returns:
            PluginResult: Result of the processing operation
        """
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                return PluginResult(
                    success=False,
                    error_message=f"File not found: {file_path}"
                )
            
            # Get file info
            file_info = self._get_file_info(file_path)
            
            # Step 1: Find appropriate parser
            parser = await plugin_registry.get_parser_for_file(
                file_path, 
                file_info.get('mime_type')
            )
            
            if not parser:
                return PluginResult(
                    success=False,
                    error_message=f"No parser available for file type: {file_info.get('mime_type', 'unknown')}"
                )
            
            # Step 2: Parse the file
            self.logger.info(f"Parsing with {parser.metadata.name}")
            parse_result = await parser.parse(file_path)
            
            if not parse_result.success:
                return PluginResult(
                    success=False,
                    error_message=f"Parsing failed: {parse_result.error_message}"
                )
            
            # Create document object
            document = Document(
                title=parse_result.data.get('title', Path(file_path).stem),
                content=parse_result.data.get('content', ''),
                file_path=file_path,
                mime_type=file_info.get('mime_type'),
                size=file_info.get('size', 0),
                created_at=datetime.utcnow(),
                metadata={
                    **(metadata or {}),
                    **parse_result.metadata,
                    'parser_used': parser.metadata.name
                },
                source=parser.metadata.name
            )
            
            # Step 3: Process through processor plugins
            processors = plugin_registry.get_processor_plugins()
            for processor in processors:
                try:
                    if await processor.can_process('document', document.metadata):
                        self.logger.info(f"Processing with {processor.metadata.name}")
                        process_result = await processor.transform(document.content, document.metadata)
                        
                        if process_result.success:
                            # Update document with processed data
                            if 'content' in process_result.data:
                                document.content = process_result.data['content']
                            
                            # Merge metadata
                            document.metadata.update(process_result.metadata)
                            
                except Exception as e:
                    self.logger.warning(f"Processor {processor.metadata.name} failed: {str(e)}")
                    # Continue with other processors
            
            # Step 4: Store in storage backends
            # If specific storage plugins are provided (e.g., user-scoped), use them
            # otherwise fall back to globally enabled storage plugins
            storage_plugins = storage_plugins or plugin_registry.get_storage_plugins()
            storage_results = {}

            # If no storage plugins are available, treat as success with parsed content only
            if not storage_plugins:
                self.logger.info("No storage plugins configured; returning parsed document only")
                return PluginResult(
                    success=True,
                    data={
                        "document": document.dict(),
                        "storage_results": {}
                    },
                    metadata={
                        "processing_time": datetime.utcnow(),
                        "storage_count": 0
                    }
                )
            
            for storage in storage_plugins:
                try:
                    self.logger.info(f"Storing with {storage.metadata.name}")
                    store_result = await storage.store(document.content, document.metadata)
                    
                    if store_result.success:
                        storage_id = store_result.data.get('storage_id') or store_result.data.get('id')
                        if storage_id:
                            document.storage_ids[storage.metadata.name] = storage_id
                            storage_results[storage.metadata.name] = {
                                "success": True,
                                "storage_id": storage_id
                            }
                    else:
                        storage_results[storage.metadata.name] = {
                            "success": False,
                            "error": store_result.error_message
                        }
                        
                except Exception as e:
                    self.logger.error(f"Storage {storage.metadata.name} failed: {str(e)}")
                    storage_results[storage.metadata.name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Check if at least one storage succeeded
            if any(result.get("success", False) for result in storage_results.values()):
                self.logger.info(f"Document processed successfully: {document.title}")
                return PluginResult(
                    success=True,
                    data={
                        "document": document.dict(),
                        "storage_results": storage_results
                    },
                    metadata={
                        "processing_time": datetime.utcnow(),
                        "storage_count": len([r for r in storage_results.values() if r.get("success")])
                    }
                )
            else:
                return PluginResult(
                    success=False,
                    error_message="All storage backends failed",
                    data={"storage_results": storage_results}
                )
                
        except Exception as e:
            self.logger.error(f"Document processing failed: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Processing error: {str(e)}"
            )

    async def process_file_async(self, file_path: str, metadata: Dict[str, Any] = None) -> str:
        """
        Queue file for background processing
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata
            
        Returns:
            str: Processing task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # Add to processing queue
        await self._processing_queue.put({
            "task_id": task_id,
            "file_path": file_path,
            "metadata": metadata,
            "queued_at": datetime.utcnow()
        })
        
        # Start worker if not running
        if not self._worker_task or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._background_worker())
        
        return task_id

    async def _background_worker(self):
        """Background worker for processing queued files"""
        while True:
            try:
                # Wait for next item in queue
                item = await self._processing_queue.get()
                
                self.logger.info(f"Processing queued file: {item['file_path']}")
                
                # Process the file
                result = await self.process_file(
                    item["file_path"],
                    item["metadata"]
                )
                
                # TODO: Store result in database for status tracking
                # For now, just log the result
                if result.success:
                    self.logger.info(f"Background processing completed: {item['task_id']}")
                else:
                    self.logger.error(f"Background processing failed: {item['task_id']} - {result.error_message}")
                
                # Mark task as done
                self._processing_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Background worker error: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before continuing

    async def search_documents(self, query: str, filters: Dict[str, Any] = None, storage_plugins: Optional[List[StoragePlugin]] = None) -> PluginResult:
        """
        Search across all storage backends
        
        Args:
            query: Search query
            filters: Optional search filters
            
        Returns:
            PluginResult: Combined search results
        """
        try:
            storage_plugins = storage_plugins or plugin_registry.get_storage_plugins()
            all_results = []
            
            # Search in all storage backends
            for storage in storage_plugins:
                try:
                    search_result = await storage.search(query, filters)
                    if search_result.success and search_result.data:
                        # Add source information
                        for item in search_result.data:
                            item['source_storage'] = storage.metadata.name
                        all_results.extend(search_result.data)
                        
                except Exception as e:
                    self.logger.warning(f"Search failed in {storage.metadata.name}: {str(e)}")
            
            return PluginResult(
                success=True,
                data=all_results,
                metadata={
                    "total_results": len(all_results),
                    "query": query,
                    "searched_storages": [s.metadata.name for s in storage_plugins]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Search error: {str(e)}"
            )

    async def get_supported_file_types(self) -> List[Dict[str, Any]]:
        """
        Get all supported file types from available parsers
        
        Returns:
            List of supported file types with extensions and MIME types
        """
        supported_types = []
        parsers = plugin_registry.get_parser_plugins()
        
        for parser in parsers:
            try:
                extensions = parser.get_supported_extensions()
                mime_types = parser.get_supported_mime_types()
                
                supported_types.append({
                    "parser": parser.metadata.name,
                    "extensions": extensions,
                    "mime_types": mime_types
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to get supported types from {parser.metadata.name}: {str(e)}")
        
        return supported_types

    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information including size and MIME type"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "size": stat.st_size,
                "mime_type": mime_type,
                "extension": Path(file_path).suffix.lower(),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get file info for {file_path}: {str(e)}")
            return {}

    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return {
            "queue_size": self._processing_queue.qsize(),
            "worker_running": self._worker_task and not self._worker_task.done(),
            "enabled_plugins": {
                "storage": len(plugin_registry.get_storage_plugins()),
                "parsers": len(plugin_registry.get_parser_plugins()),
                "processors": len(plugin_registry.get_processor_plugins())
            }
        }

# Global document engine instance
document_engine = DocumentEngine()

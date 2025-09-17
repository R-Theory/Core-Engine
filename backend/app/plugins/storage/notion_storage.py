"""
Notion Storage Plugin - Store documents as Notion pages

This plugin enables storing documents directly in Notion as pages within
a database, supporting your vision of Notion as the primary knowledge backend.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.core.plugin_interface import (
    StoragePlugin, PluginResult, PluginMetadata, PluginType, 
    PluginCapability, PluginConfig, PluginProcessingError
)

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

logger = logging.getLogger(__name__)

class NotionStoragePlugin(StoragePlugin):
    """
    Notion storage plugin for storing documents as Notion pages
    
    Features:
    - Store documents as pages in a Notion database
    - Preserve document metadata as database properties
    - Support for rich text content
    - Search across stored documents
    - Bi-directional sync capabilities
    """
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.client: Optional[Client] = None
        self.database_id: Optional[str] = None
        self.integration_token: Optional[str] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Notion Storage",
            version="1.0.0",
            description="Store documents as pages in Notion databases",
            author="Core Engine Team",
            plugin_type=PluginType.STORAGE,
            capabilities=[
                PluginCapability.STORE,
                PluginCapability.READ,
                PluginCapability.SEARCH,
                PluginCapability.WRITE
            ],
            dependencies=["notion-client"],
            config_schema={
                "integration_token": {
                    "type": "string",
                    "required": True,
                    "description": "Notion integration token"
                },
                "database_id": {
                    "type": "string",
                    "required": True,
                    "description": "Notion database ID for storing documents"
                },
                "page_template": {
                    "type": "string",
                    "required": False,
                    "description": "Template for new pages"
                }
            }
        )

    async def process(self, data: Any, **kwargs) -> PluginResult:
        \"\"\"Main processing method required by base Plugin class\"\"\"
        # For storage plugins, this method can delegate to store
        if isinstance(data, dict) and 'content' in data and 'metadata' in data:
            return await self.store(data['content'], data['metadata'])
        else:
            return PluginResult(
                success=False,
                error_message=\"NotionStorage expects data with 'content' and 'metadata' keys\"
            )

    async def initialize(self) -> bool:
        """Initialize the Notion client and validate configuration"""
        try:
            if not NOTION_AVAILABLE:
                self.logger.error("notion-client package not available")
                return False
            
            # Get configuration
            config = self.config.config
            self.integration_token = config.get('integration_token')
            self.database_id = config.get('database_id')
            
            if not self.integration_token:
                self.logger.error("Notion integration token not provided")
                return False
            
            # Initialize Notion client
            self.client = Client(auth=self.integration_token)
            
            # Test connection by getting database info
            if self.database_id:
                try:
                    database = await self._make_request(
                        self.client.databases.retrieve,
                        database_id=self.database_id
                    )
                    self.logger.info(f"Connected to Notion database: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}")
                except Exception as e:
                    self.logger.warning(f"Database validation failed, will create new one: {str(e)}")
                    self.database_id = None
            
            # Create database if not exists
            if not self.database_id:
                self.database_id = await self._create_documents_database()
                if not self.database_id:
                    return False
            
            self.logger.info("Notion storage plugin initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Notion storage: {str(e)}")
            return False

    async def store(self, content: str, metadata: Dict[str, Any]) -> PluginResult:
        """
        Store content as a Notion page
        
        Args:
            content: Document content to store
            metadata: Document metadata
            
        Returns:
            PluginResult: Result with page ID if successful
        """
        try:
            if not self.client or not self.database_id:
                return PluginResult(
                    success=False,
                    error_message="Notion client not initialized"
                )
            
            # Prepare page properties
            properties = self._build_page_properties(metadata)
            
            # Create page content blocks
            children = self._build_page_content(content, metadata)
            
            # Create the page
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": children
            }
            
            page = await self._make_request(
                self.client.pages.create,
                **page_data
            )
            
            page_id = page.get('id')
            page_url = page.get('url')
            
            self.logger.info(f"Document stored in Notion: {page_id}")
            
            return PluginResult(
                success=True,
                data={
                    "storage_id": page_id,
                    "page_id": page_id,
                    "page_url": page_url
                },
                metadata={
                    "storage_type": "notion_page",
                    "database_id": self.database_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store document in Notion: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Notion storage error: {str(e)}"
            )

    async def retrieve(self, storage_id: str) -> PluginResult:
        """
        Retrieve a document by page ID
        
        Args:
            storage_id: Notion page ID
            
        Returns:
            PluginResult: Result with document content
        """
        try:
            if not self.client:
                return PluginResult(
                    success=False,
                    error_message="Notion client not initialized"
                )
            
            # Get page
            page = await self._make_request(
                self.client.pages.retrieve,
                page_id=storage_id
            )
            
            # Get page content blocks
            blocks = await self._make_request(
                self.client.blocks.children.list,
                block_id=storage_id
            )
            
            # Extract content and metadata
            content = self._extract_content_from_blocks(blocks.get('results', []))
            metadata = self._extract_metadata_from_page(page)
            
            return PluginResult(
                success=True,
                data={
                    "content": content,
                    "metadata": metadata,
                    "page_url": page.get('url')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve document from Notion: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Notion retrieval error: {str(e)}"
            )

    async def delete(self, storage_id: str) -> PluginResult:
        """
        Delete a document by page ID
        
        Args:
            storage_id: Notion page ID
            
        Returns:
            PluginResult: Result of deletion
        """
        try:
            if not self.client:
                return PluginResult(
                    success=False,
                    error_message="Notion client not initialized"
                )
            
            # Archive the page (Notion's way of "deleting")
            await self._make_request(
                self.client.pages.update,
                page_id=storage_id,
                archived=True
            )
            
            self.logger.info(f"Document archived in Notion: {storage_id}")
            
            return PluginResult(
                success=True,
                data={"storage_id": storage_id}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to delete document from Notion: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Notion deletion error: {str(e)}"
            )

    async def search(self, query: str, filters: Dict[str, Any] = None) -> PluginResult:
        """
        Search documents in Notion database
        
        Args:
            query: Search query
            filters: Optional filters
            
        Returns:
            PluginResult: Search results
        """
        try:
            if not self.client or not self.database_id:
                return PluginResult(
                    success=False,
                    error_message="Notion client not initialized"
                )
            
            # Build search filter
            search_filter = {
                "database_id": self.database_id,
                "filter": {
                    "and": [
                        {
                            "property": "Content",
                            "rich_text": {
                                "contains": query
                            }
                        }
                    ]
                }
            }
            
            # Add additional filters if provided
            if filters:
                for key, value in filters.items():
                    if key == "title":
                        search_filter["filter"]["and"].append({
                            "property": "Title",
                            "title": {"contains": value}
                        })
            
            # Query database
            results = await self._make_request(
                self.client.databases.query,
                **search_filter
            )
            
            # Process results
            documents = []
            for page in results.get('results', []):
                doc_data = {
                    "page_id": page.get('id'),
                    "title": self._extract_title_from_page(page),
                    "url": page.get('url'),
                    "created_time": page.get('created_time'),
                    "last_edited_time": page.get('last_edited_time'),
                    "metadata": self._extract_metadata_from_page(page)
                }
                documents.append(doc_data)
            
            return PluginResult(
                success=True,
                data=documents,
                metadata={
                    "total_results": len(documents),
                    "query": query,
                    "database_id": self.database_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to search in Notion: {str(e)}")
            return PluginResult(
                success=False,
                error_message=f"Notion search error: {str(e)}"
            )

    async def _create_documents_database(self) -> Optional[str]:
        """Create a new database for storing documents"""
        try:
            # First, we need a page to create the database in
            # For now, we'll assume the user has provided a parent page ID
            # In a real implementation, this would be configurable
            
            database_data = {
                "parent": {
                    "type": "page_id", 
                    "page_id": "your-parent-page-id"  # This should come from config
                },
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Core Engine Documents"}
                    }
                ],
                "properties": {
                    "Title": {"title": {}},
                    "Content": {"rich_text": {}},
                    "File Type": {"select": {"options": []}},
                    "Size": {"number": {}},
                    "Created": {"date": {}},
                    "Tags": {"multi_select": {"options": []}},
                    "Source": {"rich_text": {}}
                }
            }
            
            database = await self._make_request(
                self.client.databases.create,
                **database_data
            )
            
            database_id = database.get('id')
            self.logger.info(f"Created new Notion database: {database_id}")
            
            return database_id
            
        except Exception as e:
            self.logger.error(f"Failed to create Notion database: {str(e)}")
            return None

    def _build_page_properties(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion page properties from metadata"""
        properties = {}
        
        # Title
        title = metadata.get('title', 'Untitled Document')
        properties["Title"] = {
            "title": [{"type": "text", "text": {"content": title}}]
        }
        
        # File type
        if 'mime_type' in metadata:
            properties["File Type"] = {
                "select": {"name": metadata['mime_type']}
            }
        
        # Size
        if 'size' in metadata:
            properties["Size"] = {"number": metadata['size']}
        
        # Created date
        properties["Created"] = {
            "date": {"start": datetime.utcnow().isoformat()}
        }
        
        # Tags
        if 'tags' in metadata and isinstance(metadata['tags'], list):
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in metadata['tags']]
            }
        
        # Source
        if 'source' in metadata:
            properties["Source"] = {
                "rich_text": [{"type": "text", "text": {"content": metadata['source']}}]
            }
        
        return properties

    def _build_page_content(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build Notion page content blocks"""
        blocks = []
        
        # Add content as paragraph blocks
        # Split content into chunks (Notion has limits on block content)
        max_chunk_size = 2000
        content_chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
        
        for chunk in content_chunks:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": chunk}
                        }
                    ]
                }
            })
        
        return blocks

    def _extract_content_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract text content from Notion blocks"""
        content_parts = []
        
        for block in blocks:
            block_type = block.get('type')
            if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3']:
                rich_text = block.get(block_type, {}).get('rich_text', [])
                for text_obj in rich_text:
                    if text_obj.get('type') == 'text':
                        content_parts.append(text_obj.get('text', {}).get('content', ''))
        
        return '\n'.join(content_parts)

    def _extract_metadata_from_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Notion page properties"""
        metadata = {}
        properties = page.get('properties', {})
        
        # Extract various property types
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type')
            
            if prop_type == 'title':
                title_list = prop_data.get('title', [])
                if title_list:
                    metadata[prop_name.lower()] = title_list[0].get('plain_text', '')
            
            elif prop_type == 'rich_text':
                text_list = prop_data.get('rich_text', [])
                if text_list:
                    metadata[prop_name.lower()] = text_list[0].get('plain_text', '')
            
            elif prop_type == 'number':
                metadata[prop_name.lower()] = prop_data.get('number')
            
            elif prop_type == 'select':
                select_data = prop_data.get('select')
                if select_data:
                    metadata[prop_name.lower()] = select_data.get('name')
            
            elif prop_type == 'multi_select':
                multi_select = prop_data.get('multi_select', [])
                metadata[prop_name.lower()] = [item.get('name') for item in multi_select]
        
        return metadata

    def _extract_title_from_page(self, page: Dict[str, Any]) -> str:
        """Extract title from Notion page"""
        properties = page.get('properties', {})
        title_prop = properties.get('Title', {})
        title_list = title_prop.get('title', [])
        
        if title_list:
            return title_list[0].get('plain_text', 'Untitled')
        
        return 'Untitled'

    async def _make_request(self, func, **kwargs):
        """Make async request to Notion API with error handling"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: func(**kwargs))
        except APIResponseError as e:
            self.logger.error(f"Notion API error: {e.status_code} - {e.message}")
            raise PluginProcessingError(f"Notion API error: {e.message}", self.metadata.name)
        except Exception as e:
            self.logger.error(f"Notion request failed: {str(e)}")
            raise
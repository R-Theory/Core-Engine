"""
Notion Integration
Syncs pages, databases, and content from Notion
This is the foundation for your knowledge graph vision where Notion acts as backend
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.integration_engine import (
    BaseIntegration, IntegrationType, IntegrationCapability, 
    SyncResult, SyncStatus, IntegrationMetadata, register_integration
)

class NotionConfig(BaseModel):
    """Notion API configuration"""
    access_token: str
    api_url: str = "https://api.notion.com/v1"
    notion_version: str = "2022-06-28"

class NotionPage(BaseModel):
    """Notion page data"""
    id: str
    title: str
    url: str
    created_time: datetime
    last_edited_time: datetime
    archived: bool = False
    parent_type: str  # "database_id", "page_id", "workspace"
    parent_id: Optional[str] = None
    properties: Dict[str, Any] = {}
    content: Optional[str] = None  # Page content blocks

class NotionDatabase(BaseModel):
    """Notion database data"""
    id: str
    title: str
    url: str
    created_time: datetime
    last_edited_time: datetime
    archived: bool = False
    properties: Dict[str, Any] = {}
    description: Optional[str] = None

class NotionBlock(BaseModel):
    """Notion block data"""
    id: str
    type: str
    content: str
    page_id: str
    created_time: datetime
    last_edited_time: datetime
    has_children: bool = False

@register_integration
class NotionIntegration(BaseIntegration[NotionPage]):
    """
    Notion integration for knowledge management
    Perfect foundation for your vision of Notion-as-backend + graph visualization
    """
    
    @property
    def integration_type(self) -> IntegrationType:
        return IntegrationType.KNOWLEDGE
    
    @property
    def supported_capabilities(self) -> List[IntegrationCapability]:
        return [
            IntegrationCapability.READ,
            IntegrationCapability.WRITE,
            IntegrationCapability.SEARCH,
            IntegrationCapability.GRAPH,  # Pages -> Links -> Databases relationships
            IntegrationCapability.BIDIRECTIONAL,  # Can sync both ways
        ]
    
    @property
    def service_name(self) -> str:
        return "Notion"
    
    def __init__(self, integration_id: str, config: Dict[str, Any]):
        super().__init__(integration_id, config)
        if config:  # Only validate config if it's provided
            self.notion_config = NotionConfig(**config)
        else:
            self.notion_config = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.notion_config.access_token}",
                "Notion-Version": self.notion_config.notion_version,
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Any:
        """Make Notion API request"""
        session = await self._get_session()
        url = f"{self.notion_config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            kwargs = {"params": params or {}}
            if data and method in ["POST", "PATCH"]:
                kwargs["json"] = data
            
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"Notion API request failed: {str(e)}")
            raise
    
    async def _get_paginated_data(self, endpoint: str, data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all pages of data from Notion API"""
        all_data = []
        next_cursor = None
        
        while True:
            try:
                request_data = (data or {}).copy()
                if next_cursor:
                    request_data["start_cursor"] = next_cursor
                
                response = await self._make_request(endpoint, "POST", request_data)
                
                if "results" in response:
                    all_data.extend(response["results"])
                    
                    if response.get("has_more", False):
                        next_cursor = response.get("next_cursor")
                    else:
                        break
                else:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error fetching paginated data: {str(e)}")
                break
        
        return all_data
    
    async def authenticate(self) -> bool:
        """Test Notion API authentication"""
        try:
            await self._make_request("/users/me")
            return True
        except Exception as e:
            self.logger.error(f"Notion authentication failed: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Notion connection"""
        return await self.authenticate()
    
    async def get_databases(self) -> List[NotionDatabase]:
        """Get all accessible databases"""
        try:
            databases_data = await self._get_paginated_data(
                "/search",
                {
                    "filter": {
                        "value": "database",
                        "property": "object"
                    }
                }
            )
            
            databases = []
            for db_data in databases_data:
                try:
                    title = ""
                    if db_data.get("title") and len(db_data["title"]) > 0:
                        title = db_data["title"][0].get("plain_text", "")
                    
                    created_time = datetime.fromisoformat(db_data["created_time"].replace('Z', '+00:00'))
                    last_edited_time = datetime.fromisoformat(db_data["last_edited_time"].replace('Z', '+00:00'))
                    
                    database = NotionDatabase(
                        id=db_data["id"],
                        title=title,
                        url=db_data["url"],
                        created_time=created_time,
                        last_edited_time=last_edited_time,
                        archived=db_data.get("archived", False),
                        properties=db_data.get("properties", {}),
                        description=db_data.get("description", [{}])[0].get("plain_text") if db_data.get("description") else None
                    )
                    databases.append(database)
                except Exception as e:
                    self.logger.warning(f"Failed to parse database {db_data.get('id', 'unknown')}: {str(e)}")
            
            return databases
        except Exception as e:
            self.logger.error(f"Failed to fetch databases: {str(e)}")
            return []
    
    async def get_pages(self, database_id: Optional[str] = None) -> List[NotionPage]:
        """Get pages from a database or search all pages"""
        try:
            if database_id:
                # Get pages from specific database
                pages_data = await self._get_paginated_data(
                    f"/databases/{database_id}/query",
                    {}
                )
            else:
                # Search all pages
                pages_data = await self._get_paginated_data(
                    "/search",
                    {
                        "filter": {
                            "value": "page",
                            "property": "object"
                        }
                    }
                )
            
            pages = []
            for page_data in pages_data:
                try:
                    # Extract title from properties or title field
                    title = "Untitled"
                    if "properties" in page_data:
                        # Look for title in properties (database page)
                        for prop_name, prop_data in page_data["properties"].items():
                            if prop_data.get("type") == "title" and prop_data.get("title"):
                                title = "".join([text.get("plain_text", "") for text in prop_data["title"]])
                                break
                    elif page_data.get("title") and len(page_data["title"]) > 0:
                        # Regular page title
                        title = "".join([text.get("plain_text", "") for text in page_data["title"]])
                    
                    created_time = datetime.fromisoformat(page_data["created_time"].replace('Z', '+00:00'))
                    last_edited_time = datetime.fromisoformat(page_data["last_edited_time"].replace('Z', '+00:00'))
                    
                    # Determine parent
                    parent = page_data.get("parent", {})
                    parent_type = parent.get("type", "workspace")
                    parent_id = None
                    if parent_type in ["database_id", "page_id"]:
                        parent_id = parent.get(parent_type)
                    
                    page = NotionPage(
                        id=page_data["id"],
                        title=title,
                        url=page_data["url"],
                        created_time=created_time,
                        last_edited_time=last_edited_time,
                        archived=page_data.get("archived", False),
                        parent_type=parent_type,
                        parent_id=parent_id,
                        properties=page_data.get("properties", {})
                    )
                    pages.append(page)
                except Exception as e:
                    self.logger.warning(f"Failed to parse page {page_data.get('id', 'unknown')}: {str(e)}")
            
            return pages
        except Exception as e:
            self.logger.error(f"Failed to fetch pages: {str(e)}")
            return []
    
    async def get_page_content(self, page_id: str) -> List[NotionBlock]:
        """Get blocks (content) for a specific page"""
        try:
            blocks_data = await self._get_paginated_data(
                f"/blocks/{page_id}/children",
                {}
            )
            
            blocks = []
            for block_data in blocks_data:
                try:
                    block_type = block_data.get("type", "unknown")
                    content = ""
                    
                    # Extract text content based on block type
                    if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                        rich_text = block_data.get(block_type, {}).get("rich_text", [])
                        content = "".join([text.get("plain_text", "") for text in rich_text])
                    elif block_type == "bulleted_list_item" or block_type == "numbered_list_item":
                        rich_text = block_data.get(block_type, {}).get("rich_text", [])
                        content = "".join([text.get("plain_text", "") for text in rich_text])
                    elif block_type == "code":
                        rich_text = block_data.get("code", {}).get("rich_text", [])
                        content = "".join([text.get("plain_text", "") for text in rich_text])
                    
                    created_time = datetime.fromisoformat(block_data["created_time"].replace('Z', '+00:00'))
                    last_edited_time = datetime.fromisoformat(block_data["last_edited_time"].replace('Z', '+00:00'))
                    
                    block = NotionBlock(
                        id=block_data["id"],
                        type=block_type,
                        content=content,
                        page_id=page_id,
                        created_time=created_time,
                        last_edited_time=last_edited_time,
                        has_children=block_data.get("has_children", False)
                    )
                    blocks.append(block)
                except Exception as e:
                    self.logger.warning(f"Failed to parse block {block_data.get('id', 'unknown')}: {str(e)}")
            
            return blocks
        except Exception as e:
            self.logger.error(f"Failed to fetch page content for {page_id}: {str(e)}")
            return []
    
    async def extract_page_links(self, page_id: str) -> List[str]:
        """Extract links to other Notion pages (for knowledge graph)"""
        try:
            blocks = await self.get_page_content(page_id)
            linked_pages = []
            
            # TODO: Parse rich text for page links and mentions
            # This would identify relationships between pages for your knowledge graph
            
            return linked_pages
        except Exception as e:
            self.logger.error(f"Failed to extract links from page {page_id}: {str(e)}")
            return []
    
    async def sync_data(self, db: Session, user_id: str, full_sync: bool = False) -> SyncResult:
        """Sync Notion data to local database"""
        try:
            result = SyncResult(status=SyncStatus.IN_PROGRESS)
            
            # For now, store Notion pages as "resources" in the existing system
            # TODO: Create dedicated Notion models later
            
            self.logger.info(f"Syncing Notion pages for user {user_id}")
            
            # Get databases first
            notion_databases = await self.get_databases()
            self.logger.info(f"Found {len(notion_databases)} Notion databases")
            
            # Get all pages
            notion_pages = await self.get_pages()
            self.logger.info(f"Found {len(notion_pages)} Notion pages")
            
            # Sync pages as resources for now
            for notion_page in notion_pages:
                try:
                    from app.models import Resource
                    
                    existing_resource = db.query(Resource).filter(
                        Resource.user_id == user_id,
                        Resource.external_id == notion_page.id,
                        Resource.external_source == "notion"
                    ).first()
                    
                    if existing_resource:
                        # Update existing
                        existing_resource.title = notion_page.title
                        existing_resource.url = notion_page.url
                        existing_resource.is_active = not notion_page.archived
                        result.items_updated += 1
                    else:
                        # Create new
                        new_resource = Resource(
                            user_id=user_id,
                            title=notion_page.title,
                            description=f"Notion page - Parent: {notion_page.parent_type}",
                            url=notion_page.url,
                            resource_type="notion_page",
                            is_active=not notion_page.archived,
                            external_id=notion_page.id,
                            external_source="notion"
                        )
                        db.add(new_resource)
                        result.items_created += 1
                    
                    result.items_processed += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to sync page {notion_page.id}: {str(e)}")
                    result.items_failed += 1
            
            db.commit()
            
            if result.items_failed > 0:
                result.status = SyncStatus.PARTIAL
            else:
                result.status = SyncStatus.SUCCESS
            
            self.logger.info(f"Notion sync completed: {result.items_created} created, {result.items_updated} updated, {result.items_failed} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"Notion sync failed: {str(e)}")
            db.rollback()
            return SyncResult(
                status=SyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_relationships(self, item_id: str) -> List[str]:
        """Get related items for knowledge graph - CRUCIAL for your vision!"""
        relationships = []
        
        try:
            if item_id.startswith("page_"):
                page_id = item_id.replace("page_", "")
                
                # Get linked pages
                linked_pages = await self.extract_page_links(page_id)
                relationships.extend([f"page_{page_id}" for page_id in linked_pages])
                
                # Get parent database if exists
                pages = await self.get_pages()
                for page in pages:
                    if page.id == page_id and page.parent_id:
                        relationships.append(f"database_{page.parent_id}")
                        break
                        
        except Exception as e:
            self.logger.error(f"Failed to get relationships for {item_id}: {str(e)}")
        
        return relationships
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[NotionPage]:
        """Search Notion content"""
        try:
            search_data = await self._make_request(
                "/search",
                "POST",
                {
                    "query": query,
                    "filter": {
                        "value": "page",
                        "property": "object"
                    }
                }
            )
            
            pages = []
            for page_data in search_data.get("results", []):
                # Convert to NotionPage object (simplified)
                try:
                    title = "Untitled"
                    if page_data.get("title"):
                        title = "".join([text.get("plain_text", "") for text in page_data["title"]])
                    
                    page = NotionPage(
                        id=page_data["id"],
                        title=title,
                        url=page_data["url"],
                        created_time=datetime.fromisoformat(page_data["created_time"].replace('Z', '+00:00')),
                        last_edited_time=datetime.fromisoformat(page_data["last_edited_time"].replace('Z', '+00:00')),
                        archived=page_data.get("archived", False),
                        parent_type=page_data.get("parent", {}).get("type", "workspace")
                    )
                    pages.append(page)
                except Exception as e:
                    self.logger.warning(f"Failed to parse search result: {str(e)}")
            
            return pages
        except Exception as e:
            self.logger.error(f"Notion search failed: {str(e)}")
            return []
    
    def extract_metadata(self, item: Any) -> IntegrationMetadata:
        """Extract metadata for knowledge graph - KEY for your vision!"""
        if isinstance(item, NotionPage):
            # Extract relationships and tags for knowledge graph
            relationships = []
            if item.parent_id:
                if item.parent_type == "database_id":
                    relationships.append(f"database_{item.parent_id}")
                elif item.parent_type == "page_id":
                    relationships.append(f"page_{item.parent_id}")
            
            return IntegrationMetadata(
                source_id=f"page_{item.id}",
                source_type="page",
                source_url=item.url,
                last_modified=item.last_edited_time,
                relationships=relationships,
                tags=["notion", "page", item.parent_type],
                additional_data={
                    "parent_type": item.parent_type,
                    "parent_id": item.parent_id,
                    "archived": item.archived,
                    "properties": item.properties
                }
            )
        elif isinstance(item, NotionDatabase):
            return IntegrationMetadata(
                source_id=f"database_{item.id}",
                source_type="database",
                source_url=item.url,
                last_modified=item.last_edited_time,
                relationships=[],  # Databases are typically root nodes
                tags=["notion", "database"],
                additional_data={
                    "properties": item.properties,
                    "description": item.description,
                    "archived": item.archived
                }
            )
        
        return super().extract_metadata(item)
    
    async def get_knowledge_graph_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Build knowledge graph from Notion data - CORE of your vision!
        This will be the foundation for Obsidian-style graph visualization
        """
        try:
            graph_data = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "source": "notion",
                    "user_id": user_id,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Get all pages and databases
            databases = await self.get_databases()
            pages = await self.get_pages()
            
            # Add database nodes
            for db in databases:
                graph_data["nodes"].append({
                    "id": f"database_{db.id}",
                    "type": "database",
                    "title": db.title,
                    "url": db.url,
                    "properties": db.properties,
                    "size": "large"  # Databases are central nodes
                })
            
            # Add page nodes and relationships
            for page in pages:
                graph_data["nodes"].append({
                    "id": f"page_{page.id}",
                    "type": "page",
                    "title": page.title,
                    "url": page.url,
                    "parent_type": page.parent_type,
                    "parent_id": page.parent_id,
                    "size": "medium"
                })
                
                # Add edge to parent
                if page.parent_id:
                    if page.parent_type == "database_id":
                        graph_data["edges"].append({
                            "source": f"database_{page.parent_id}",
                            "target": f"page_{page.id}",
                            "relationship": "contains"
                        })
                    elif page.parent_type == "page_id":
                        graph_data["edges"].append({
                            "source": f"page_{page.parent_id}",
                            "target": f"page_{page.id}",
                            "relationship": "child_of"
                        })
                
                # TODO: Add edges for page links and mentions
                # This would create the full knowledge graph
            
            return graph_data
            
        except Exception as e:
            self.logger.error(f"Failed to build knowledge graph: {str(e)}")
            return {"nodes": [], "edges": [], "error": str(e)}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
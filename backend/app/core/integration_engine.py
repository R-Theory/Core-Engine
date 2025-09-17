"""
Core Integration Engine - Extensible architecture for external service integrations
Designed to support modular integrations that can be visualized as knowledge graphs
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class IntegrationType(str, Enum):
    """Types of integrations supported"""
    LMS = "lms"                    # Learning Management System (Canvas)
    CODE_REPO = "code_repo"        # Code repositories (GitHub)
    KNOWLEDGE = "knowledge"        # Knowledge management (Notion, Obsidian)
    STORAGE = "storage"            # File storage (Google Drive, OneDrive)
    AI_MODEL = "ai_model"          # AI services (OpenAI, Anthropic)
    COMMUNICATION = "communication" # Communication (Slack, Discord)

class SyncStatus(str, Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

class IntegrationCapability(str, Enum):
    """What capabilities an integration supports"""
    READ = "read"                  # Can fetch data
    WRITE = "write"                # Can create/update data
    WEBHOOK = "webhook"            # Supports real-time webhooks
    SEARCH = "search"              # Supports searching
    GRAPH = "graph"                # Supports relationship/graph data
    BIDIRECTIONAL = "bidirectional" # Supports two-way sync

class IntegrationMetadata(BaseModel):
    """Metadata about data retrieved from integrations"""
    source_id: str                 # ID in the external system
    source_type: str               # Type of data (assignment, repository, note, etc.)
    source_url: Optional[str] = None
    last_modified: Optional[datetime] = None
    relationships: List[str] = []   # Related items for knowledge graph
    tags: List[str] = []           # Tags/categories
    additional_data: Dict[str, Any] = {}

class SyncResult(BaseModel):
    """Result of a sync operation"""
    status: SyncStatus
    items_processed: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

T = TypeVar('T')

class BaseIntegration(ABC, Generic[T]):
    """
    Abstract base class for all integrations
    Designed for maximum extensibility and knowledge graph support
    """
    
    def __init__(self, integration_id: str, config: Dict[str, Any]):
        self.integration_id = integration_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def integration_type(self) -> IntegrationType:
        """Type of this integration"""
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> List[IntegrationCapability]:
        """What capabilities this integration supports"""
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Human-readable service name"""
        pass
    
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get integration metadata without instantiation"""
        try:
            # Create a temporary instance with minimal config
            temp_instance = cls("temp", {})
            return {
                "service_name": temp_instance.service_name,
                "integration_type": temp_instance.integration_type,
                "capabilities": temp_instance.supported_capabilities
            }
        except Exception:
            # Fallback if instantiation fails
            return {
                "service_name": cls.__name__.replace('Integration', ''),
                "integration_type": IntegrationType.KNOWLEDGE,
                "capabilities": []
            }
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is working"""
        pass
    
    @abstractmethod
    async def sync_data(self, db: Session, user_id: str, full_sync: bool = False) -> SyncResult:
        """Sync data from the external service"""
        pass
    
    async def get_relationships(self, item_id: str) -> List[str]:
        """Get related items for knowledge graph (optional)"""
        return []
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[T]:
        """Search functionality (optional)"""
        raise NotImplementedError("Search not supported by this integration")
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle webhook payload (optional)"""
        raise NotImplementedError("Webhooks not supported by this integration")
    
    def extract_metadata(self, item: Any) -> IntegrationMetadata:
        """Extract metadata for knowledge graph"""
        return IntegrationMetadata(
            source_id=str(getattr(item, 'id', 'unknown')),
            source_type=self.service_name.lower()
        )

class IntegrationRegistry:
    """Registry for managing all available integrations"""
    
    def __init__(self):
        self._integrations: Dict[str, type] = {}
        self._active_instances: Dict[str, BaseIntegration] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, integration_class: type):
        """Register an integration class"""
        if not issubclass(integration_class, BaseIntegration):
            raise ValueError("Integration must inherit from BaseIntegration")
        
        # Use the class name as the key
        key = integration_class.__name__.lower().replace('integration', '')
        self._integrations[key] = integration_class
        self.logger.info(f"Registered integration: {key}")
    
    def get_available_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Get info about all available integrations"""
        result = {}
        for key, integration_class in self._integrations.items():
            try:
                # Use the class metadata method
                metadata = integration_class.get_metadata()
                result[key] = {
                    **metadata,
                    "class": integration_class.__name__
                }
            except Exception as e:
                self.logger.warning(f"Failed to get metadata for {key}: {str(e)}")
                result[key] = {
                    "service_name": key.title(),
                    "integration_type": "unknown",
                    "capabilities": [],
                    "class": integration_class.__name__,
                    "error": str(e)
                }
        return result
    
    def create_integration(self, service_key: str, integration_id: str, config: Dict[str, Any]) -> BaseIntegration:
        """Create an integration instance"""
        if service_key not in self._integrations:
            raise ValueError(f"Unknown integration: {service_key}")
        
        integration_class = self._integrations[service_key]
        instance = integration_class(integration_id, config)
        self._active_instances[integration_id] = instance
        return instance
    
    def get_integration(self, integration_id: str) -> Optional[BaseIntegration]:
        """Get an active integration instance"""
        return self._active_instances.get(integration_id)
    
    def remove_integration(self, integration_id: str):
        """Remove an integration instance"""
        if integration_id in self._active_instances:
            del self._active_instances[integration_id]

class IntegrationEngine:
    """
    Main integration engine that orchestrates all integrations
    Supports the knowledge graph vision by maintaining relationships
    """
    
    def __init__(self):
        self.registry = IntegrationRegistry()
        self.logger = logging.getLogger(__name__)
    
    async def sync_user_integrations(self, db: Session, user_id: str, integration_ids: List[str] = None) -> Dict[str, SyncResult]:
        """Sync data for all user integrations"""
        from app.models import UserIntegration
        
        query = db.query(UserIntegration).filter(
            UserIntegration.user_id == user_id,
            UserIntegration.is_active == True
        )
        
        if integration_ids:
            query = query.filter(UserIntegration.id.in_(integration_ids))
        
        user_integrations = query.all()
        results = {}
        
        for user_integration in user_integrations:
            try:
                # Get the integration instance
                integration = self.registry.get_integration(str(user_integration.id))
                if not integration:
                    # Create new instance if not exists
                    config = user_integration.config_data or {}
                    integration = self.registry.create_integration(
                        user_integration.service_name,
                        str(user_integration.id),
                        config
                    )
                
                # Perform sync
                result = await integration.sync_data(db, user_id)
                results[str(user_integration.id)] = result
                
                # Update last sync time
                user_integration.last_sync = datetime.utcnow()
                if result.status == SyncStatus.FAILED:
                    user_integration.connection_error = result.error_message
                else:
                    user_integration.connection_error = None
                    user_integration.is_connected = True
                
            except Exception as e:
                self.logger.error(f"Failed to sync integration {user_integration.id}: {str(e)}")
                results[str(user_integration.id)] = SyncResult(
                    status=SyncStatus.FAILED,
                    error_message=str(e)
                )
                user_integration.connection_error = str(e)
                user_integration.is_connected = False
        
        db.commit()
        return results
    
    async def test_integration(self, service_name: str, config: Dict[str, Any]) -> bool:
        """Test an integration configuration"""
        try:
            integration = self.registry.create_integration(
                service_name,
                "test",
                config
            )
            return await integration.test_connection()
        except Exception as e:
            self.logger.error(f"Failed to test {service_name} integration: {str(e)}")
            return False
    
    def get_knowledge_graph_data(self, db: Session, user_id: str) -> Dict[str, Any]:
        """
        Extract knowledge graph data from all integrations
        This supports your Notion-as-backend + graph visualization vision
        """
        # TODO: This will query all synced data and build relationship graph
        # For now, return structure that can be expanded
        return {
            "nodes": [],
            "edges": [],
            "metadata": {
                "last_updated": datetime.utcnow(),
                "total_nodes": 0,
                "total_edges": 0
            }
        }

# Global integration engine instance
integration_engine = IntegrationEngine()

# Decorator for registering integrations
def register_integration(integration_class):
    """Decorator to register an integration"""
    integration_engine.registry.register(integration_class)
    return integration_class
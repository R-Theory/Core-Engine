"""
Core Plugin Interface - Base classes for all plugins in the Core Engine system

This module defines the foundational interfaces that all plugins must implement,
enabling a modular and extensible architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PluginType(str, Enum):
    """Types of plugins supported by the system"""
    STORAGE = "storage"
    PARSER = "parser"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"

class PluginStatus(str, Enum):
    """Plugin status states"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"

class PluginCapability(str, Enum):
    """Capabilities that plugins can provide"""
    READ = "read"
    WRITE = "write"
    PARSE = "parse"
    STORE = "store"
    ANALYZE = "analyze"
    SEARCH = "search"
    TRANSFORM = "transform"

class PluginMetadata(BaseModel):
    """Metadata about a plugin"""
    name: str
    version: str
    description: str
    author: Optional[str] = None
    plugin_type: PluginType
    capabilities: List[PluginCapability]
    dependencies: List[str] = []
    config_schema: Dict[str, Any] = {}

class PluginConfig(BaseModel):
    """Plugin configuration"""
    enabled: bool = False
    config: Dict[str, Any] = {}
    priority: int = 100  # Lower number = higher priority

class PluginResult(BaseModel):
    """Result from plugin operation"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class Plugin(ABC):
    """
    Abstract base class for all plugins
    
    All plugins must inherit from this class and implement the required methods.
    This ensures consistency across the plugin ecosystem.
    """
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.status = PluginStatus.INACTIVE
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialized = False

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin with its configuration
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def process(self, data: Any, **kwargs) -> PluginResult:
        """
        Main processing method - must be implemented by all plugins
        
        Args:
            data: Input data to process
            **kwargs: Additional arguments
            
        Returns:
            PluginResult: Result of the processing operation
        """
        pass

    async def cleanup(self) -> bool:
        """
        Cleanup resources when plugin is disabled or removed
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            self.status = PluginStatus.INACTIVE
            return True
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            return False

    async def health_check(self) -> bool:
        """
        Check if plugin is healthy and operational
        
        Returns:
            bool: True if healthy, False otherwise
        """
        return self.status == PluginStatus.ACTIVE

    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.config.enabled and self.status == PluginStatus.ACTIVE

class StoragePlugin(Plugin):
    """
    Base class for storage plugins
    
    Storage plugins handle where and how documents are stored.
    Examples: Notion, PostgreSQL, Google Drive, local files
    """
    
    @abstractmethod
    async def store(self, content: str, metadata: Dict[str, Any]) -> PluginResult:
        """
        Store content with metadata
        
        Args:
            content: The content to store
            metadata: Associated metadata
            
        Returns:
            PluginResult: Result with storage ID if successful
        """
        pass

    @abstractmethod
    async def retrieve(self, storage_id: str) -> PluginResult:
        """
        Retrieve content by storage ID
        
        Args:
            storage_id: Unique identifier for stored content
            
        Returns:
            PluginResult: Result with content if found
        """
        pass

    @abstractmethod
    async def delete(self, storage_id: str) -> PluginResult:
        """
        Delete content by storage ID
        
        Args:
            storage_id: Unique identifier for stored content
            
        Returns:
            PluginResult: Result of deletion operation
        """
        pass

    @abstractmethod
    async def search(self, query: str, filters: Dict[str, Any] = None) -> PluginResult:
        """
        Search stored content
        
        Args:
            query: Search query string
            filters: Optional filters to apply
            
        Returns:
            PluginResult: Result with matching content
        """
        pass

class ParserPlugin(Plugin):
    """
    Base class for parser plugins
    
    Parser plugins extract content and metadata from files.
    Examples: PDF parser, DOCX parser, code parser, markdown parser
    """
    
    @abstractmethod
    async def can_parse(self, file_path: str, mime_type: str = None) -> bool:
        """
        Check if this parser can handle the given file
        
        Args:
            file_path: Path to the file
            mime_type: Optional MIME type
            
        Returns:
            bool: True if parser can handle the file
        """
        pass

    @abstractmethod
    async def parse(self, file_path: str) -> PluginResult:
        """
        Parse file and extract content
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            PluginResult: Result with extracted content and metadata
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of file extensions this parser supports
        
        Returns:
            List[str]: List of supported file extensions (e.g., ['.pdf', '.txt'])
        """
        pass

    @abstractmethod
    def get_supported_mime_types(self) -> List[str]:
        """
        Get list of MIME types this parser supports
        
        Returns:
            List[str]: List of supported MIME types
        """
        pass

class ProcessorPlugin(Plugin):
    """
    Base class for processor plugins
    
    Processor plugins transform or enrich content after parsing.
    Examples: AI analysis, keyword extraction, sentiment analysis
    """
    
    @abstractmethod
    async def can_process(self, content_type: str, metadata: Dict[str, Any]) -> bool:
        """
        Check if this processor can handle the given content
        
        Args:
            content_type: Type of content
            metadata: Content metadata
            
        Returns:
            bool: True if processor can handle the content
        """
        pass

    @abstractmethod
    async def transform(self, content: str, metadata: Dict[str, Any]) -> PluginResult:
        """
        Transform or enrich the content
        
        Args:
            content: Content to process
            metadata: Associated metadata
            
        Returns:
            PluginResult: Result with transformed content
        """
        pass

class Document(BaseModel):
    """
    Document model for the plugin system
    """
    id: Optional[str] = None
    title: str
    content: str
    file_path: str
    mime_type: Optional[str] = None
    size: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    source: Optional[str] = None  # Which plugin parsed it
    storage_ids: Dict[str, str] = {}  # Storage plugin -> storage ID mapping

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PluginException(Exception):
    """Base exception for plugin-related errors"""
    
    def __init__(self, message: str, plugin_name: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.plugin_name = plugin_name
        self.details = details or {}
        super().__init__(self.message)

class PluginInitializationError(PluginException):
    """Raised when plugin initialization fails"""
    pass

class PluginProcessingError(PluginException):
    """Raised when plugin processing fails"""
    pass

class PluginConfigurationError(PluginException):
    """Raised when plugin configuration is invalid"""
    pass
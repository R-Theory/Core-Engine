# Core Engine MVP System Design Document

**Version:** 1.0  
**Date:** December 2024  
**Author:** Bob (System Architect)  
**Based on:** Product Requirements Document v1.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [System Architecture](#system-architecture)
4. [Component Specifications](#component-specifications)
5. [Data Structures and Interfaces](#data-structures-and-interfaces)
6. [Program Call Flow](#program-call-flow)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Integration Patterns](#integration-patterns)
10. [Performance Considerations](#performance-considerations)
11. [Scalability Strategy](#scalability-strategy)

---

## System Overview

The Core Engine is a modular, AI-powered learning and project management platform designed as a personal study/project operating system for university computer science students. The system follows a microservices architecture with clear separation of concerns, enabling scalability and maintainability.

### Key Architectural Goals

- **Modularity**: Plugin-based architecture for extensible functionality
- **Scalability**: Horizontal scaling capabilities for all components
- **Security**: Multi-layered security with OAuth 2.0 and sandboxed execution
- **Performance**: Sub-2s response times with intelligent caching
- **Reliability**: 99.5% uptime with graceful error handling

---

## Architecture Principles

### 1. Separation of Concerns
- **Frontend**: Pure presentation layer with state management
- **Backend API**: Business logic and data orchestration
- **Database**: Data persistence with optimized queries
- **Plugins**: Isolated external integrations
- **AI Agents**: Sandboxed AI processing

### 2. Event-Driven Architecture
- Asynchronous processing for long-running tasks
- Event sourcing for audit trails and state reconstruction
- Message queues for reliable inter-service communication

### 3. Security by Design
- Zero-trust security model
- Principle of least privilege
- Input validation and sanitization at all layers
- Encrypted data at rest and in transit

### 4. API-First Design
- RESTful APIs with OpenAPI specifications
- Versioned endpoints for backward compatibility
- Consistent error handling and response formats

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer (Nginx)                    │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
              ┌───────▼────────┐     ┌───────▼────────┐
              │   Frontend     │     │   Backend API  │
              │   (Next.js)    │     │   (FastAPI)    │
              │   Port: 3000   │     │   Port: 8000   │
              └────────────────┘     └───────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼────────┐     ┌───────▼────────┐     ┌───────▼────────┐
            │   Database     │     │     Redis      │     │  File Storage  │
            │ (PostgreSQL)   │     │   (Cache/Queue)│     │   (S3/Local)   │
            │   Port: 5432   │     │   Port: 6379   │     │                │
            └────────────────┘     └────────────────┘     └────────────────┘
                    │
            ┌───────▼────────┐
            │ Background     │
            │ Workers        │
            │ (Celery)       │
            └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Plugin Ecosystem                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Canvas Plugin  │  GitHub Plugin  │    Google Drive Plugin      │
│  (Docker)       │  (Docker)       │        (Docker)             │
└─────────────────┴─────────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent Layer                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  MetaGPT Agent  │  Claude Agent   │    Perplexity Agent         │
│  (Docker)       │  (Docker)       │        (Docker)             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Component Breakdown

#### Frontend Layer (Next.js 13+)
- **Technology**: Next.js 13+ with App Router, React 18, TypeScript
- **State Management**: Zustand for global state, TanStack Query for server state
- **Styling**: Tailwind CSS with custom design system
- **Authentication**: NextAuth.js with multiple OAuth providers

#### Backend API Layer (FastAPI)
- **Technology**: FastAPI with Python 3.11+, async/await patterns
- **Database ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: OAuth 2.0 + JWT with refresh token rotation
- **Background Tasks**: Celery with Redis broker

#### Data Layer
- **Primary Database**: PostgreSQL 15+ with connection pooling
- **Cache Layer**: Redis for session storage, API caching, and message queuing
- **File Storage**: S3-compatible storage with CDN integration
- **Search Engine**: PostgreSQL full-text search with GIN indexes

#### Plugin System
- **Runtime**: Docker containers with resource limits
- **Communication**: REST APIs with JSON payloads
- **Security**: Sandboxed execution with network isolation
- **Registry**: Dynamic plugin discovery and loading

#### AI Agent Framework
- **Orchestration**: Chain-of-responsibility pattern with context passing
- **Execution**: Async processing with timeout and retry mechanisms
- **Cost Management**: Usage tracking and budget controls
- **Provider Abstraction**: Unified interface for multiple AI providers

---

## Component Specifications

### 1. Backend API Architecture (FastAPI)

#### Directory Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configuration management
│   │   └── database.py         # Database configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── courses.py     # Course management
│   │       ├── resources.py   # Resource management
│   │       ├── workflows.py   # Workflow automation
│   │       ├── plugins.py     # Plugin management
│   │       └── agents.py      # AI agent endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py        # Security utilities
│   │   ├── plugin_loader.py   # Plugin system
│   │   ├── agent_registry.py  # AI agent management
│   │   ├── workflow_engine.py # Workflow execution
│   │   └── exceptions.py      # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py           # Base model classes
│   │   ├── user.py           # User models
│   │   ├── course.py         # Course models
│   │   ├── resource.py       # Resource models
│   │   ├── workflow.py       # Workflow models
│   │   └── plugin.py         # Plugin models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py           # User Pydantic schemas
│   │   ├── course.py         # Course schemas
│   │   ├── resource.py       # Resource schemas
│   │   └── workflow.py       # Workflow schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── course_service.py  # Course business logic
│   │   ├── resource_service.py # Resource management
│   │   ├── workflow_service.py # Workflow execution
│   │   └── plugin_service.py  # Plugin management
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base.py           # Base plugin interface
│   │   ├── canvas/           # Canvas integration
│   │   ├── github/           # GitHub integration
│   │   └── google_drive/     # Google Drive integration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Base agent interface
│   │   ├── metagpt/          # MetaGPT integration
│   │   ├── claude/           # Claude integration
│   │   └── perplexity/       # Perplexity integration
│   └── utils/
│       ├── __init__.py
│       ├── logging.py        # Logging configuration
│       ├── cache.py          # Caching utilities
│       └── validation.py     # Input validation
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

#### Core Application Configuration
```python
# app/main.py
from fastapi import FastAPI, Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config.settings import settings
from app.config.database import init_db
from app.api.v1 import auth, courses, resources, workflows, plugins, agents
from app.core.exceptions import setup_exception_handlers
from app.utils.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    setup_logging()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Core Engine API",
    description="AI-powered learning and project management platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Exception handlers
setup_exception_handlers(app)

# API Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["resources"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
```

### 2. Frontend Architecture (Next.js 13+)

#### Directory Structure
```
frontend/
├── src/
│   ├── app/                   # App Router (Next.js 13+)
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx          # Dashboard page
│   │   ├── loading.tsx       # Global loading UI
│   │   ├── error.tsx         # Global error UI
│   │   ├── not-found.tsx     # 404 page
│   │   ├── (auth)/           # Route groups
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── courses/
│   │   │   ├── page.tsx      # Course list
│   │   │   ├── [id]/         # Dynamic routes
│   │   │   │   ├── page.tsx  # Course details
│   │   │   │   └── assignments/
│   │   │   └── new/
│   │   ├── resources/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   ├── workflows/
│   │   │   ├── page.tsx
│   │   │   ├── builder/
│   │   │   └── [id]/
│   │   └── settings/
│   │       ├── page.tsx
│   │       ├── plugins/
│   │       └── agents/
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── table.tsx
│   │   │   └── index.ts
│   │   ├── forms/            # Form components
│   │   │   ├── course-form.tsx
│   │   │   ├── resource-form.tsx
│   │   │   └── workflow-form.tsx
│   │   ├── layout/           # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── navigation.tsx
│   │   │   └── footer.tsx
│   │   ├── features/         # Feature-specific components
│   │   │   ├── course-map/
│   │   │   ├── resource-vault/
│   │   │   ├── workflow-builder/
│   │   │   └── plugin-manager/
│   │   └── providers/        # Context providers
│   │       ├── auth-provider.tsx
│   │       ├── theme-provider.tsx
│   │       └── query-provider.tsx
│   ├── lib/
│   │   ├── api/              # API client
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── courses.ts
│   │   │   ├── resources.ts
│   │   │   ├── workflows.ts
│   │   │   └── plugins.ts
│   │   ├── auth/             # Authentication
│   │   │   ├── config.ts
│   │   │   └── providers.ts
│   │   ├── utils/            # Utility functions
│   │   │   ├── cn.ts         # Class name utility
│   │   │   ├── format.ts     # Formatting utilities
│   │   │   └── validation.ts # Client-side validation
│   │   └── constants/
│   │       ├── api.ts
│   │       └── routes.ts
│   ├── hooks/
│   │   ├── use-auth.ts       # Authentication hook
│   │   ├── use-api.ts        # API data fetching
│   │   ├── use-local-storage.ts
│   │   └── use-debounce.ts
│   ├── stores/               # Zustand stores
│   │   ├── auth-store.ts
│   │   ├── course-store.ts
│   │   ├── resource-store.ts
│   │   └── workflow-store.ts
│   ├── types/
│   │   ├── api.ts            # API response types
│   │   ├── auth.ts           # Authentication types
│   │   ├── course.ts         # Course-related types
│   │   ├── resource.ts       # Resource types
│   │   └── workflow.ts       # Workflow types
│   └── styles/
│       ├── globals.css       # Global styles
│       └── components.css    # Component styles
├── public/
│   ├── icons/
│   ├── images/
│   └── favicon.ico
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── Dockerfile
└── docker-compose.yml
```

#### Core Application Setup
```typescript
// src/app/layout.tsx
import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'
import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Core Engine - AI-Powered Learning Platform',
  description: 'Personal study and project management system for computer science students',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <Providers>
          <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-auto">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  )
}
```

### 3. Plugin System Architecture

#### Plugin Manifest Schema
```yaml
# Plugin Manifest Schema (plugin-manifest.yaml)
$schema: "https://core-engine.dev/schemas/plugin-manifest-v1.json"
apiVersion: "v1"
kind: "Plugin"

metadata:
  name: "canvas-integration"          # Required: Plugin identifier
  version: "1.2.0"                   # Required: Semantic version
  description: "Canvas LMS integration for assignments and courses"
  author: "Core Engine Team"
  homepage: "https://github.com/core-engine/plugins/canvas"
  license: "MIT"
  tags: ["education", "lms", "canvas"]

spec:
  # Plugin capabilities
  capabilities:
    - "read_courses"
    - "read_assignments" 
    - "read_grades"
    - "webhook_receiver"

  # Authentication configuration
  authentication:
    type: "oauth2"                   # oauth2, api_key, basic_auth
    authorization_url: "https://canvas.instructure.com/login/oauth2/auth"
    token_url: "https://canvas.instructure.com/login/oauth2/token"
    scopes: 
      - "url:GET|/api/v1/courses"
      - "url:GET|/api/v1/assignments"
    refresh_token_supported: true

  # Configuration fields for user input
  configuration:
    schema:
      type: "object"
      properties:
        canvas_domain:
          type: "string"
          title: "Canvas Domain"
          description: "Your Canvas domain (e.g., uncch.instructure.com)"
          pattern: "^[a-zA-Z0-9.-]+\\.(instructure\\.com|edu)$"
          required: true
        sync_frequency:
          type: "string"
          title: "Sync Frequency"
          description: "How often to sync data from Canvas"
          enum: ["realtime", "hourly", "daily", "weekly"]
          default: "daily"
        include_concluded:
          type: "boolean"
          title: "Include Concluded Courses"
          description: "Whether to include concluded/completed courses"
          default: false

  # API endpoints exposed by the plugin
  endpoints:
    - name: "get_courses"
      method: "GET"
      path: "/courses"
      description: "Fetch all enrolled courses"
      parameters:
        - name: "enrollment_state"
          in: "query"
          type: "string"
          enum: ["active", "invited", "concluded"]
      responses:
        200:
          description: "List of courses"
          schema:
            type: "array"
            items:
              $ref: "#/definitions/Course"
    
    - name: "get_assignments"
      method: "GET" 
      path: "/courses/{course_id}/assignments"
      description: "Fetch assignments for a specific course"
      parameters:
        - name: "course_id"
          in: "path"
          type: "string"
          required: true
      responses:
        200:
          description: "List of assignments"

  # Webhook configuration
  webhooks:
    - name: "assignment_created"
      description: "Triggered when new assignment is created"
      payload_schema:
        type: "object"
        properties:
          assignment_id: { type: "string" }
          course_id: { type: "string" }
          title: { type: "string" }
          due_date: { type: "string", format: "date-time" }

  # Resource requirements
  resources:
    limits:
      memory: "128Mi"
      cpu: "100m"
      storage: "1Gi"
    requests:
      memory: "64Mi"
      cpu: "50m"

  # Security policies
  security:
    network_policy: "restricted"     # none, restricted, full
    file_system_access: "read_only"  # none, read_only, read_write
    environment_variables: []        # List of allowed env vars

# Data type definitions
definitions:
  Course:
    type: "object"
    properties:
      id: { type: "string" }
      name: { type: "string" }
      course_code: { type: "string" }
      enrollment_term_id: { type: "string" }
      start_at: { type: "string", format: "date-time" }
      end_at: { type: "string", format: "date-time" }
```

#### Plugin Base Interface
```python
# app/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import asyncio
import aiohttp

class PluginCapability(str, Enum):
    READ_COURSES = "read_courses"
    READ_ASSIGNMENTS = "read_assignments"
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    SEND_NOTIFICATIONS = "send_notifications"
    WEBHOOK_RECEIVER = "webhook_receiver"

class PluginManifest(BaseModel):
    metadata: Dict[str, Any]
    spec: Dict[str, Any]
    
    @property
    def name(self) -> str:
        return self.metadata["name"]
    
    @property
    def version(self) -> str:
        return self.metadata["version"]
    
    @property
    def capabilities(self) -> List[PluginCapability]:
        return [PluginCapability(cap) for cap in self.spec.get("capabilities", [])]

class PluginExecutionContext(BaseModel):
    user_id: str
    plugin_id: str
    action: str
    parameters: Dict[str, Any]
    credentials: Dict[str, Any]
    timeout: int = 30

class PluginExecutionResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    cost: Optional[float] = None

class BasePlugin(ABC):
    def __init__(self, manifest: PluginManifest, config: Dict[str, Any]):
        self.manifest = manifest
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": f"CoreEngine-Plugin/{self.manifest.name}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plugin configuration"""
        pass
    
    @abstractmethod
    async def execute_action(self, context: PluginExecutionContext) -> PluginExecutionResult:
        """Execute a plugin action"""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """Get plugin health status"""
        pass
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook (optional)"""
        return {"status": "not_implemented"}
    
    def get_capabilities(self) -> List[PluginCapability]:
        """Get plugin capabilities"""
        return self.manifest.capabilities
    
    def supports_capability(self, capability: PluginCapability) -> bool:
        """Check if plugin supports a specific capability"""
        return capability in self.manifest.capabilities
```

#### Plugin Loader and Registry
```python
# app/core/plugin_loader.py
import os
import yaml
import docker
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
import aiofiles
import json

class PluginSandbox:
    def __init__(self, plugin_name: str, manifest: PluginManifest):
        self.plugin_name = plugin_name
        self.manifest = manifest
        self.docker_client = docker.from_env()
        self.container: Optional[docker.models.containers.Container] = None
    
    async def start_container(self) -> str:
        """Start plugin container and return container ID"""
        try:
            # Build container image if needed
            image_name = f"core-engine-plugin-{self.plugin_name}"
            
            # Container configuration based on manifest
            container_config = {
                "image": image_name,
                "name": f"plugin-{self.plugin_name}-{asyncio.current_task().get_name()}",
                "detach": True,
                "remove": True,
                "network_mode": "none" if self.manifest.spec.get("security", {}).get("network_policy") == "none" else "bridge",
                "mem_limit": self.manifest.spec.get("resources", {}).get("limits", {}).get("memory", "128m"),
                "cpu_period": 100000,
                "cpu_quota": int(self.manifest.spec.get("resources", {}).get("limits", {}).get("cpu", "100m").rstrip("m")) * 1000,
                "read_only": self.manifest.spec.get("security", {}).get("file_system_access") == "read_only",
                "tmpfs": {"/tmp": "size=100m,noexec"},
                "environment": {
                    "PLUGIN_NAME": self.plugin_name,
                    "PLUGIN_VERSION": self.manifest.version
                }
            }
            
            self.container = self.docker_client.containers.run(**container_config)
            return self.container.id
            
        except Exception as e:
            raise PluginExecutionError(f"Failed to start plugin container: {e}")
    
    async def execute_action(self, action: str, params: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action in sandboxed container"""
        if not self.container:
            await self.start_container()
        
        # Prepare execution payload
        payload = {
            "action": action,
            "parameters": params,
            "credentials": credentials,
            "manifest": self.manifest.dict()
        }
        
        # Write payload to container
        exec_result = self.container.exec_run([
            "python", "/app/execute.py", json.dumps(payload)
        ], workdir="/app")
        
        if exec_result.exit_code != 0:
            raise PluginExecutionError(f"Plugin execution failed: {exec_result.output.decode()}")
        
        try:
            return json.loads(exec_result.output.decode())
        except json.JSONDecodeError as e:
            raise PluginExecutionError(f"Invalid plugin response: {e}")
    
    async def cleanup(self):
        """Cleanup container resources"""
        if self.container:
            try:
                self.container.stop(timeout=5)
                self.container.remove()
            except Exception as e:
                print(f"Error cleaning up container: {e}")

class PluginRegistry:
    def __init__(self, plugin_directory: str = "/app/plugins"):
        self.plugin_directory = Path(plugin_directory)
        self.loaded_plugins: Dict[str, PluginManifest] = {}
        self.plugin_instances: Dict[str, BasePlugin] = {}
    
    async def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        plugins = []
        
        for plugin_dir in self.plugin_directory.iterdir():
            if plugin_dir.is_dir():
                manifest_path = plugin_dir / "plugin-manifest.yaml"
                if manifest_path.exists():
                    plugins.append(plugin_dir.name)
        
        return plugins
    
    async def load_plugin(self, plugin_name: str) -> PluginManifest:
        """Load plugin manifest"""
        manifest_path = self.plugin_directory / plugin_name / "plugin-manifest.yaml"
        
        if not manifest_path.exists():
            raise PluginNotFoundError(f"Plugin manifest not found: {plugin_name}")
        
        async with aiofiles.open(manifest_path, 'r') as f:
            content = await f.read()
        
        try:
            manifest_data = yaml.safe_load(content)
            manifest = PluginManifest(**manifest_data)
            
            # Validate manifest
            await self._validate_manifest(manifest)
            
            self.loaded_plugins[plugin_name] = manifest
            return manifest
            
        except yaml.YAMLError as e:
            raise PluginValidationError(f"Invalid YAML in manifest: {e}")
        except Exception as e:
            raise PluginValidationError(f"Invalid manifest structure: {e}")
    
    async def _validate_manifest(self, manifest: PluginManifest):
        """Validate plugin manifest"""
        required_fields = ["name", "version", "description"]
        
        for field in required_fields:
            if field not in manifest.metadata:
                raise PluginValidationError(f"Missing required field: {field}")
        
        # Validate capabilities
        valid_capabilities = [cap.value for cap in PluginCapability]
        for capability in manifest.capabilities:
            if capability not in valid_capabilities:
                raise PluginValidationError(f"Invalid capability: {capability}")
    
    async def get_plugin_instance(self, plugin_name: str, config: Dict[str, Any]) -> BasePlugin:
        """Get or create plugin instance"""
        if plugin_name not in self.loaded_plugins:
            await self.load_plugin(plugin_name)
        
        manifest = self.loaded_plugins[plugin_name]
        
        # Create plugin instance based on type
        if plugin_name == "canvas-integration":
            from app.plugins.canvas.plugin import CanvasPlugin
            return CanvasPlugin(manifest, config)
        elif plugin_name == "github-integration":
            from app.plugins.github.plugin import GitHubPlugin
            return GitHubPlugin(manifest, config)
        elif plugin_name == "google-drive-integration":
            from app.plugins.google_drive.plugin import GoogleDrivePlugin
            return GoogleDrivePlugin(manifest, config)
        else:
            # Generic sandboxed plugin
            return SandboxedPlugin(manifest, config)
    
    async def execute_plugin_action(
        self, 
        plugin_name: str, 
        action: str, 
        params: Dict[str, Any], 
        credentials: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PluginExecutionResult:
        """Execute plugin action with error handling and monitoring"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            plugin = await self.get_plugin_instance(plugin_name, config)
            
            context = PluginExecutionContext(
                user_id=params.get("user_id"),
                plugin_id=plugin_name,
                action=action,
                parameters=params,
                credentials=credentials
            )
            
            async with plugin:
                result = await plugin.execute_action(context)
                
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return PluginExecutionResult(
                success=True,
                data=result.data,
                execution_time=execution_time,
                cost=result.cost
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return PluginExecutionResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )

# Custom exceptions
class PluginError(Exception):
    pass

class PluginNotFoundError(PluginError):
    pass

class PluginValidationError(PluginError):
    pass

class PluginExecutionError(PluginError):
    pass
```

### 4. AI Agent Framework

#### Agent Base Interface
```python
# app/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
from enum import Enum
import asyncio
import time

class AgentType(str, Enum):
    CODE_GENERATION = "code_generation"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    PLANNING = "planning"
    REVIEW = "review"

class AgentCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    CODE_ANALYSIS = "code_analysis"
    WEB_SEARCH = "web_search"
    DOCUMENT_ANALYSIS = "document_analysis"
    IMAGE_ANALYSIS = "image_analysis"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"

class AgentConfig(BaseModel):
    name: str
    type: AgentType
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    cost_per_request: float = 0.0
    capabilities: List[AgentCapability] = []

class AgentContext(BaseModel):
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, Any]] = []
    workflow_context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class AgentRequest(BaseModel):
    prompt: str
    context: Optional[AgentContext] = None
    parameters: Dict[str, Any] = {}
    stream: bool = False

class AgentResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    cost: float
    metadata: Dict[str, Any] = {}

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session_id = None
        
    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process a single request"""
        pass
    
    @abstractmethod
    async def stream_process(self, request: AgentRequest) -> AsyncGenerator[str, None]:
        """Process request with streaming response"""
        pass
    
    @abstractmethod
    async def get_cost_estimate(self, prompt: str) -> float:
        """Estimate cost for processing prompt"""
        pass
    
    async def validate_request(self, request: AgentRequest) -> bool:
        """Validate incoming request"""
        if not request.prompt or len(request.prompt.strip()) == 0:
            raise ValueError("Prompt cannot be empty")
        
        if len(request.prompt) > 50000:  # Reasonable limit
            raise ValueError("Prompt too long")
        
        return True
    
    def supports_capability(self, capability: AgentCapability) -> bool:
        """Check if agent supports a specific capability"""
        return capability in self.config.capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        return {
            "status": "healthy",
            "agent": self.config.name,
            "provider": self.config.provider,
            "capabilities": [cap.value for cap in self.config.capabilities]
        }
```

#### Agent Orchestrator
```python
# app/core/agent_registry.py
from typing import Dict, List, Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

class AgentOrchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    async def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = agent
        self.agent_configs[agent_id] = agent.config
        
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents"""
        agents_info = []
        
        for agent_id, agent in self.agents.items():
            health = await agent.health_check()
            agents_info.append({
                "id": agent_id,
                "config": self.agent_configs[agent_id].dict(),
                "health": health
            })
        
        return agents_info
    
    async def execute_single_agent(
        self, 
        agent_id: str, 
        request: AgentRequest
    ) -> AgentResponse:
        """Execute single agent request"""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent not found: {agent_id}")
        
        start_time = time.time()
        
        try:
            await agent.validate_request(request)
            response = await agent.process(request)
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentResponse(
                success=False,
                error=str(e),
                execution_time=execution_time,
                cost=0.0
            )
    
    async def execute_agent_chain(
        self, 
        chain_config: List[Dict[str, Any]], 
        initial_context: AgentContext
    ) -> List[AgentResponse]:
        """Execute chain of agents with context passing"""
        results = []
        context = initial_context
        
        for step in chain_config:
            agent_id = step["agent_id"]
            prompt_template = step["prompt"]
            parameters = step.get("parameters", {})
            
            # Interpolate context into prompt
            prompt = self._interpolate_prompt(prompt_template, context, results)
            
            request = AgentRequest(
                prompt=prompt,
                context=context,
                parameters=parameters
            )
            
            response = await self.execute_single_agent(agent_id, request)
            results.append(response)
            
            # Update context with response
            if response.success and response.data:
                context.workflow_context.update(response.data)
            
            # Stop chain if any step fails
            if not response.success:
                break
        
        return results
    
    async def execute_parallel_agents(
        self, 
        agent_requests: List[Dict[str, Any]]
    ) -> List[AgentResponse]:
        """Execute multiple agents in parallel"""
        tasks = []
        
        for req in agent_requests:
            agent_id = req["agent_id"]
            request = AgentRequest(**req["request"])
            
            task = asyncio.create_task(
                self.execute_single_agent(agent_id, request)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AgentResponse(
                    success=False,
                    error=str(result),
                    execution_time=0.0,
                    cost=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _interpolate_prompt(
        self, 
        template: str, 
        context: AgentContext, 
        previous_results: List[AgentResponse]
    ) -> str:
        """Interpolate context and previous results into prompt template"""
        variables = {
            "context": context.workflow_context,
            "metadata": context.metadata,
            "user_id": context.user_id,
            "session_id": context.session_id
        }
        
        # Add previous step results
        for i, result in enumerate(previous_results):
            variables[f"step_{i}"] = {
                "content": result.content,
                "data": result.data,
                "success": result.success
            }
        
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Template variable not found: {e}")
    
    async def get_agent_recommendations(
        self, 
        task_description: str, 
        required_capabilities: List[AgentCapability]
    ) -> List[str]:
        """Recommend agents based on task requirements"""
        suitable_agents = []
        
        for agent_id, config in self.agent_configs.items():
            # Check if agent has required capabilities
            if all(cap in config.capabilities for cap in required_capabilities):
                suitable_agents.append(agent_id)
        
        # Sort by cost (lower cost first)
        suitable_agents.sort(key=lambda aid: self.agent_configs[aid].cost_per_request)
        
        return suitable_agents

class AgentNotFoundError(Exception):
    pass
```

### 5. Workflow Engine

#### Workflow Definition Schema
```python
# app/models/workflow.py
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid

class Workflow(BaseModel):
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")

class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    results = Column(JSON)
    error_message = Column(Text)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
```

#### Workflow Engine Implementation
```python
# app/core/workflow_engine.py
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
import json
import time
from datetime import datetime

class WorkflowStepType(str, Enum):
    PLUGIN_ACTION = "plugin_action"
    AI_AGENT = "ai_agent"
    SYSTEM_ACTION = "system_action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStep(BaseModel):
    name: str
    type: WorkflowStepType
    config: Dict[str, Any]
    depends_on: List[str] = []
    condition: Optional[str] = None
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3

class WorkflowDefinition(BaseModel):
    name: str
    description: str
    version: str = "1.0"
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = {}
    timeout: int = 3600

class WorkflowExecutionContext(BaseModel):
    execution_id: str
    workflow_id: str
    user_id: str
    variables: Dict[str, Any] = {}
    step_results: Dict[str, Any] = {}
    current_step: Optional[str] = None
    start_time: datetime
    status: WorkflowStatus = WorkflowStatus.PENDING

class WorkflowEngine:
    def __init__(self, plugin_registry, agent_orchestrator):
        self.plugin_registry = plugin_registry
        self.agent_orchestrator = agent_orchestrator
        self.running_executions: Dict[str, WorkflowExecutionContext] = {}
        
    async def execute_workflow(
        self, 
        workflow_definition: WorkflowDefinition,
        user_id: str,
        input_variables: Dict[str, Any] = None
    ) -> str:
        """Start workflow execution and return execution ID"""
        execution_id = str(uuid.uuid4())
        
        context = WorkflowExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_definition.name,
            user_id=user_id,
            variables={**workflow_definition.variables, **(input_variables or {})},
            start_time=datetime.utcnow()
        )
        
        self.running_executions[execution_id] = context
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow_async(workflow_definition, context))
        
        return execution_id
    
    async def _execute_workflow_async(
        self, 
        workflow_definition: WorkflowDefinition, 
        context: WorkflowExecutionContext
    ):
        """Execute workflow asynchronously"""
        try:
            context.status = WorkflowStatus.RUNNING
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow_definition.steps)
            
            # Execute steps in topological order
            executed_steps = set()
            
            while len(executed_steps) < len(workflow_definition.steps):
                # Find steps ready to execute
                ready_steps = []
                for step in workflow_definition.steps:
                    if (step.name not in executed_steps and 
                        all(dep in executed_steps for dep in step.depends_on)):
                        ready_steps.append(step)
                
                if not ready_steps:
                    raise WorkflowExecutionError("Circular dependency detected or no steps ready")
                
                # Execute ready steps (can be parallel if no dependencies between them)
                await self._execute_steps_batch(ready_steps, context)
                
                # Mark steps as executed
                for step in ready_steps:
                    executed_steps.add(step.name)
            
            context.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            context.status = WorkflowStatus.FAILED
            context.step_results["error"] = str(e)
            
        finally:
            # Save execution results to database
            await self._save_execution_results(context)
            
            # Clean up from running executions
            if context.execution_id in self.running_executions:
                del self.running_executions[context.execution_id]
    
    async def _execute_steps_batch(
        self, 
        steps: List[WorkflowStep], 
        context: WorkflowExecutionContext
    ):
        """Execute a batch of steps (potentially in parallel)"""
        # Group steps by whether they can run in parallel
        parallel_steps = []
        sequential_steps = []
        
        for step in steps:
            if step.type == WorkflowStepType.PARALLEL:
                parallel_steps.append(step)
            else:
                sequential_steps.append(step)
        
        # Execute parallel steps
        if parallel_steps:
            tasks = [
                self._execute_single_step(step, context) 
                for step in parallel_steps
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Execute sequential steps
        for step in sequential_steps:
            await self._execute_single_step(step, context)
    
    async def _execute_single_step(
        self, 
        step: WorkflowStep, 
        context: WorkflowExecutionContext
    ):
        """Execute a single workflow step"""
        context.current_step = step.name
        start_time = time.time()
        
        try:
            # Check condition if specified
            if step.condition and not self._evaluate_condition(step.condition, context):
                context.step_results[step.name] = {
                    "status": "skipped",
                    "reason": "condition_not_met"
                }
                return
            
            # Execute step based on type
            if step.type == WorkflowStepType.PLUGIN_ACTION:
                result = await self._execute_plugin_step(step, context)
            elif step.type == WorkflowStepType.AI_AGENT:
                result = await self._execute_agent_step(step, context)
            elif step.type == WorkflowStepType.SYSTEM_ACTION:
                result = await self._execute_system_step(step, context)
            elif step.type == WorkflowStepType.CONDITION:
                result = await self._execute_condition_step(step, context)
            elif step.type == WorkflowStepType.LOOP:
                result = await self._execute_loop_step(step, context)
            else:
                raise WorkflowExecutionError(f"Unknown step type: {step.type}")
            
            execution_time = time.time() - start_time
            
            context.step_results[step.name] = {
                "status": "completed",
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Retry logic
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                await self._execute_single_step(step, context)
            else:
                context.step_results[step.name] = {
                    "status": "failed",
                    "error": str(e),
                    "execution_time": execution_time
                }
                raise WorkflowExecutionError(f"Step {step.name} failed: {e}")
    
    async def _execute_plugin_step(
        self, 
        step: WorkflowStep, 
        context: WorkflowExecutionContext
    ) -> Dict[str, Any]:
        """Execute plugin action step"""
        plugin_name = step.config["plugin"]
        action = step.config["action"]
        params = self._interpolate_variables(step.config.get("params", {}), context)
        
        # Get user credentials for plugin
        credentials = await self._get_plugin_credentials(context.user_id, plugin_name)
        
        result = await self.plugin_registry.execute_plugin_action(
            plugin_name=plugin_name,
            action=action,
            params=params,
            credentials=credentials,
            config={}  # TODO: Get user plugin config
        )
        
        if not result.success:
            raise WorkflowExecutionError(f"Plugin action failed: {result.error}")
        
        return result.data
    
    async def _execute_agent_step(
        self, 
        step: WorkflowStep, 
        context: WorkflowExecutionContext
    ) -> Dict[str, Any]:
        """Execute AI agent step"""
        agent_id = step.config["agent"]
        prompt_template = step.config["prompt"]
        parameters = step.config.get("parameters", {})
        
        # Interpolate variables into prompt
        prompt = self._interpolate_variables(prompt_template, context)
        
        agent_context = AgentContext(
            user_id=context.user_id,
            session_id=context.execution_id,
            workflow_context=context.variables,
            metadata={"step_name": step.name}
        )
        
        request = AgentRequest(
            prompt=prompt,
            context=agent_context,
            parameters=parameters
        )
        
        response = await self.agent_orchestrator.execute_single_agent(agent_id, request)
        
        if not response.success:
            raise WorkflowExecutionError(f"Agent execution failed: {response.error}")
        
        return {
            "content": response.content,
            "data": response.data,
            "cost": response.cost
        }
    
    async def _execute_system_step(
        self, 
        step: WorkflowStep, 
        context: WorkflowExecutionContext
    ) -> Dict[str, Any]:
        """Execute system action step"""
        action = step.config["action"]
        params = self._interpolate_variables(step.config.get("params", {}), context)
        
        if action == "create_notification":
            # Create user notification
            await self._create_notification(
                user_id=context.user_id,
                title=params.get("title"),
                content=params.get("content"),
                priority=params.get("priority", "medium")
            )
            return {"status": "notification_created"}
        
        elif action == "update_variable":
            # Update workflow variable
            variable_name = params["name"]
            variable_value = params["value"]
            context.variables[variable_name] = variable_value
            return {"variable": variable_name, "value": variable_value}
        
        elif action == "send_email":
            # Send email notification
            await self._send_email(
                to=params["to"],
                subject=params["subject"],
                body=params["body"]
            )
            return {"status": "email_sent"}
        
        else:
            raise WorkflowExecutionError(f"Unknown system action: {action}")
    
    def _interpolate_variables(
        self, 
        template: Any, 
        context: WorkflowExecutionContext
    ) -> Any:
        """Interpolate workflow variables into template"""
        if isinstance(template, str):
            # Simple string interpolation
            variables = {
                **context.variables,
                **{f"steps.{k}": v for k, v in context.step_results.items()},
                "execution_id": context.execution_id,
                "user_id": context.user_id
            }
            
            try:
                return template.format(**variables)
            except KeyError as e:
                raise WorkflowExecutionError(f"Template variable not found: {e}")
        
        elif isinstance(template, dict):
            return {k: self._interpolate_variables(v, context) for k, v in template.items()}
        
        elif isinstance(template, list):
            return [self._interpolate_variables(item, context) for item in template]
        
        else:
            return template
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for workflow steps"""
        graph = {}
        for step in steps:
            graph[step.name] = step.depends_on
        return graph
    
    def _evaluate_condition(self, condition: str, context: WorkflowExecutionContext) -> bool:
        """Evaluate workflow condition"""
        # Simple condition evaluation (can be extended with more complex logic)
        variables = {
            **context.variables,
            **{f"steps.{k}": v for k, v in context.step_results.items()}
        }
        
        try:
            # Use eval with restricted globals for safety
            safe_globals = {"__builtins__": {}}
            return eval(condition, safe_globals, variables)
        except Exception:
            return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        if execution_id in self.running_executions:
            context = self.running_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": context.status.value,
                "current_step": context.current_step,
                "step_results": context.step_results,
                "start_time": context.start_time.isoformat()
            }
        
        # Check database for completed executions
        # TODO: Implement database lookup
        return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running workflow execution"""
        if execution_id in self.running_executions:
            context = self.running_executions[execution_id]
            context.status = WorkflowStatus.CANCELLED
            return True
        return False

class WorkflowExecutionError(Exception):
    pass
```

---

## Data Structures and Interfaces

I'll create separate files for the class diagram and sequence diagram as requested.
